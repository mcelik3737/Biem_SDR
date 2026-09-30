import json
import threading

import pytest

from biem_radia.hytera_snmp import (
    ALARM_BASE,
    UPTIME,
    SnmpMessage,
    SnmpMonitor,
    _encode,
    _fields,
    _tlv,
    get_request,
    parse_snmp,
    repeater_badge,
)


def response(request, value=b"\x02\x01\x00", error=0):
    outer = _fields(_tlv(request)[1])
    fields = _fields(outer[2][1])
    oid = _fields(_fields(fields[-1][1])[0][1])[0]
    varbind = _encode(48, _encode(48, _encode(*oid) + value))
    pdu = _encode(0xA2, _encode(*fields[0]) + bytes([2, 1, error, 2, 1, 0]) + varbind)
    return _encode(48, _encode(*outer[0]) + _encode(*outer[1]) + pdu)


def trap(oid, value, version=0):
    parsed = _fields(_tlv(response(get_request(123, oid), value))[1])
    pdu = _fields(parsed[2][1])
    if version == 0:
        payload = (
            b"\x06\x03\x2b\x06\x01\x40\x04\xc0\xa8\x01\x62\x02\x01\x06\x02\x01\x01\x43\x01\x01"
            + _encode(*pdu[-1])
        )
    else:
        payload = b"".join(_encode(*f) for f in pdu)
    return _encode(
        48,
        bytes([2, 1, version])
        + _encode(4, b"private-test-secret")
        + _encode(0xA4 if version == 0 else 0xA7, payload),
    )


def test_get_only_and_realistic_v1_v2_traps():
    request = get_request(32768, UPTIME)
    assert _fields(_tlv(request)[1])[2][0] == 0xA0
    result = parse_snmp(response(request, b"\x43\x03\x01\x02\x03"))
    assert result.request_id == 32768 and result.values == ((UPTIME, 0x43, 66051),)
    for version in (0, 1):
        result = parse_snmp(trap(ALARM_BASE + "4.0", b"\x02\x01\xff", version))
        assert result.kind == "trap" and result.values[0][2] == -1
        assert "secret" not in repr(result)


def test_malformed_packets_and_requests_are_not_observations():
    valid = response(get_request(13, UPTIME))
    for n in range(len(valid)):
        with pytest.raises(ValueError):
            parse_snmp(valid[:n])
    for invalid in (valid + b"\x00", b"\x30\x80", get_request(1, UPTIME), b"a" * 32769):
        with pytest.raises(ValueError):
            parse_snmp(invalid)


def test_alarm_latching_unknown_and_stale_are_not_all_clear(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("biem_radia.hytera_snmp.time.monotonic", lambda: clock[0])
    monitor = SnmpMonitor(tmp_path)
    monitor.thread = threading.current_thread()
    monitor.started = 100
    oid = ALARM_BASE + "2.0"
    monitor.observe(parse_snmp(trap(oid, b"\x02\x01\x02")))
    assert repeater_badge(
        voice_running=True, linked=4, snmp=monitor.snapshot(), configured=True
    ) == ("Alarm", "red")
    monitor.observe(parse_snmp(trap(oid, b"\x02\x01\xff")))
    assert monitor.snapshot()["active"] == ["Sıcaklık: Yüksek"]
    clock[0] = 140
    monitor.observe(SnmpMessage("response", 2, 0, "", ((UPTIME, 0x43, 100),)))
    assert monitor.snapshot()["fresh"] and monitor.snapshot()["active_stale"]
    assert (
        repeater_badge(voice_running=True, linked=4, snmp=monitor.snapshot(), configured=True)[0]
        == "Son alarm • veri eski"
    )
    monitor.observe(parse_snmp(trap(oid, b"\x02\x01\x00")))
    assert not monitor.snapshot()["active"] and monitor.snapshot()["normal"] == 1
    monitor.observe(parse_snmp(trap(ALARM_BASE + "4.0", b"\x02\x01\xff")))
    assert monitor.snapshot()["unknown"] == 1
    clock[0] = 180
    assert not monitor.snapshot()["fresh"] and monitor.snapshot()["normal"] == 0
    events = "".join(p.read_text("utf-8") for p in (tmp_path / "hytera-status").glob("*"))
    assert "private-test-secret" not in events and "Sıcaklık: Yüksek" in events
    assert all(json.loads(line)["protocol"] == "SNMP" for line in events.splitlines())


def test_presence_voice_fault_and_no_response_are_independent(tmp_path, monkeypatch):
    monkeypatch.setattr("biem_radia.hytera_snmp.time.monotonic", lambda: 100)
    monitor = SnmpMonitor(tmp_path)

    def badge(voice=False, linked=0):
        return repeater_badge(
            voice_running=voice, linked=linked, snmp=monitor.snapshot(), configured=True
        )

    assert badge() == ("Durum bilinmiyor", "gray")
    monitor.thread = threading.current_thread()
    monitor.started = 50
    assert badge() == ("Yanıt yok", "red")
    monitor.last_seen = 99
    assert badge() == ("Röle var", "green")
    assert badge(True) == ("Röle var • ses yok", "orange")
    assert badge(True, 2) == ("Kısmi bağlantı", "orange")
    assert badge(True, 4) == ("Bağlı", "green")
    monitor.last_seen = 50
    assert badge(True, 4) == ("Ses bağlı • SNMP yok", "orange")


def test_socket_filtering_read_only_and_release(tmp_path, monkeypatch):
    monitor = SnmpMonitor(tmp_path)
    monitor.started = 0
    sockets, sent = [], []

    class FakeSocket:
        def __init__(self, *args):
            self.incoming = []
            self.closed = False
            sockets.append(self)

        def bind(self, address):
            self.address = address
            if address[1] == 162:
                high = trap(ALARM_BASE + "2.0", b"\x02\x01\x02")
                self.incoming.extend(
                    [(high, ("192.168.1.99", 161)), (b"bad", ("192.168.1.98", 161))]
                )

        def setsockopt(self, *args):
            pass

        def sendto(self, data, address):
            sent.append((data, address))
            self.incoming.append((response(data), ("192.168.1.98", 161)))

        def recvfrom(self, size):
            return self.incoming.pop(0)

        def close(self):
            self.closed = True

    def ready(read, *args):
        pending = [s for s in read if s.incoming]
        if not pending:
            monitor.cancel.set()
        return pending, [], []

    monkeypatch.setattr("biem_radia.hytera_snmp.socket.socket", FakeSocket)
    monkeypatch.setattr("biem_radia.hytera_snmp.select.select", ready)
    monitor._run("192.168.1.118", "192.168.1.98")
    assert len(sent) == 10 and all(address == ("192.168.1.98", 161) for _, address in sent)
    assert all(_fields(_tlv(data)[1])[2][0] == 0xA0 for data, _ in sent)
    assert all(s.closed for s in sockets)
    assert len(monitor.alarms) == 9 and not monitor.snapshot()["active"]
