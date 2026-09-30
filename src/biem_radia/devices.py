from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk

from .sources import RtlLibrary


class DevicesPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        self.path = app.archive.root / "device.json"
        self.items = []
        self.choice = tk.StringVar()
        self.saved = {}
        self.status = tk.StringVar(value="Cihaz listesi henüz yenilenmedi.")
        try:
            self.saved = json.loads(self.path.read_text("utf-8")) if self.path.exists() else {}
            if not isinstance(self.saved, dict):
                self.saved = {}
        except (ValueError, OSError):
            pass
        ttk.Label(self, text="SDR CİHAZLARI", font=("Segoe UI", 16, "bold")).pack(
            anchor="w", pady=(0, 12)
        )
        self.table = ttk.Treeview(
            self, columns=("index", "type", "product", "serial", "state"), show="headings", height=6
        )
        for key, label, width in [
            ("index", "USB kodu", 85),
            ("type", "SDR tipi", 150),
            ("product", "Üretici / ürün", 280),
            ("serial", "Seri numarası", 160),
            ("state", "Durum", 150),
        ]:
            self.table.heading(key, text=label)
            self.table.column(key, width=width)
        self.table.pack(fill="x")
        row = ttk.Frame(self)
        row.pack(fill="x", pady=16)
        ttk.Label(row, text="Kullanılacak USB alıcı").pack(side="left", padx=(0, 12))
        self.select = ttk.Combobox(row, textvariable=self.choice, state="readonly", width=65)
        self.select.pack(side="left")
        self.select.bind("<<ComboboxSelected>>", self.save)
        ttk.Button(row, text="Cihazları yenile", command=self.refresh).pack(side="left", padx=12)
        ttk.Label(self, textvariable=self.status, wraplength=1000).pack(anchor="w", pady=8)
        self.network = tk.StringVar()
        ttk.Label(self, textvariable=self.network, wraplength=1000).pack(anchor="w", pady=12)
        ttk.Label(
            self,
            text="USB kodu takma sırasıyla değişebilir. Benzersiz seri numarası varsa yeniden eşleştirilir.\nAynı seri numaralı cihazlarda USB kodunu kontrol edin. Görünüyor olması cihazın boşta olduğunu göstermez.\nBu sürümde bir USB alıcı seçilir; 2–3 cihazla bağımsız eşzamanlı alım sonraki aşamadır.",
            wraplength=1000,
        ).pack(anchor="w", pady=12)

    def save(self, event=None):
        index = self.select.current()
        if 0 <= index < len(self.items):
            self.saved = {
                "index": self.items[index]["index"],
                "serial": self.items[index]["serial"],
            }
            try:
                self.path.write_text(json.dumps(self.saved, indent=2), "utf-8")
            except OSError as exc:
                self.status.set(str(exc))

    def refresh(self):
        dll = self.app.project / "vendor/rtl-sdr/package/x64/rtlsdr.dll"
        self.table.delete(*self.table.get_children())
        self.items = []
        try:
            if dll.exists():
                library = RtlLibrary(dll)
                try:
                    self.items = [dict(item) for item in library.inventory()]
                finally:
                    library.close()
            labels = []
            for item in self.items:
                labels.append(
                    f"USB {item['index']} • {item['name']} • SN {item['serial'] or 'yok'}"
                )
                self.table.insert(
                    "",
                    "end",
                    values=(
                        f"USB {item['index']}",
                        "RTL-SDR",
                        item["manufacturer"] + " / " + item["product"],
                        item["serial"] or "yok",
                        "USB'de görünüyor",
                    ),
                )
            self.select.configure(values=labels)
            matches = [
                i
                for i, item in enumerate(self.items)
                if self.saved.get("serial") and item["serial"] == self.saved["serial"]
            ]
            fallback = next(
                (
                    i
                    for i, item in enumerate(self.items)
                    if item["index"] == self.saved.get("index", 0)
                ),
                -1,
            )
            selected = (
                matches[0]
                if len(matches) == 1
                else fallback
                if not self.saved.get("serial") or len(matches) > 1
                else -1
            )
            if selected >= 0:
                self.select.current(selected)
            else:
                self.choice.set("")
            self.status.set(
                f"{len(self.items)} USB alıcı görünüyor. Durum son yenileme anına aittir."
                if self.items
                else "USB RTL-SDR bağlı değil veya sürücü cihazı listelemiyor."
            )
        except (OSError, ValueError) as exc:
            self.status.set(f"Cihaz listesi alınamadı: {exc}")
        self.network.set(
            f"Ethernet SDR / rtl_tcp: {self.app.host.get()}:{self.app.port.get()} • {'Ana alım çalışıyor' if self.app.source.get() == 'rtl_tcp' and self.app.receiver.running else 'Bağlantı doğrulanmadı'}\nHytera HR659: {self.app.repeater_panel.fields['repeater_ip'].get() or 'IP girilmedi'} • Sürücü henüz etkin değil"
        )

    def selected_index(self):
        # Re-enumerate before opening so stale USB order cannot silently pick another serial.
        self.save()
        self.refresh()
        selected = self.select.current()
        if selected < 0 or selected >= len(self.items):
            raise ValueError("SDR Cihazları sekmesinden bağlı bir USB alıcı seçin.")
        return self.items[selected]["index"]
