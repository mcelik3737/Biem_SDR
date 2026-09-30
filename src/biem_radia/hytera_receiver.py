"""Independent, receive-only Hytera IP Dispatch transport and two-slot archive."""

from __future__ import annotations

import ipaddress
import json
import queue
import select
import socket
import threading
import time
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .filenames import available_path, recording_name
from .hytera_protocol import (
    CallStatus,
    VoicePacket,
    call_status,
    pcmu_decode,
    transport,
    voice_packet,
)
from .live_audio import LiveAudio
from .storage import Archive


class SlotRecorder:
    """RCP-gated PCMU with bounded reordering and independent call state per slot."""

    def __init__(self, archive: Archive, slot: int, monitor: LiveAudio, notify):
        self.archive, self.slot, self.monitor, self.notify = archive, slot, monitor, notify
        self.channel = f"Hytera • Slot {slot}"
        self.call: CallStatus | None = None
        self.call_at = self.last_audio = 0.0
        self.closing_at: float | None = None
        self.pending: dict[int, tuple[VoicePacket, float]] = {}
        self.next_seq: int | None = None
        self.next_stamp: int | None = None
        self.ssrc: int | None = None
        self.writer: wave.Wave_write | None = None
        self.path: Path | None = None
        self.samples = self.received = self.lost = self.discarded = 0
        self.segment_lost = 0
        self.started = datetime.now(timezone.utc)
        self.cooldown = 0.0

    def control(self, call: CallStatus, now: float):
        if call.voice:
            if self.call != call or self.closing_at is not None:
                self.finish("call_changed")
                self.reset_stream()
            self.call, self.call_at, self.closing_at = call, now, None
        elif self.call is not None and call.service == 1 and call.state in (1, 3, 4, 7):
            # Allow the final RTP packets to arrive after the control datagram.
            self.closing_at = min(self.closing_at or now + 0.3, now + 0.3)
        else:
            self.finish("call_end")
            self.call = None
            self.reset_stream()

    def reset_stream(self):
        self.pending.clear()
        self.next_seq = self.next_stamp = self.ssrc = None
        self.last_audio = 0.0
        self.closing_at = None

    def accept(self, packet: VoicePacket, now: float):
        self.tick(now)
        if self.call is None:
            self.discarded += 1
            return
        if self.ssrc is not None and packet.ssrc != self.ssrc:
            self.discarded += 1  # A new stream needs a new call-control announcement.
            return
        if self.next_seq is None:
            self.next_seq, self.ssrc = packet.sequence, packet.ssrc
        distance = (packet.sequence - self.next_seq) & 65535
        if distance >= 32768 or packet.sequence in self.pending:
            self.discarded += 1
            return
        if distance > 1000:
            self.finish("sequence_discontinuity")
            self.call = None
            self.reset_stream()
            return
        self.pending[packet.sequence] = packet, now
        self.last_audio = now
        self.received += 1
        self.flush(now)

    def flush(self, now: float, force: bool = False):
        while self.pending and self.next_seq is not None:
            if self.next_seq not in self.pending:
                oldest = min(at for _, at in self.pending.values())
                if not force and now - oldest < 0.15 and len(self.pending) < 32:
                    return
                expected = self.next_seq
                nearest = min(self.pending, key=lambda seq: (seq - expected) & 65535)
                missing = (nearest - self.next_seq) & 65535
                self.lost += missing
                self.segment_lost += missing
                self.next_seq = nearest
            packet, at = self.pending.pop(self.next_seq)
            self.next_seq = (self.next_seq + 1) & 65535
            gap = (
                0 if self.next_stamp is None else (packet.timestamp - self.next_stamp) & 0xFFFFFFFF
            )
            if gap > 8000:
                self._finish_file("timestamp_discontinuity")
                self.call = None
                self.reset_stream()
                return
            self.next_stamp = (packet.timestamp + len(packet.audio)) & 0xFFFFFFFF
            pcm = pcmu_decode(packet.audio)
            self.monitor.feed(
                self.channel, str(self.slot), pcm / 32768.0, 8000, f"Slot {self.slot}"
            )
            # Packet losses are silence, never repeated speech. Preserve RTP timing.
            if gap:
                pcm = np.concatenate((np.zeros(gap, dtype="<i2"), pcm))
            self.write(pcm, at)

    def write(self, pcm: np.ndarray, now: float):
        if now < self.cooldown or self.call is None:
            return
        if self.writer is None:
            self.started = datetime.fromtimestamp(now, timezone.utc)
            directory = (
                self.archive.root / "recordings" / self.started.astimezone().strftime("%Y-%m-%d")
            )
            directory.mkdir(parents=True, exist_ok=True)
            self.path = directory / f"TEMP_hytera_slot{self.slot}_{uuid.uuid4().hex}.wav"
            self.writer = wave.open(str(self.path), "wb")
            self.writer.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
            self.samples = 0
        count = min(len(pcm), 90 * 8000 - self.samples)
        self.writer.writeframes(pcm[:count].astype("<i2").tobytes())
        self.samples += count
        if self.samples >= 90 * 8000:
            self._finish_file("maximum_90_seconds")
            self.cooldown = now + 2.0

    def tick(self, now: float):
        self.flush(now)
        if self.call is not None and (
            (self.closing_at is not None and now >= self.closing_at)
            or (self.last_audio and now - self.last_audio > 1.2)
            or (not self.last_audio and now - self.call_at > 2)
        ):
            self.finish("call_end" if self.closing_at else "audio_timeout")
            self.call = None
            self.reset_stream()

    def finish(self, reason: str):
        self.flush(time.time(), force=True)
        self._finish_file(reason)

    def _finish_file(self, reason: str):
        if self.writer is None or self.path is None:
            return
        self.writer.close()
        self.writer = None
        call = self.call
        duration = self.samples / 8000
        group = call.target if call and call.kind == "group" else None
        name = recording_name("DMR", self.started, duration, call.radio if call else None, group)
        path = available_path(self.path.parent, name)
        self.path.rename(path)
        path = self.archive.protect_file(path)
        call_id = uuid.uuid4().hex
        with self.archive.connect() as db:
            radio = str(call.radio) if call and call.radio is not None else None
            target = str(call.target) if call and call.target is not None else None
            group_id = str(group) if group is not None else None
            alias = db.execute(
                "SELECT name FROM aliases WHERE system='Hytera' AND ((kind='radio' AND identity=?) OR (kind='group' AND identity=?)) ORDER BY CASE kind WHEN 'radio' THEN 0 ELSE 1 END LIMIT 1",
                (radio, group_id),
            ).fetchone()
            db.execute(
                """INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason,
                radio_id,group_id,slot,title,system,destination_id,call_type,protocol_slot,timing_basis)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    call_id,
                    self.channel,
                    0,
                    self.started.isoformat(),
                    duration,
                    str(path.relative_to(self.archive.root)),
                    "DMR/Hytera-IP",
                    reason,
                    radio,
                    group_id,
                    self.slot,
                    alias[0] if alias else None,
                    "Hytera",
                    target,
                    call.kind if call else None,
                    self.slot,
                    "rtp_8000hz",
                ),
            )
        self.notify(
            {
                "kind": "archive_changed",
                "slot": self.slot,
                "call_id": call_id,
                "text": f"ID {radio or '—'} • Hedef {target or '—'} • Slot {self.slot} • {duration:.2f} sn kaydedildi • Eksik paket: {self.segment_lost}",
            }
        )
        self.path = None
        self.samples = self.segment_lost = 0


class HyteraReceiver:
    def __init__(self, archive: Archive):
        self.archive = archive
        self.monitor = LiveAudio()
        self.messages: queue.Queue = queue.Queue(maxsize=256)
        self.thread: threading.Thread | None = None
        self.cancel = threading.Event()

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def notify(self, message: dict):
        try:
            self.messages.put_nowait(message)
        except queue.Full:
            # UI must never stall UDP reception. A later snapshot includes counters.
            pass

    def start(self, profile: dict):
        if self.running:
            raise ValueError("Hytera alımı zaten açık.")
        for key in ("local_ip", "repeater_ip"):
            address = ipaddress.IPv4Address(profile[key])
            if address.is_unspecified or address.is_multicast or int(address) == 0xFFFFFFFF:
                raise ValueError("Tek bir cihazın IPv4 adresini girin.")
        ports = [int(profile[f"{kind}_ts{slot}"]) for slot in (1, 2) for kind in ("rcp", "rtp")]
        if len(set(ports)) != 4 or any(not 1 <= port <= 65535 for port in ports):
            raise ValueError("Dört ayrı ve geçerli UDP portu gerekli.")
        self.cancel.clear()
        self.thread = threading.Thread(target=self._run, args=(dict(profile),), daemon=True)
        self.thread.start()

    def stop(self):
        self.cancel.set()
        self.monitor.stop()

    def _run(self, profile: dict):
        sockets: dict[socket.socket, tuple[int, str, int]] = {}
        slots = {n: SlotRecorder(self.archive, n, self.monitor, self.notify) for n in (1, 2)}
        last_seen: dict[int, float] = {}
        last_sequence: dict[int, int] = {}
        session = self.archive.root / "hytera-sessions" / uuid.uuid4().hex
        log = None
        try:
            session.mkdir(parents=True)
            log = (session / "digital.jsonl").open("w", encoding="utf-8")
            for slot in (1, 2):
                for kind in ("rcp", "rtp"):
                    port = int(profile[f"{kind}_ts{slot}"])
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sockets[sock] = slot, kind, port
                    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    sock.bind((profile["local_ip"], port))
                    sock.sendto(bytes.fromhex("324200050000"), (profile["repeater_ip"], port))
            self.notify({"kind": "status", "text": "UDP alımı açık • Röleden yanıt bekleniyor"})
            next_heartbeat = next_snapshot = 0.0
            errors = 0
            while not self.cancel.is_set():
                now = time.time()
                if now >= next_heartbeat:
                    for sock, (_, _, port) in sockets.items():
                        sock.sendto(bytes.fromhex("324200020000"), (profile["repeater_ip"], port))
                    next_heartbeat = now + 2
                ready, _, _ = select.select(list(sockets), [], [], 0.05)
                for sock in ready:
                    slot, kind, port = sockets[sock]
                    try:
                        data, sender = sock.recvfrom(65535)
                    except ConnectionResetError:
                        continue
                    if sender != (profile["repeater_ip"], port):
                        continue
                    now = time.time()
                    try:
                        if data.startswith(b"2B"):
                            packet = transport(data)
                            if packet.slot is not None and packet.slot != slot:
                                raise ValueError("Port ve paketteki slot eşleşmiyor")
                            last_seen[port] = now
                            if packet.flags & (8 | 16):
                                raise RuntimeError(
                                    "Röle bağlantıyı kapattı veya reddetti; yeniden bağlanın."
                                )
                            if packet.acknowledgement:
                                sock.sendto(packet.acknowledgement, sender)
                            if packet.payload:
                                previous = last_sequence.get(port)
                                if (
                                    previous is not None
                                    and not 0 < (packet.sequence - previous) & 65535 < 32768
                                ):
                                    continue
                                last_sequence[port] = packet.sequence
                                status = call_status(packet.payload)
                                if kind == "rcp" and status is not None:
                                    slots[slot].control(status, now)
                                if kind == "rcp" and status is not None and status.voice:
                                    target_label = "Grup" if status.kind == "group" else "Hedef"
                                    self.notify(
                                        {
                                            "kind": "call",
                                            "slot": slot,
                                            "text": f"ID {status.radio or '—'} • {target_label} {status.target or '—'} • Slot {slot} • CC: iletilmiyor",
                                        }
                                    )
                                log.write(
                                    json.dumps(
                                        {
                                            "observed_utc": datetime.now(timezone.utc).isoformat(),
                                            "channel": slots[slot].channel,
                                            "protocol": "DMR/Hytera-IP",
                                            "category": "röle kontrol",
                                            "raw": f"Slot {slot} • {status} • HEX {data.hex()}",
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n"
                                )
                                log.flush()
                        elif kind == "rtp":
                            voice = voice_packet(data)
                            last_seen[port] = now
                            slots[slot].accept(voice, now)
                    except ValueError as exc:
                        errors += 1
                        if errors <= 10:
                            self.notify({"kind": "status", "text": f"Paket atlandı: {exc}"})
                for recorder in slots.values():
                    recorder.tick(time.time())
                if now >= next_snapshot:
                    linked = sum(now - at < 15 for at in last_seen.values())
                    self.notify(
                        {
                            "kind": "snapshot",
                            "linked": linked,
                            "errors": errors,
                            "slots": {
                                n: {
                                    "received": r.received,
                                    "lost": r.lost,
                                    "discarded": r.discarded,
                                    "recording": r.writer is not None,
                                }
                                for n, r in slots.items()
                            },
                        }
                    )
                    next_snapshot = now + 0.5
        except Exception as exc:
            self.notify({"kind": "error", "text": f"Hytera bağlantısı durdu: {exc}"})
        finally:
            for sock in sockets:
                sock.close()
            for recorder in slots.values():
                try:
                    recorder.finish("stopped")
                except Exception as exc:
                    self.notify(
                        {
                            "kind": "error",
                            "text": f"Kayıt tamamlanamadı; yerel dosya korundu: {exc}",
                        }
                    )
            if log is not None:
                log.close()
            self.notify({"kind": "stopped", "text": "Hytera alımı kapalı"})
