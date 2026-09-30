"""Read-only SNMPv1 GET and v1/v2c trap monitoring, independent of voice/SDR.

No SET, reboot, registration or transmitter operations. Community strings are
never included in parsed messages or logs. See docs/HYTERA_ETHERNET.md for MIB sources.
"""

from __future__ import annotations

import ipaddress
import json
import queue
import secrets
import select
import socket
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

UPTIME = "1.3.6.1.2.1.1.3.0"
ALARM_BASE = "1.3.6.1.4.1.40297.1.2.1.1."
ALARMS = {
    1: ("Besleme gerilimi", {0: "Normal", 1: "Düşük", 2: "Yüksek", 3: "Anormal"}),
    2: ("Sıcaklık", {0: "Normal", 1: "Düşük", 2: "Yüksek"}),
    3: ("Fan", {0: "Normal", 1: "Alarm"}),
    4: ("İleri güç", {0: "Normal", 1: "Alarm"}),
    5: ("Yansıyan güç", {0: "Normal", 1: "Alarm"}),
    6: ("VSWR / anten", {0: "Normal", 1: "Alarm"}),
    7: ("Verici PLL", {0: "Normal", 1: "Kilit hatası"}),
    8: ("Alıcı PLL", {0: "Normal", 1: "Kilit hatası"}),
    9: ("Batarya gerilimi", {0: "Normal", 1: "Anormal"}),
}
# One object per GET: an unsupported optional OID must not hide other alarms.
POLL_OIDS = [UPTIME] + [f"{ALARM_BASE}{n}.0" for n in ALARMS]


def _tlv(data: bytes, at: int = 0) -> tuple[int, bytes, int]:
    if at + 2 > len(data):
        raise ValueError("Eksik BER başlığı")
    tag, length = data[at : at + 2]
    at += 2
    if length & 128:
        size = length & 127
        if not 1 <= size <= 4 or at + size > len(data):
            raise ValueError("Geçersiz BER uzunluğu")
        length = int.from_bytes(data[at : at + size], "big")
        at += size
    if at + length > len(data):
        raise ValueError("Eksik BER değeri")
    return tag, data[at : at + length], at + length


def _fields(data: bytes) -> list[tuple[int, bytes]]:
    result, at = [], 0
    while at < len(data):
        tag, value, at = _tlv(data, at)
        result.append((tag, value))
        if len(result) > 128:
            raise ValueError("Çok fazla SNMP alanı")
    return result


def _integer(field: tuple[int, bytes], tag: int = 2) -> int:
    kind, value = field
    if kind != tag or not 1 <= len(value) <= 9:
        raise ValueError("Geçersiz SNMP sayısı")
    return int.from_bytes(value, "big", signed=tag == 2)


