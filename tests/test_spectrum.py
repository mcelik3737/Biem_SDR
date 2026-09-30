import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import numpy as np
import pytest

from biem_radia.app import RadiaApp
from biem_radia.models import SAMPLE_RATE
from biem_radia.spectrum import SpectrumPanel, SpectrumWorker, fft_db, sweep_centers


def test_spectrum_mailbox_concurrent_overflow_and_drain():
    worker = SpectrumWorker()

    def produce():
        for number in range(10000):
            worker.publish({"status": str(number)})

    def consume():
        received = []
        for _ in range(10000):
            received.extend(int(item["status"]) for item in worker.take_messages())
        return received

    with ThreadPoolExecutor(max_workers=2) as executor:
        producer = executor.submit(produce)
        consumer = executor.submit(consume)
        producer.result(timeout=10)
        received = consumer.result(timeout=10)
    received.extend(int(item["status"]) for item in worker.take_messages())
    assert received == sorted(set(received))
    assert received[-1] == 9999
    assert worker.take_messages() == []


def test_spectrum_drawing_error_does_not_break_poll():
    worker = SpectrumWorker()
    statuses = []

    def fail(message):
        raise RuntimeError("test drawing failure")

    panel = SimpleNamespace(worker=worker, status=SimpleNamespace(set=statuses.append), draw=fail)
    worker.publish({"status": "measurement", "values": [1]})
    SpectrumPanel.poll(panel)
    assert "test drawing failure" in statuses[-1]
    worker.publish({"status": "next measurement"})
    SpectrumPanel.poll(panel)
    assert statuses[-1] == "next measurement"


@pytest.mark.parametrize("window", ["Hamming", "Hann", "Blackman", "Dikdörtgen"])
def test_fft_frequency_and_amplitude(window):
    tone_bin = 100
    n = np.arange(16384)
    iq = 0.25 * np.exp(2j * np.pi * tone_bin * n / 2048)
    values = fft_db(iq, window)
    assert np.argmax(values) == 1024 + tone_bin
    assert values.max() == pytest.approx(20 * np.log10(0.25), abs=0.01)
    assert abs((np.argmax(values) - 1024) * SAMPLE_RATE / 2048 - 46875) < 1


def test_sweep_coverage_and_admin_gate(monkeypatch):
    centers = sweep_centers(420e6, 422e6)
    assert len(centers) == 3
    assert centers[0] - SAMPLE_RATE * 0.375 <= 420e6
    assert centers[-1] + SAMPLE_RATE * 0.375 >= 422e6
    with pytest.raises(ValueError):
        sweep_centers(440e6, 400e6)
    with pytest.raises(ValueError):
        sweep_centers(400e6, 500e6)
    monkeypatch.setattr("biem_radia.spectrum.is_admin", lambda: False)
    with pytest.raises(PermissionError):
        SpectrumWorker().start(None, 420e6, 421e6, "Hamming", 0, 0, 19, False)


def test_spectrum_sweep_closes_source_and_measures_without_usb(monkeypatch):
    monkeypatch.setattr("biem_radia.spectrum.is_admin", lambda: True)
    opened, closed = [], []

    class Source:
        def __init__(self, dll, center, **kwargs):
            self.center = center
            opened.append(center)

        def tune_sweep(self, center, ppm, gain, agc):
            self.center = center
            return True

        def read(self):
            return np.ones(32768, dtype=complex) * 0.1

        def close(self):
            closed.append(self.center)

    monkeypatch.setattr("biem_radia.spectrum.USBSource", Source)
    worker = SpectrumWorker()
    messages = []

    def publish(message):
        messages.append(message)
        if "values" in message:
            worker.stop()

    monkeypatch.setattr(worker, "publish", publish)
    worker.start(None, 420e6, 422e6, "Hamming", 0, 15, 29, False)
    worker.thread.join(5)
    assert not worker.running and len(opened) == len(closed) == 1
    assert len(messages[-1]["values"]) == 900


def test_device_serial_reselection_and_spectrum_render(tmp_path, monkeypatch):
    root = tk.Tk()
    root.withdraw()
    app = RadiaApp(root, tmp_path)
    dll = tmp_path / "vendor/rtl-sdr/package/x64/rtlsdr.dll"
    dll.parent.mkdir(parents=True)
    dll.touch()
    items = [
        {"index": 0, "name": "Test", "manufacturer": "Maker", "product": "RTL", "serial": "A"},
        {"index": 1, "name": "Test", "manufacturer": "Maker", "product": "RTL", "serial": "B"},
    ]

    class Library:
        def __init__(self, path):
            pass

        def inventory(self):
            return items

        def close(self):
            pass

    monkeypatch.setattr("biem_radia.devices.RtlLibrary", Library)
    try:
        panel = app.devices
        panel.refresh()
        panel.select.current(1)
        panel.save()
        items[:] = [{**items[1], "index": 0}, {**items[0], "index": 1}]
        assert panel.selected_index() == 0
        items[:] = [items[1]]
        with pytest.raises(ValueError):
            panel.selected_index()
        app.spectrum.draw({"values": np.linspace(-100, -20, 900), "low": 420e6, "high": 421e6})
        assert (
            app.spectrum.photo.width()
            == int(app.spectrum.plot_bounds[1] - app.spectrum.plot_bounds[0]) + 1
        )
        assert len(app.spectrum.rows) == 1
    finally:
        for token in root.tk.splitlist(root.tk.call("after", "info")):
            root.after_cancel(token)
        root.destroy()
