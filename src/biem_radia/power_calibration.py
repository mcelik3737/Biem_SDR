"""Explicit external-reference calibration; never infer dBm from tuner gain alone."""

import tkinter as tk
from tkinter import messagebox, ttk

from .rf_power import PowerCalibrations, live_power_text


def show_power_calibration(app):
    dialog = tk.Toplevel(app.root)
    dialog.title("Anten giriş gücü • dBm kalibrasyonu")
    dialog.transient(app.root)
    body = ttk.Frame(dialog, padding=20)
    body.pack(fill="both", expand=True)
    ttk.Label(body, text="Bilinen RF seviyesiyle kalibrasyon", font=("Segoe UI", 14, "bold")).pack(
        anchor="w"
    )
    ttk.Label(
        body,
        text=(
            "SDR'nin anten girişine ulaşan seviyesi ölçülmüş bir referans sinyal gerekir.\n"
            "Telsizin çıkış gücü, antene ulaşan güç değildir. Sadece kazanç çıkarmak dBm vermez.\n"
            "Önce kanalı dinlemeye alın; manuel kazanç kullanın. AGC ile dBm hesaplanmaz.\n"
            "Profil cihaz, frekans, mod, bant, PPM ve kazanç için geçerlidir.\n"
            "Tek noktalı referans yaklaşık sonuç verir; RF ölçüm cihazının yerini tutmaz."
        ),
        justify="left",
        wraplength=580,
    ).pack(anchor="w", pady=12)
    names = [card.name.get() for card in app.cards]
    channel = tk.StringVar(value=names[0] if names else "")
    ttk.Label(body, text="Referans sinyali dinleyen kanal").pack(anchor="w")
    ttk.Combobox(body, textvariable=channel, values=names, state="readonly", width=40).pack(
        anchor="w", pady=5
    )
    status = tk.StringVar()
    ttk.Label(body, textvariable=status).pack(anchor="w", pady=6)
    reference = tk.StringVar()
    ttk.Label(body, text="Anten girişinde bilinen güç / dBm (örn. −70)").pack(anchor="w")
    ttk.Entry(body, textvariable=reference, width=20).pack(anchor="w", pady=5)

    def selected():
        return next((c.latest_state for c in app.cards if c.name.get() == channel.get()), None)

    def refresh():
        if dialog.winfo_exists():
            status.set(live_power_text(selected()))
            dialog.after(400, refresh)

    def save():
        try:
            if not app.receiver.running:
                raise ValueError("Kalibrasyon için referans sinyali canlı dinleyin.")
            PowerCalibrations(app.archive.root).save_reference(
                selected() or {}, float(reference.get().replace(",", "."))
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("Güç kalibrasyonu", str(exc), parent=dialog)
            return
        messagebox.showinfo(
            "Kaydedildi",
            "Kalibrasyon kaydedildi. Uygulamak için alımı durdurup yeniden başlatın. Eski kayıtlara uygulanmaz.",
            parent=dialog,
        )
        dialog.destroy()

    ttk.Button(body, text="Referansı kaydet", command=save).pack(side="left", pady=12)
    ttk.Button(body, text="Kapat", command=dialog.destroy).pack(side="right", pady=12)
    refresh()