def _oid(data: bytes) -> str:
    values, number = [], 0
    for part in data:
        number = (number << 7) | (part & 127)
        if number > 0xFFFFFFFFFFFFFFFF:
            raise ValueError("OID çok büyük")
        if not part & 128:
            values.append(number)
            number = 0
    if not values or not data or data[-1] & 128:
        raise ValueError("Eksik OID")
    first = values.pop(0)
    arc = min(2, first // 40)
    return ".".join(map(str, [arc, first - arc * 40, *values]))


def _value(tag: int, data: bytes) -> int | str | None:
    if tag in (2, 0x41, 0x42, 0x43, 0x46):
        return _integer((tag, data), tag)
    if tag == 6:
        return _oid(data)
    if tag == 0x40 and len(data) == 4:
        return str(ipaddress.IPv4Address(data))
    if tag in (5, 0x80, 0x81, 0x82):
        return None
    # Do not assume byte order, units, text or alarm meanings for opaque vendor values.
    return "hex:" + data[:256].hex()


@dataclass(frozen=True)
class SnmpMessage:
    kind: str
    request_id: int | None
    error: int
    description: str
    values: tuple[tuple[str, int, int | str | None], ...]


def parse_snmp(data: bytes) -> SnmpMessage:
    if len(data) > 32768:
        raise ValueError("SNMP paketi çok büyük")
    tag, body, end = _tlv(data)
    if tag != 48 or end != len(data):
        raise ValueError("Geçersiz SNMP zarfı")
    outer = _fields(body)
    if len(outer) != 3 or outer[1][0] != 4:
        raise ValueError("SNMP v1/v2c zarfı gerekli")
    version = _integer(outer[0])
    if version not in (0, 1):
        raise ValueError("SNMP sürümü desteklenmiyor")
    pdu_tag, payload = outer[2]
    fields = _fields(payload)
    request_id, error = None, 0
    if pdu_tag == 0xA4 and version == 0:
        if len(fields) != 6 or fields[0][0] != 6 or fields[1][0] != 0x40 or len(fields[1][1]) != 4:
            raise ValueError("Geçersiz SNMPv1 Trap")
        generic, specific = _integer(fields[2]), _integer(fields[3])
        _integer(fields[4], 0x43)
        description = f"Trap {_oid(fields[0][1])} • Genel {generic} • Özel {specific}"
        kind = "trap"
    elif pdu_tag in (0xA2, 0xA7) and (pdu_tag != 0xA7 or version == 1):
        if len(fields) != 4:
            raise ValueError("Geçersiz SNMP yanıtı")
        request_id, error = _integer(fields[0]), _integer(fields[1])
        _integer(fields[2])
        kind = "response" if pdu_tag == 0xA2 else "trap"
        description = "SNMP yanıtı" if kind == "response" else "SNMPv2c Trap"
    else:
        raise ValueError("Desteklenmeyen SNMP PDU")
    if fields[-1][0] != 48:
        raise ValueError("Eksik VarBind listesi")
    values = []
    for tag, value in _fields(fields[-1][1]):
        if tag != 48:
            raise ValueError("Geçersiz VarBind")
        pair = _fields(value)
        if len(pair) != 2 or pair[0][0] != 6:
            raise ValueError("Geçersiz VarBind alanı")
        values.append((_oid(pair[0][1]), pair[1][0], _value(*pair[1])))
    return SnmpMessage(kind, request_id, error, description, tuple(values))


def _encode(tag: int, data: bytes) -> bytes:
    length = len(data)
    size = bytes([length]) if length < 128 else b"\x82" + length.to_bytes(2, "big")
    return bytes([tag]) + size + data


def get_request(request_id: int, oid: str, community: bytes = b"public") -> bytes:
    # Fixed GET-only encoder; no operation selector can turn this into SET.
    arcs = [int(x) for x in oid.split(".")]
    encoded = bytearray()
    for arc in [40 * arcs[0] + arcs[1], *arcs[2:]]:
        parts = [arc & 127]
        while arc > 127:
            arc >>= 7
            parts.insert(0, (arc & 127) | 128)
        encoded.extend(parts)
    varbinds = _encode(48, _encode(48, _encode(6, bytes(encoded)) + b"\x05\x00"))
    pdu = _encode(
        0xA0,
        _encode(2, request_id.to_bytes(4, "big", signed=True)) + b"\x02\x01\x00" * 2 + varbinds,
    )
    return _encode(48, b"\x02\x01\x00" + _encode(4, community) + pdu)


class SnmpMonitor:
    def __init__(self, root: Path):
        self.root = root
        self.thread: threading.Thread | None = None
        self.cancel = threading.Event()
        self.messages: queue.Queue = queue.Queue(maxsize=256)
        self.last_seen: float | None = None
        self.started: float | None = None
        self.alarms: dict[str, tuple[int | None, float, str]] = {}
        self.history: deque[dict] = deque(maxlen=100)
        self.lock = threading.Lock()
        self.error = ""
        self.unsupported: set[str] = set()

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, local: str, remote: str):
        if self.running:
            return
        for ip in (local, remote):
            address = ipaddress.IPv4Address(ip)
            if address.is_unspecified or address.is_multicast or int(address) == 0xFFFFFFFF:
                raise ValueError("SNMP için PC ve rölenin tekil IPv4 adresi gerekli.")
        self.last_seen = None
        self.started = time.monotonic()
        self.alarms.clear()
        self.unsupported.clear()
        self.error = ""
        self.cancel.clear()
        self.thread = threading.Thread(target=self._run, args=(local, remote), daemon=True)
        self.thread.start()

    def stop(self):
        self.cancel.set()

    def snapshot(self):
        with self.lock:
            now = time.monotonic()
            fresh = self.running and self.last_seen is not None and now - self.last_seen <= 35
            active = [
                label for value, _, label in self.alarms.values() if value is not None and value > 0
            ]
            normal = sum(value == 0 and now - at <= 35 for value, at, _ in self.alarms.values())
            unknown = sum(value is None for value, _, _ in self.alarms.values())
            return {
                "running": self.running,
                "attempted": self.started is not None,
                "fresh": fresh,
                "age": None if self.last_seen is None else max(0, now - self.last_seen),
                "active": active,
                "active_stale": any(
                    value is not None and value > 0 and now - at > 35
                    for value, at, _ in self.alarms.values()
                ),
                "fields": dict(self.alarms),
                "normal": normal,
                "unknown": unknown,
                "waiting": self.running and self.started is not None and now - self.started < 35,
                "error": self.error,
                "history": list(self.history),
            }

    def event(self, text: str, *, category: str = "SNMP", values=None):
        item = {
            "observed_utc": datetime.now(timezone.utc).isoformat(),
            "channel": "Hytera durum",
            "protocol": "SNMP",
            "category": category,
            "raw": text,
        }
        if values is not None:
            item["values"] = values
        with self.lock:
            self.history.append(item)
        directory = self.root / "hytera-status"
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / (datetime.now().strftime("%Y-%m-%d") + ".jsonl")).open(
            "a", encoding="utf-8"
        ) as log:
            log.write(json.dumps(item, ensure_ascii=False) + "\n")
        try:
            self.messages.put_nowait(item)
        except queue.Full:
            pass

    def observe(self, message: SnmpMessage, *, now: float | None = None):
        now = time.monotonic() if now is None else now
        changed = []
        with self.lock:
            self.last_seen = now
            if not message.error:
                for oid, tag, value in message.values:
                    if not oid.startswith(ALARM_BASE):
                        continue
                    suffix = oid[len(ALARM_BASE) :].split(".")
                    if len(suffix) != 2 or suffix[1] != "0" or not suffix[0].isdigit():
                        continue
                    info = ALARMS.get(int(suffix[0]))
                    if info is None:
                        continue
                    title, meanings = info
                    valid = (
                        value if tag == 2 and isinstance(value, int) and value in meanings else None
                    )
                    label = f"{title}: {meanings[valid] if valid is not None else 'bilinmeyen / desteklenmiyor'}"
                    previous = self.alarms.get(oid)
                    # An unknown value cannot acknowledge/clear a previously reported alarm.
                    if valid is None and previous is not None and previous[0] not in (None, 0):
                        changed.append(label)
                        continue
                    self.alarms[oid] = valid, now, label
                    if previous is None or previous[0] != valid:
                        changed.append(label)
        if message.kind == "trap" or changed:
            self.event(
                " • ".join(changed) or message.description,
                category="SNMP bildirimi",
                values=message.values,
            )

    def _run(self, local: str, remote: str):
        sockets = []
        waiting: dict[int, tuple[str, float]] = {}
        next_query, next_log = 0.0, 0.0
        last_link = None
        sequence = secrets.randbelow(0x3FFFFFFF)
        try:
            request_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sockets.append(request_socket)
            request_socket.bind((local, 0))
            trap_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    trap_socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                trap_socket.bind((local, 162))
                sockets.append(trap_socket)
            except OSError as exc:
                trap_socket.close()
                self.event(
                    f"Trap UDP 162 açılamadı; salt okunur sorgular devam ediyor: {exc}",
                    category="SNMP uyarı",
                )
            self.event("SNMP durum izleme başladı • GET UDP 161 / Trap UDP 162")
            while not self.cancel.is_set():
                now = time.monotonic()
                if now >= next_query:
                    waiting = {key: item for key, item in waiting.items() if now - item[1] < 3}
                    for oid in POLL_OIDS:
                        if oid in self.unsupported and oid != UPTIME:
                            continue
                        sequence = (sequence + 1) & 0x7FFFFFFF
                        request_socket.sendto(get_request(sequence, oid), (remote, 161))
                        waiting[sequence] = oid, now
                    next_query = now + 10
                ready, _, _ = select.select(sockets, [], [], 0.2)
                for sock in ready:
                    try:
                        data, sender = sock.recvfrom(32769)
                    except ConnectionResetError:
                        continue
                    if sender[0] != remote:
                        continue
                    try:
                        message = parse_snmp(data)
                    except ValueError:
                        continue
                    if sock is request_socket:
                        pending = (
                            waiting.pop(message.request_id, None)
                            if message.request_id is not None
                            else None
                        )
                        if (
                            message.kind != "response"
                            or sender[1] != 161
                            or pending is None
                            or now - pending[1] > 3
                        ):
                            continue
                        if message.error:
                            if pending[0] not in self.unsupported:
                                self.event(
                                    f"OID {pending[0]} • SNMP hata {message.error}; arıza sonucu bilinmiyor"
                                )
                            self.unsupported.add(pending[0])
                        elif not message.values or any(
                            oid != pending[0] for oid, _, _ in message.values
                        ):
                            continue
                    elif message.kind != "trap":
                        continue
                    self.observe(message)
                state = self.snapshot()
                linked = state["fresh"]
                if linked != last_link and (linked or not state["waiting"]):
                    self.event(
                        "Röleden SNMP yanıtı alınıyor"
                        if linked
                        else "Röleden güncel SNMP yanıtı yok",
                        category="bağlantı",
                    )
                    last_link = linked
                if now >= next_log:
                    self.event(
                        f"Durum: {'yanıt var' if linked else 'yanıt bekleniyor'} • Normal alan {state['normal']} • Alarm {len(state['active'])}",
                        category="durum özeti",
                    )
                    next_log = now + 60
        except Exception as exc:
            self.error = f"SNMP izleme durdu: {exc}"
            try:
                self.event(self.error, category="SNMP hata")
            except OSError:
                pass
        finally:
            for sock in sockets:
                sock.close()


def repeater_badge(
    *, voice_running: bool, linked: int, snmp: dict, configured: bool
) -> tuple[str, str]:
    """Presence, voice transport and alarm are distinct observations."""
    if snmp["active"]:
        return (
            "Alarm" if snmp["fresh"] and not snmp["active_stale"] else "Son alarm • veri eski"
        ), "red"
    if linked == 4 and voice_running:
        if snmp["attempted"] and not snmp["fresh"]:
            return "Ses bağlı • SNMP yok", "orange"
        return "Bağlı", "green"
    if voice_running and linked:
        return "Kısmi bağlantı", "orange"
    if snmp["fresh"]:
        return ("Röle var • ses yok" if voice_running else "Röle var"), (
            "orange" if voice_running else "green"
        )
    if snmp["waiting"]:
        return "Kontrol ediliyor", "gray"
    if snmp["error"]:
        return "İzleme hatası", "orange"
    if not voice_running and snmp["attempted"] and not snmp["running"]:
        return "İzleme kapalı", "gray"
    if voice_running or snmp["running"] or snmp["age"] is not None:
        return "Yanıt yok", "red"
    return ("Durum bilinmiyor" if configured else "Ayarlanmamış"), "gray"
