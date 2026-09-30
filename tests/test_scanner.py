from pathlib import Path

import numpy as np

from biem_radia.engine import Receiver
from biem_radia.models import SAMPLE_RATE, Channel
from biem_radia.scanner import DmrScanGate, ScanGate
from biem_radia.storage import Archive


def test_dmr_requires_sync_and_releases_wrong_or_lost_cc():
    gate = DmrScanGate(-45, dwell=1, release=1)
    assert not gate.advance_dmr(-20, 1, None)
    assert gate.advance_dmr(-20, 1, None)
    for code in range(16):
        gate = DmrScanGate(-45, dwell=1, release=1)
        assert not gate.advance_dmr(-20, 0.5, code)
        assert gate.held and gate.color_code == code
        assert not gate.advance_dmr(-20, 30, code)
        assert not gate.advance_dmr(-20, 0.4, None)
        assert not gate.advance_dmr(-20, 0.4, code)
        assert gate.advance_dmr(-20, 1, (code + 1) % 16)
    assert DmrScanGate(-45).advance_dmr(-20, 2, 16)
    gate = DmrScanGate(-45)
    assert not gate.advance_dmr(-20, 0.1, 11)
    assert gate.advance_dmr(-80, 1, 11)


def test_scan_holds_carrier_and_restarts_release_after_short_gap():
    gate = ScanGate(-45, dwell=0.5, release=1)
    for _ in range(100):
        assert not gate.advance(-30, 0.1)
    for _ in range(5):
        assert not gate.advance(-60, 0.1)
    assert not gate.advance(-45, 0.1)
    assert not gate.advance(-60, 0.9)
    assert gate.advance(-60, 0.11)
    empty = ScanGate(-45, dwell=0.5)
    assert not empty.advance(-60, 0.4)
    assert empty.advance(-60, 0.11)


def test_dmr_scan_uses_auto_cc_without_changing_saved_channel(tmp_path, monkeypatch):
    receiver = Receiver(Archive(tmp_path))
    channel = Channel("DMR", 427500000, mode="DMR", color_code=11)

    def run(channels, *args):
        assert channels[0].color_code is None
        assert isinstance(args[-1], DmrScanGate)
        receiver.stop()
        return "stopped"

    monkeypatch.setattr(receiver, "_run", run)
    receiver._scan([channel], Path("unused"), "USB", "", 0, 0, 1, 19, 1)
    assert channel.color_code == 11


def test_scan_retunes_distant_channels_finalizes_and_stops(tmp_path, monkeypatch):
    opened = []
    receiver = Receiver(Archive(tmp_path))

    class Source:
        def __init__(self, dll, center, **kwargs):
            self.count = 0
            self.center = center
            self.closed = False
            opened.append(self)

        def read(self):
            self.count += 1
            if len(opened) == 2 and self.count >= 18:
                receiver.stop()
            # First visit: carrier remains well past dwell, then disappears.
            if self.count <= 55:
                t = (np.arange(24000) + self.count * 24000) / SAMPLE_RATE
                return 0.2 * np.exp(
                    -2j * np.pi * 100000 * t - 1j * 2.5 * np.cos(2 * np.pi * 1000 * t)
                )
            return np.zeros(24000, dtype=np.complex128)

        def close(self):
            self.closed = True

    monkeypatch.setattr("biem_radia.engine.USBSource", Source)
    receiver.start(
        [Channel("A", 446006250), Channel("B", 427500000)],
        Path("unused"),
        scan=True,
        scan_dwell=0.3,
        scan_release=0.7,
    )
    assert receiver.thread is not None
    receiver.thread.join(10)
    assert not receiver.running
    assert len(opened) == 2 and all(s.closed for s in opened)
    assert opened[0].count >= 80
    assert [s.center for s in opened] == [446106250, 427600000]
    rows = receiver.archive.search()
    assert {r["channel"] for r in rows} == {"A", "B"}
    messages = list(receiver.messages.queue)
    assert sum(m["kind"] == "stopped" for m in messages) == 1
    assert messages[-1] == {"kind": "stopped", "reason": "stopped"}


def test_five_frequency_scan_visits_every_channel_in_order(tmp_path, monkeypatch):
    receiver = Receiver(Archive(tmp_path))
    centers = []

    class QuietSource:
        def __init__(self, dll, center, **kwargs):
            centers.append(center)
            if len(centers) == 6:
                receiver.stop()

        def read(self):
            return np.zeros(48000, dtype=np.complex64)

        def close(self):
            pass

    monkeypatch.setattr("biem_radia.engine.USBSource", QuietSource)
    channels = [Channel(f"Channel {i}", 400000000 + i * 10000000) for i in range(5)]
    receiver.start(channels, Path("unused"), scan=True, scan_dwell=1.0)
    assert receiver.thread is not None
    receiver.thread.join(10)
    assert not receiver.running
    assert centers == [400100000, 410100000, 420100000, 430100000, 440100000, 400100000]
    assert not receiver.archive.search()
