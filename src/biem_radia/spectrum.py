"""Receive-only swept FFT measurement; no demodulation or recording."""

from __future__ import annotations

import ctypes
import logging
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np

from .models import SAMPLE_RATE
from .sources import USBSource
from .spectrum_plot import SpectrumDisplay

WINDOWS = {
    "Hamming": np.hamming,
    "Hann": np.hanning,
    "Blackman": np.blackman,
    "Dikdörtgen": np.ones,
}


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def sweep_centers(low: float, high: float) -> np.ndarray:
    if not all(math.isfinite(v) for v in (low, high)) or not 24e6 <= low < high <= 1.7e9:
        raise ValueError("24–1700 MHz arasında geçerli bir başlangıç/bitiş girin.")
    if high - low > 24e6:
        raise ValueError("Bir tarama en fazla 24 MHz olabilir; daha küçük aralık seçin.")
    count = math.ceil((high - low) / (SAMPLE_RATE * 0.75))
    step = (high - low) / count
    return low + step * (np.arange(count) + 0.5)


def fft_db(iq: np.ndarray, window: str, size: int = 2048) -> np.ndarray:
    weights = WINDOWS[window](size)
    frames = iq[: len(iq) // size * size].reshape(-1, size)
    if not len(frames):
        raise ValueError("FFT için yeterli örnek yok.")
    power = np.mean(abs(np.fft.fftshift(np.fft.fft(frames * weights, axis=1), axes=1)) ** 2, axis=0)
    return 10 * np.log10(np.maximum(power / weights.sum() ** 2, 1e-12))


class SpectrumWorker:
    def __init__(self):
        self.thread = None
        self.stop_event = threading.Event()
        self.messages = queue.Queue(maxsize=3)
        self.message_lock = threading.Lock()
        self.settle_ms = 60

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def stop(self):
        self.stop_event.set()

    def publish(self, message):
        # Dropping an old frame and consuming from Tk must be one transaction.
        with self.message_lock:
            if self.messages.full():
                self.messages.get_nowait()
            self.messages.put_nowait(message)

    def take_messages(self):
        with self.message_lock:
            result = []
            while True:
                try:
                    result.append(self.messages.get_nowait())
                except queue.Empty:
                    return result

    def start(self, dll, low, high, window, index, ppm, gain, agc):
        if not is_admin():
            raise PermissionError("Spektrum ölçümü için Windows yönetici yetkisi gerekli.")
        if self.running:
            raise ValueError("Spektrum zaten çalışıyor.")
        centers = sweep_centers(low, high)
        if window not in WINDOWS:
            raise ValueError("Geçersiz FFT penceresi.")
        self.rf_settings = (gain, agc, ppm)
        self.stop_event.clear()
        self.take_messages()
        self.publish({"status": "USB açılıyor • İlk ölçüm bekleniyor…"})
        self.thread = threading.Thread(
            target=self._run,
            args=(dll, low, high, centers, window, index, ppm, gain, agc),
            daemon=True,
        )
        self.thread.start()

    def _run(self, dll, low, high, centers, window, index, ppm, gain, agc):
        source = None
        stage = "USB açılışı"
        try:
            logging.info("Spectrum start: USB %s, %.0f–%.0f Hz", index, low, high)
            frequencies = np.linspace(low, high, 900)
            while not self.stop_event.is_set():
                gain, agc, ppm = self.rf_settings
                started = time.monotonic()
                values = np.full(900, -120.0)
                for i, center in enumerate(centers):
                    if self.stop_event.is_set():
                        return
                    self.publish(
                        {"status": f"Ölçülüyor {i + 1}/{len(centers)} • {center / 1e6:.5f} MHz"}
                    )
                    if source is None:
                        stage = "USB açılışı"
                        source = USBSource(
                            dll,
                            int(center),
                            index=index,
                            ppm=ppm,
                            gain_db=gain,
                            agc=agc,
                            synchronous=True,
                        )
                        changed = True
                        logging.info("Spectrum USB opened; waiting for first IQ block")
                    else:
                        stage = "frekans ayarı"
                        changed = source.tune_sweep(int(center), ppm, gain, agc)
                    stage = "USB örnek okuma"
                    discarded = 0
                    settle_samples = int(SAMPLE_RATE * self.settle_ms / 1000) if changed else 0
                    while discarded < settle_samples:
                        if self.stop_event.is_set():
                            return
                        discarded += len(source.read())
                    iq = source.read()
                    actual_gain = source.gain_db if hasattr(source, "gain_db") else gain
                    clipping = (
                        float(np.mean((abs(np.real(iq)) >= 0.98) | (abs(np.imag(iq)) >= 0.98)))
                        * 100
                    )
                    stage = "FFT hesaplama"
                    bins = fft_db(iq, window)
                    axis = np.fft.fftshift(np.fft.fftfreq(2048, 1 / SAMPLE_RATE)) + center
                    left = low if i == 0 else (centers[i - 1] + center) / 2
                    right = high if i == len(centers) - 1 else (center + centers[i + 1]) / 2
                    mask = (frequencies >= left) & (frequencies <= right)
                    values[mask] = np.interp(frequencies[mask], axis, bins)
                self.publish(
                    {
                        "values": values,
                        "low": low,
                        "high": high,
                        "settings": (gain, agc, ppm),
                        "window": window,
                        "status": f"Son tarama {time.monotonic() - started:.2f} sn • {time.strftime('%H:%M:%S')} • Kazanç {'AGC' if agc else str(actual_gain) + ' dB'} • ADC sınırında %{clipping:.1f} (son bant)",
                    }
                )
                self.stop_event.wait(max(0, 0.1 - (time.monotonic() - started)))
        except Exception as exc:
            logging.exception("Spectrum failed during %s", stage)
            self.publish({"status": f"Ölçüm durdu ({stage}): {exc}"})
        finally:
            if source is not None:
                try:
                    source.close()
                except Exception as exc:
                    logging.exception("Spectrum USB close failed")
                    self.publish({"status": f"USB kapatılamadı: {exc}"})
            logging.info("Spectrum worker exited")


class SpectrumPanel(SpectrumDisplay):
    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self.app = app
        self.worker = SpectrumWorker()
        self.low = tk.StringVar(value="420.0")
        self.high = tk.StringVar(value="421.0")
        self.window = tk.StringVar(value="Hamming")
        self.view = tk.StringVar(value="Spektrum + Şelale")
        self.status = tk.StringVar(
            value="Hazır • Yönetici ölçümü"
            if is_admin()
            else "Kilitli • Programı Windows'ta yönetici olarak çalıştırın."
        )
        self.rows = []
        self.photo = None
        ttk.Label(self, text="SPEKTRUM / ŞELALE", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=12)
        for title, variable, choices in [
            ("Başlangıç / MHz", self.low, None),
            ("Bitiş / MHz", self.high, None),
            ("FFT penceresi", self.window, list(WINDOWS)),
            ("Gösterim", self.view, ["Spektrum + Şelale", "Spektrum", "Şelale"]),
        ]:
            app._field(controls, title, variable, 19, choices)
        ttk.Button(
            controls,
            text="Ölçümü başlat",
            command=self.start,
            state="normal" if is_admin() else "disabled",
        ).pack(side="left", padx=8, pady=(16, 0))
        ttk.Button(controls, text="Durdur", command=self.worker.stop).pack(
            side="left", pady=(16, 0)
        )
        self.build_display_controls()
        speed_row = ttk.Frame(self)
        speed_row.pack(fill="x")
        self.speed = tk.StringVar(value="Hızlı / 60 ms")
        app._field(
            speed_row,
            "Bant geçiş beklemesi",
            self.speed,
            20,
            ["Hızlı / 60 ms", "Dengeli / 120 ms", "Kararlı / 250 ms"],
        )
        self.speed.trace_add(
            "write",
            lambda *args: setattr(
                self.worker,
                "settle_ms",
                {"Hızlı / 60 ms": 60, "Dengeli / 120 ms": 120, "Kararlı / 250 ms": 250}[
                    self.speed.get()
                ],
            ),
        )
        ttk.Label(
            speed_row, text="Hızlı mod: USB açık kalır • Kararsız tepelerde beklemeyi artırın"
        ).pack(side="left", padx=12, pady=(16, 0))
        ttk.Label(self, textvariable=self.status).pack(anchor="w", pady=4)
        ttk.Label(
            self,
            text="Seviye: dBFS / FFT bin; tepe eşiği kayıt squelch eşiği değildir. İşaretli bant yalnız görsel seçimdir.\nAralık / FFT değişince durdurup başlatın. Şelale: üst satır en yeni, her 3 piksel bir tam tarama. dBm kalibrasyonu ve otomatik tür tespiti yok.",
            wraplength=1050,
        ).pack(anchor="w", pady=4)
        band_row = ttk.Frame(self)
        band_row.pack(fill="x")
        ttk.Button(band_row, text="Tam bandı göster", command=self.full_band).pack(side="left")
        ttk.Button(
            band_row, text="Görünen bandı ölçüm aralığı yap", command=self.measure_visible
        ).pack(side="left", padx=8)
        ttk.Label(
            band_row,
            text="Sağ sürgüler: görünüm yakınlığı ve merkez • Sol sürgüler: seviye ve eşik",
        ).pack(side="left", padx=8)
        plot_area = ttk.Frame(self)
        plot_area.pack(fill="both", expand=True, pady=10)
        self.build_sidebars(plot_area)
        self.canvas = tk.Canvas(plot_area, background="#101b2d", highlightthickness=0, height=480)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Motion>", self.pointer)
        self.canvas.bind("<Button-1>", lambda e: self.pointer(e, lock=True))
        self.canvas.bind("<Button-3>", self.unlock)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.view.trace_add("write", lambda *args: self.redraw())

    def start(self):
        try:
            if self.app.receiver.running or self.app.radio.running:
                raise ValueError("Önce ana alımı ve FM RADIO'yu durdurun.")
            if self.app.source.get() != "USB":
                raise ValueError("Spektrum şu anda USB RTL-SDR kaynağını destekliyor.")
            self.worker.start(
                self.app.project / "vendor/rtl-sdr/package/x64/rtlsdr.dll",
                float(self.low.get().replace(",", ".")) * 1e6,
                float(self.high.get().replace(",", ".")) * 1e6,
                self.window.get(),
                self.app.devices.selected_index(),
                int(self.app.ppm.get()),
                float(self.app.usb_gain.get()),
                self.app.usb_agc.get() == "Tuner AGC",
            )
            self.rows.clear()
            self.last = self.smoothed = self.maximum = None
            self.measurement_key = None
            self.canvas.delete("all")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Spektrum", str(exc))

    def poll(self):
        for message in self.worker.take_messages():
            self.status.set(message["status"])
            if "values" in message:
                try:
                    self.draw(message)
                except Exception as exc:
                    # A drawing failure must not kill the application's Tk poll loop.
                    logging.exception("Spectrum drawing failed")
                    self.status.set(f"Spektrum çizilemedi: {exc}")
