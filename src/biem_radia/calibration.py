"""Known-reference PPM calibration, independent of spectral peak telemetry."""

from __future__ import annotations

import json
import math
import tkinter as tk
from tkinter import messagebox, ttk


def reference_ppm(reference_hz: float, observed_hz: float, measurement_ppm: int) -> int:
    if not all(math.isfinite(v) and 24e6 <= v <= 1766e6 for v in (reference_hz, observed_hz)):
        raise ValueError("Referans ve gözlenen merkez 24–1766 MHz aralığında olmalı.")
    if not -200 <= measurement_ppm <= 200:
        raise ValueError("Ölçüm sırasındaki PPM −200…200 aralığında olmalı.")
    # librtlsdr uses xtal * (1 + ppm/1e6). A high displayed frequency needs LESS PPM.
    corrected = ((1 + measurement_ppm / 1e6) * reference_hz / observed_hz - 1) * 1e6
    target = round(corrected)
    if not -200 <= target <= 200:
        raise ValueError(
            "Hesaplanan PPM sınır dışında; frekansları ve ölçüm PPM değerini kontrol edin."
        )
    return target


class CalibrationPanel(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="SDR FREKANS KALİBRASYONU", padding=12)
        self.app = app
        self.reference = tk.StringVar(value="427.55000")
        self.observed = tk.StringVar()
        # This is the PPM used to make the measurement, not the subsequently saved result.
        self.measurement_ppm = tk.StringVar(value=app.ppm.get())
        self.status = tk.StringVar(
            value="Referans merkezini ölçün; hesaplanan düzeltme sonraki alımda uygulanır."
        )
        row = ttk.Frame(self)
        row.pack(fill="x")
        for index, (caption, variable) in enumerate(
            (
                ("Bilinen frekans / MHz", self.reference),
                ("Gözlenen merkez / MHz", self.observed),
                ("Ölçüm sırasındaki PPM", self.measurement_ppm),
            )
        ):
            ttk.Label(row, text=caption).grid(row=0, column=index, sticky="w", padx=(0, 12))
            ttk.Entry(row, textvariable=variable, width=23).grid(
                row=1, column=index, sticky="w", padx=(0, 12)
            )
        ttk.Button(row, text="Hesapla", command=self.preview).grid(row=1, column=3, padx=6)
        ttk.Button(row, text="PPM kaydet", command=self.save).grid(row=1, column=4)
        ttk.Label(self, textvariable=self.status, wraplength=900).pack(anchor="w", pady=(10, 4))
        ttk.Label(
            self,
            text="Seçili SDR için bilinen, kararlı bir sinyal merkezi kullanın. Dijital sinyalin tek tepe noktası merkez olmayabilir.\n"
            "Kayıtlı PPM her alıcı açılışında uygulanır; kanal frekansları değişmez. Yeni ölçümde ölçüm PPM alanını güncelleyin.",
            wraplength=900,
        ).pack(anchor="w")

    def calculate(self):
        return reference_ppm(
            float(self.reference.get().replace(",", ".")) * 1e6,
            float(self.observed.get().replace(",", ".")) * 1e6,
            int(self.measurement_ppm.get()),
        )

    def preview(self):
        try:
            target = self.calculate()
            self.status.set(f"Hesaplanan düzeltme: {target:+d} PPM • Henüz kaydedilmedi")
        except ValueError as exc:
            messagebox.showerror("SDR kalibrasyonu", str(exc))

    def save(self):
        try:
            if (
                self.app.receiver.running
                or self.app.radio.running
                or self.app.spectrum.worker.running
            ):
                raise ValueError(
                    "Kalibrasyon kaydı için önce alımı, spektrumu ve FM Radio'yu durdurun."
                )
            target = self.calculate()
            path = self.app.receiver_config_path
            settings = json.loads(path.read_text("utf-8")) if path.exists() else {}
            if not isinstance(settings, dict):
                raise ValueError("Alıcı ayarı nesne olmalı.")
            settings["ppm"] = str(target)
            pending = path.with_suffix(".json.tmp")
            pending.write_text(json.dumps(settings, indent=2), "utf-8")
            pending.replace(path)
            self.app.ppm.set(str(target))
            self.status.set(
                f"{target:+d} PPM kaydedildi • Sonraki alıcı açılışında otomatik uygulanacak"
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("SDR kalibrasyonu", str(exc))
