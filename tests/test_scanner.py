from pathlib import Path

import numpy as np

from biem_radia.engine import Receiver
from biem_radia.models import SAMPLE_RATE, Channel
from biem_radia.scanner import ScanGate
from biem_radia.storage import Archive


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
