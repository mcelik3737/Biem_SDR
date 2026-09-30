"""Offline Hytera connection profile; saving never opens a network connection."""

from __future__ import annotations

import ipaddress
import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


class RepeaterSettingsPanel(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, data_root: Path):
        super().__init__(parent, padding=20)
        self.path = data_root / "hytera.json"
        self.fields = {
            key: tk.StringVar(value=value)
            for key, value in {
                "model": "HR659 UHF",
                "firmware": "2.5",
                "repeater_ip": "",
                "local_ip": "",
                "rcp_ts1": "30009",
                "rcp_ts2": "30010",
                "rtp_ts1": "30012",
                "rtp_ts2": "30014",
            }.items()
        }
        self.status = tk.StringVar(value="Bağlı değil • Şimdilik yalnızca bağlantı ayarları")
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text("utf-8"))
                if not isinstance(saved, dict):
                    raise ValueError("Ayar dosyası nesne olmalı.")
                for key, variable in self.fields.items():
                    if key in saved:
                        variable.set(str(saved[key]))
            except (ValueError, OSError) as exc:
                self.status.set(f"Ayarlar okunamadı: {exc}")
        ttk.Label(self, text="HYTERA RÖLE / ETHERNET", font=("Segoe UI", 16, "bold")).pack(
            anchor="w", pady=(0, 12)
        )
        ttk.Label(self, textvariable=self.status, foreground="#246293").pack(anchor="w")
        form = ttk.Frame(self)
        form.pack(anchor="w", pady=18)
        labels = {
            "model": "Röle modeli",
            "firmware": "Firmware sürümü (cihazda doğrulanacak)",
            "repeater_ip": "Röle IP adresi",
            "local_ip": "PC yerel IP adresi (isteğe bağlı)",
            "rcp_ts1": "Slot 1 / Kontrol UDP portu",
            "rcp_ts2": "Slot 2 / Kontrol UDP portu",
            "rtp_ts1": "Slot 1 / Ses UDP portu",
            "rtp_ts2": "Slot 2 / Ses UDP portu",
        }
        for row, (key, label) in enumerate(labels.items()):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 24), pady=6)
            ttk.Entry(form, textvariable=self.fields[key], width=28).grid(
                row=row, column=1, sticky="w", pady=6
            )
        ttk.Button(self, text="Bağlantı ayarlarını kaydet", command=self.save).pack(anchor="w")
        ttk.Label(
            self,
            text="IP Dispatch bağlantısı henüz etkin değil. Röle bağlandığında iki slotun ses ve "
            "ID/grup bilgileriyle canlı test yapılacak.\nPortlar HytBridge örneğinden alınmıştır; "
            "rölenin gerçek ayarlarıyla doğrulanmalıdır. Ayarları kaydetmek bağlantı başlatmaz.",
            wraplength=850,
            foreground="#526174",
        ).pack(anchor="w", pady=20)

    def save(self) -> bool:
        values = {key: variable.get().strip() for key, variable in self.fields.items()}
        try:
            for key in ("repeater_ip", "local_ip"):
                if values[key]:
                    address = ipaddress.IPv4Address(values[key])
                    if address.is_unspecified or address.is_multicast or int(address) == 0xFFFFFFFF:
                        raise ValueError("Tek bir cihazın IPv4 adresini girin.")
            ports = [int(values[key]) for key in ("rcp_ts1", "rcp_ts2", "rtp_ts1", "rtp_ts2")]
            if any(port < 1 or port > 65535 for port in ports) or len(set(ports)) != 4:
                raise ValueError("UDP portları 1–65535 arasında ve birbirinden farklı olmalı.")
            pending = self.path.with_suffix(".json.tmp")
            pending.write_text(json.dumps(values, ensure_ascii=False, indent=2), "utf-8")
            pending.replace(self.path)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Hytera bağlantı ayarları", str(exc))
            return False
        self.status.set("Ayarlar kaydedildi • Bağlı değil • Canlı test bekleniyor")
        return True
