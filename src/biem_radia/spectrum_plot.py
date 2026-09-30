"""Spectrum display controls and markers. All levels are FFT-bin dBFS."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

import numpy as np
from scipy.signal import find_peaks


def prominent_peaks(values, threshold, count=6):
    indices, _ = find_peaks(values, height=threshold, prominence=3, distance=12)
    return sorted(indices, key=lambda i: values[i], reverse=True)[:count]


def display_limits(reference, span):
    reference, span = float(reference), float(span)
    if (
        not all(math.isfinite(x) for x in (reference, span))
        or not -120 <= reference <= 10
        or not 10 <= span <= 120
    ):
        raise ValueError("Üst seviye −120…10 dBFS, görünüm aralığı 10…120 dB olmalı.")
    return reference - span, reference


class SpectrumDisplay(ttk.Frame):
    app: Any
    worker: Any
    canvas: tk.Canvas
    status: tk.StringVar
    view: tk.StringVar
    low: tk.StringVar
    high: tk.StringVar
    rows: list
    last: Any
    smoothed: Any
    maximum: Any
    photo: Any
    measurement_key: Any
    locked_hz: Any
    hover_hz: Any

    def build_display_controls(self):
        self.zoom = tk.DoubleVar(value=1)
        self.pan = tk.DoubleVar(value=50)
        self.reference = tk.DoubleVar(value=-25)
        self.dynamic_range = tk.DoubleVar(value=50)
        self.threshold = tk.DoubleVar(value=-50)
        self.bandwidth = tk.StringVar(value="12500")
        self.average = tk.StringVar(value="1")
        self.peak_hold = tk.BooleanVar(value=False)
        self.marker = tk.StringVar(
            value="Grafikte fareyle gezin • Sol tık: tepeye kilitle • Sağ tık: kilidi kaldır"
        )
        self.last = None
        self.smoothed = None
        self.maximum = None
        self.locked_hz = None
        self.hover_hz = None
        self.plot_bounds = (58, 900, 20, 200)
        self.measurement_key = None
        rf = ttk.Frame(self)
        rf.pack(fill="x", pady=3)
        for label, var, choices in [
            ("RF kazanç / dB", self.app.usb_gain, None),
            ("Kazanç modu", self.app.usb_agc, ["Manuel", "Tuner AGC"]),
            ("PPM", self.app.ppm, None),
            ("İşaretli bant / Hz", self.bandwidth, ["6250", "12500", "25000", "200000"]),
        ]:
            self.app._field(rf, label, var, 15, choices)
        ttk.Button(rf, text="RF ayarını uygula", command=self.apply_rf).pack(
            side="left", padx=8, pady=(16, 0)
        )
        ttk.Button(rf, text="Kilitli frekansa yakınlaş", command=self.zoom_marker).pack(
            side="left", pady=(16, 0)
        )
        scale = ttk.Frame(self)
        scale.pack(fill="x", pady=3)
        for label, var, choices in [
            ("Üst seviye / dBFS", self.reference, None),
            ("Görünüm aralığı / dB", self.dynamic_range, None),
            ("Tepe eşiği / dBFS", self.threshold, None),
            ("Ortalama / tarama", self.average, ["1", "2", "4", "8"]),
        ]:
            self.app._field(scale, label, var, 15, choices)
        ttk.Button(scale, text="Görünümü uygula", command=self.redraw).pack(
            side="left", padx=8, pady=(16, 0)
        )
        ttk.Button(scale, text="Otomatik ölçek", command=self.auto_scale).pack(
            side="left", pady=(16, 0)
        )
        ttk.Checkbutton(scale, text="Tepe tut", variable=self.peak_hold, command=self.redraw).pack(
            side="left", padx=8, pady=(16, 0)
        )
        ttk.Button(scale, text="Tepeleri sıfırla", command=self.reset_peaks).pack(
            side="left", pady=(16, 0)
        )
        ttk.Label(self, textvariable=self.marker, foreground="#174b78", wraplength=1400).pack(
            anchor="w", pady=6
        )

    def build_sidebars(self, parent):
        left = ttk.Frame(parent, padding=(0, 4, 6, 4))
        left.pack(side="left", fill="y")
        right = ttk.Frame(parent, padding=(6, 4, 0, 4))
        right.pack(side="right", fill="y")
        for host, title, variable, start, end, step in [
            (left, "Eşik\ndBFS", self.threshold, 10, -120, 1),
            (left, "Üst\ndBFS", self.reference, 10, -120, 1),
            (left, "Aralık\ndB", self.dynamic_range, 120, 10, 1),
            (right, "Yakınlık\n×", self.zoom, 20, 1, 0.1),
            (right, "Merkez\n%", self.pan, 100, 0, 1),
        ]:
            column = ttk.Frame(host)
            column.pack(side="left", fill="y")
            ttk.Label(column, text=title, justify="center").pack()
            tk.Scale(
                column,
                from_=start,
                to=end,
                resolution=step,
                variable=variable,
                orient="vertical",
                width=14,
                sliderlength=22,
                length=220,
                background="#f3f5f8",
                foreground="#334155",
                troughcolor="#d9e2ed",
                highlightthickness=0,
                command=lambda value: self.redraw(),
            ).pack(fill="y", expand=True)

    def visible_indices(self):
        if self.last is None:
            return np.array([], dtype=int)
        axis = np.linspace(self.last["low"], self.last["high"], len(self.smoothed))
        span = (axis[-1] - axis[0]) / max(1, self.zoom.get())
        center = axis[0] + (axis[-1] - axis[0]) * self.pan.get() / 100
        low = min(max(axis[0], center - span / 2), axis[-1] - span)
        begin = int(np.searchsorted(axis, low))
        end = int(np.searchsorted(axis, low + span, side="right"))
        return np.arange(min(begin, len(axis) - 2), min(len(axis), max(begin + 2, end)))

    def visible_band(self):
        indices = self.visible_indices()
        axis = np.linspace(self.last["low"], self.last["high"], len(self.smoothed))
        return float(axis[indices[0]]), float(axis[indices[-1]])

    def full_band(self):
        self.zoom.set(1)
        self.pan.set(50)
        self.redraw()

    def measure_visible(self):
        if self.last is None:
            return
        if self.worker.running:
            self.status.set("Ölçüm bandını değiştirmek için önce Durdur'a basın.")
            return
        low, high = self.visible_band()
        self.low.set(f"{low / 1e6:.6f}")
        self.high.set(f"{high / 1e6:.6f}")
        self.status.set("Görünen bant ölçüm aralığına aktarıldı • Ölçümü başlat")

    def apply_rf(self):
        try:
            if self.app.receiver.running or self.app.radio.running:
                raise ValueError("RF ayarı için ana alım ve FM RADIO kapalı olmalı.")
            gain = float(self.app.usb_gain.get().replace(",", "."))
            ppm = int(self.app.ppm.get())
            if not math.isfinite(gain) or not -10 <= gain <= 50 or not -200 <= ppm <= 200:
                raise ValueError("Kazanç −10…50 dB, PPM −200…200 olmalı.")
            self.worker.rf_settings = (gain, self.app.usb_agc.get() == "Tuner AGC", ppm)
            self.status.set(
                "RF ayarı sonraki tam taramada uygulanacak"
                if self.worker.running
                else "RF ayarı hazır; Ölçümü başlat düğmesine basın"
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("Spektrum RF", str(exc))

    def reset_peaks(self):
        self.maximum = None if self.smoothed is None else self.smoothed.copy()
        self.redraw()

    def auto_scale(self):
        if self.last is None:
            return
        values = self.last["values"]
        top = min(10, math.ceil((float(np.max(values)) + 8) / 5) * 5)
        bottom = max(-120, math.floor((float(np.percentile(values, 20)) - 8) / 5) * 5)
        self.reference.set(top)
        self.dynamic_range.set(min(120, max(20, top - bottom)))
        self.redraw()

    def zoom_marker(self):
        if self.locked_hz is None:
            self.status.set("Önce grafikte bir tepeye sol tıklayın.")
            return
        if self.worker.running:
            self.status.set("Yakınlaşmak için Durdur'a basın; sonra tekrar yakınlaşın.")
            return
        self.low.set(f"{max(24e6, self.locked_hz - 125000) / 1e6:.6f}")
        self.high.set(f"{min(1.7e9, self.locked_hz + 125000) / 1e6:.6f}")
        self.status.set("250 kHz aralık hazır • Ölçümü başlat")

    def pointer(self, event, lock=False):
        if self.last is None:
            return
        indices = self.visible_indices()
        values = self.smoothed[indices]
        low, high = self.visible_band()
        left, right, _, _ = self.plot_bounds
        fraction = np.clip((event.x - left) / (right - left), 0, 1)
        index = int(round(fraction * (len(values) - 1)))
        if lock:
            peaks = prominent_peaks(values, -120, count=len(values))
            nearby = [i for i in peaks if abs(i - index) * (right - left) / (len(values) - 1) <= 18]
            if nearby:
                index = min(nearby, key=lambda i: abs(i - index))
            self.locked_hz = low + index / (len(values) - 1) * (high - low)
        self.hover_hz = low + fraction * (high - low)
        self.draw_marker()

    def unlock(self, event=None):
        self.locked_hz = None
        self.draw_marker()

    def draw_marker(self):
        self.canvas.delete("marker")
        if self.last is None or self.smoothed is None:
            return
        low, high = self.visible_band()
        hz = self.locked_hz if self.locked_hz is not None else self.hover_hz
        if hz is None or not low <= hz <= high:
            return
        left, right, top, bottom = self.plot_bounds
        fraction = (hz - low) / (high - low)
        index = int(
            round(
                (hz - self.last["low"])
                / (self.last["high"] - self.last["low"])
                * (len(self.smoothed) - 1)
            )
        )
        level = float(self.smoothed[index])
        try:
            bw = float(self.bandwidth.get())
            threshold = float(self.threshold.get())
        except ValueError:
            return
        x = left + fraction * (right - left)
        half_width = bw / (high - low) * (right - left) / 2
        self.canvas.create_rectangle(
            max(left, x - half_width),
            top,
            min(right, x + half_width),
            bottom,
            outline="#fbbf24",
            dash=(3, 3),
            tags="marker",
        )
        self.canvas.create_line(
            x, top, x, max(bottom, self.canvas.winfo_height() - 28), fill="#fbbf24", tags="marker"
        )
        configured = [c for c in self.app.channels if abs(c.frequency_hz - hz) <= c.spacing_hz / 2]
        kind = "Tür: bilinmiyor (bu görünümde otomatik protokol çözümü yok)"
        if configured:
            c = min(configured, key=lambda c: abs(c.frequency_hz - hz))
            kind = f"Tanımlı kanal: {c.name} / {c.mode} • Tür RF'den doğrulanmadı"
        self.marker.set(
            f"{'KİLİTLİ' if self.locked_hz is not None else 'İMLEÇ'} • {hz / 1e6:.6f} MHz • {level:.1f} dBFS/bin • Eşiğe göre {level - threshold:+.1f} dB • {kind}"
        )

    def redraw(self):
        if self.last is None:
            return
        try:
            self.render()
        except (ValueError, tk.TclError) as exc:
            self.status.set(f"Görünüm ayarı: {exc}")

    def draw(self, message):
        values = np.asarray(message["values"])
        key = (message["low"], message["high"], message.get("settings"), message.get("window"))
        if key != self.measurement_key:
            self.rows.clear()
            self.maximum = self.smoothed = None
            self.measurement_key = key
        self.last = message
        try:
            average = max(1, min(8, int(self.average.get())))
        except ValueError:
            average = 1
        if self.smoothed is None:
            self.smoothed = values.copy()
        else:
            self.smoothed = 10 * np.log10(
                np.maximum(
                    10 ** (self.smoothed / 10) * (1 - 1 / average) + 10 ** (values / 10) / average,
                    1e-12,
                )
            )
        self.maximum = values.copy() if self.maximum is None else np.maximum(self.maximum, values)
        self.rows.insert(0, values.copy())
        self.rows = self.rows[:240]
        self.redraw()

    def render(self):
        minimum, maximum = display_limits(self.reference.get(), self.dynamic_range.get())
        threshold = float(self.threshold.get())
        if not math.isfinite(threshold) or not -120 <= threshold <= 10:
            raise ValueError("Tepe eşiği −120…10 dBFS olmalı.")
        indices = self.visible_indices()
        values = self.smoothed[indices]
        low, high = self.visible_band()
        canvas = self.canvas
        canvas.delete("all")
        width, height = max(400, canvas.winfo_width()), max(220, canvas.winfo_height())
        left, right, top = 65, width - 22, 28
        bottom = int(height * 0.5) if self.view.get() == "Spektrum + Şelale" else height - 36
        self.plot_bounds = (left, right, top, bottom)

        def xy(i, db):
            return (
                left + i * (right - left) / (len(values) - 1),
                top + np.clip((maximum - db) / (maximum - minimum), 0, 1) * (bottom - top),
            )

        if self.view.get() != "Şelale":
            for db in np.linspace(minimum, maximum, 6):
                y = xy(0, db)[1]
                canvas.create_line(left, y, right, y, fill="#304158")
                canvas.create_text(30, y, text=f"{db:.0f}", fill="#cbd5e1")
            canvas.create_text(left, 12, text="dBFS / FFT bin", anchor="w", fill="#cbd5e1")
            if self.peak_hold.get() and self.maximum is not None:
                canvas.create_line(
                    *[v for i, db in enumerate(self.maximum[indices]) for v in xy(i, db)],
                    fill="#c084fc",
                )
            canvas.create_line(
                *[v for i, db in enumerate(values) for v in xy(i, db)],
                fill="#5ed8bf",
                width=1.5,
            )
            if minimum <= threshold <= maximum:
                y = xy(0, threshold)[1]
                canvas.create_line(left, y, right, y, fill="#fb923c", dash=(7, 4))
                canvas.create_text(
                    right - 5,
                    y - 9,
                    text=f"Tepe eşiği {threshold:g} dBFS",
                    anchor="e",
                    fill="#fdba74",
                )
            for order, i in enumerate(prominent_peaks(values, threshold)):
                x, y = xy(i, values[i])
                hz = low + i / (len(values) - 1) * (high - low)
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#fde68a", outline="")
                canvas.create_text(
                    np.clip(x, left + 70, right - 70),
                    max(top + 18, y - 22 - order % 2 * 18),
                    text=f"{hz / 1e6:.5f} MHz\n{values[i]:.1f} dBFS",
                    fill="#fde68a",
                    font=("Segoe UI", 9),
                )
        if self.view.get() != "Spektrum":
            waterfall_top = bottom + 20 if self.view.get() == "Spektrum + Şelale" else top
            pixels_w = int(right - left) + 1
            pixels_h = max(1, height - 35 - waterfall_top)
            # Every completed sweep occupies three pixels; empty history stays dark.
            cols = np.round(np.linspace(0, len(values) - 1, pixels_w)).astype(int)
            history = np.array(self.rows)[:, indices][:, cols]
            colors = np.clip((history - minimum) / (maximum - minimum), 0, 1)
            rgb = np.stack(
                (
                    np.clip(colors * 3 - 1.5, 0, 1),
                    np.clip(colors * 2 - 0.4, 0, 1),
                    np.clip(0.2 + colors * 1.8, 0, 1),
                ),
                axis=-1,
            )
            raw = np.repeat((rgb * 255).astype(np.uint8), 3, axis=0)[:pixels_h]
            background = np.full((pixels_h, pixels_w, 3), [16, 27, 45], dtype=np.uint8)
            background[: len(raw)] = raw
            ppm = f"P6\n{pixels_w} {pixels_h}\n255\n".encode() + background.tobytes()
            self.photo = tk.PhotoImage(data=ppm, format="PPM")
            canvas.create_image(left, waterfall_top, anchor="nw", image=self.photo)
        for i in range(7):
            canvas.create_text(
                left + i * (right - left) / 6,
                height - 14,
                text=f"{(low + (high - low) * i / 6) / 1e6:.4f}",
                fill="#cbd5e1",
            )
        self.draw_marker()
