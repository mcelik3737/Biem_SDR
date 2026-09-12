from __future__ import annotations

import argparse
import json
import logging
import math
import os
import queue
import tkinter as tk
import winsound
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from .engine import Receiver
from .models import Channel
from .storage import Archive

ROOT = Path.cwd()


class RadiaApp:
    def __init__(self, root: tk.Tk, project: Path):
        self.root, self.project = root, project
        self.archive = Archive(project / "data")
        self.receiver = Receiver(self.archive)
        self.config_path = self.archive.root / "channels.json"
        self.channels = [Channel("PMR 01", 446_006_250, squelch_db=-48)]
        if self.config_path.exists():
            try:
                self.channels = [
                    Channel(**item) for item in json.loads(self.config_path.read_text("utf-8"))
                ]
            except (ValueError, TypeError) as exc:
                messagebox.showerror("Kanal ayarları", f"Ayar dosyası okunamadı: {exc}")
        self.last_count = -1
        self.closing = False
        root.title("BİEM Radia • Dispatcher / Analog FM")
        root.geometry("1240x820")
        root.minsize(1050, 700)
        root.configure(bg="#101b2d")
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#17253b", foreground="#e5edf8")
        style.configure("TFrame", background="#101b2d")
        style.configure("TLabel", background="#101b2d")
        style.configure("TLabelframe", background="#101b2d", bordercolor="#354761")
        style.configure("TLabelframe.Label", background="#101b2d", foreground="#74d9cc")
        style.configure(
            "TEntry", fieldbackground="#21334d", foreground="#ffffff", insertcolor="#ffffff"
        )
        style.configure("TCombobox", fieldbackground="#21334d", foreground="#ffffff")
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#21334d")],
            foreground=[("readonly", "#ffffff")],
        )
        style.configure("TButton", padding=(12, 7), background="#294667")
        style.map("TButton", background=[("active", "#326283")])
        style.configure(
            "Treeview",
            background="#17253b",
            fieldbackground="#17253b",
            foreground="#e5edf8",
            rowheight=31,
        )
        style.configure("Treeview.Heading", background="#233853", foreground="#b6c9e4", padding=7)
        style.map("Treeview", background=[("selected", "#285f73")])

        outer = ttk.Frame(root, padding=22)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text="BİEM  /  RADIA", font=("Segoe UI", 24, "bold")).pack(side="left")
        ttk.Label(header, text="DİSPATCHER   •   ANALOG FM", foreground="#74d9cc").pack(
            side="right"
        )
        self.status = tk.StringVar(value="Alıcı beklemede • Kayıt başlatılmadı")
        ttk.Label(
            outer,
            textvariable=self.status,
            font=("Segoe UI", 12),
            foreground="#74d9cc",
            padding=(0, 14),
        ).pack(anchor="w")

        setup = ttk.LabelFrame(outer, text="ALICI VE KANALLAR", padding=12)
        setup.pack(fill="x")
        row = ttk.Frame(setup)
        row.pack(fill="x")
        self.source = tk.StringVar(value="USB")
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="1234")
        self.ppm = tk.StringVar(value="0")
        self.usb_gain = tk.StringVar(value="19")
        self._field(row, "Kaynak", self.source, 10, ["USB", "rtl_tcp"])
        self._field(row, "Ethernet SDR adresi", self.host, 17)
        self._field(row, "Port", self.port, 7)
        self._field(row, "PPM düzeltme", self.ppm, 8)
        self._field(row, "USB kazanç / dB", self.usb_gain, 10)
        self.start_button = ttk.Button(row, text="▶ Alımı başlat", command=self.start)
        self.start_button.pack(side="left", padx=(20, 6), pady=(16, 0))
        self.stop_button = ttk.Button(row, text="■ Durdur", command=self.receiver.stop)
        self.stop_button.pack(side="left", pady=(16, 0))

        edit = ttk.Frame(setup)
        edit.pack(fill="x", pady=(12, 8))
        self.name = tk.StringVar(value="PMR 01")
        self.freq = tk.StringVar(value="446.00625")
        self.spacing = tk.StringVar(value="12500")
        self.bandwidth = tk.StringVar(value="12500")
        self.squelch = tk.StringVar(value="-48")
        for label, variable, width, values in [
            ("Kanal adı", self.name, 20, None),
            ("Frekans / MHz", self.freq, 14, None),
            ("Aralık / Hz", self.spacing, 9, ["6250", "12500", "25000"]),
            ("Filtre / Hz", self.bandwidth, 9, None),
            ("Squelch / dBFS", self.squelch, 10, None),
        ]:
            self._field(edit, label, variable, width, values)
        ttk.Button(edit, text="Ekle / güncelle", command=self.save_channel).pack(
            side="left", padx=8, pady=(16, 0)
        )
        ttk.Button(edit, text="Sil", command=self.remove_channel).pack(side="left", pady=(16, 0))
        self.channel_table = ttk.Treeview(
            setup,
            columns=("name", "frequency", "spacing", "filter", "squelch"),
            show="headings",
            height=3,
        )
        for key, label in zip(
            self.channel_table["columns"],
            ["Kanal", "MHz", "Aralık / Hz", "Filtre / Hz", "Squelch / dBFS"],
            strict=True,
        ):
            self.channel_table.heading(key, text=label)
            self.channel_table.column(key, width=150)
        self.channel_table.pack(fill="x")
        self.channel_table.bind("<<TreeviewSelect>>", self.select_channel)
        self.refresh_channels()
        self.levels = tk.StringVar(
            value="Tüm listedeki kanallar eşzamanlı alınır. Ayar değişikliği için alımı durdurun."
        )
        ttk.Label(setup, textvariable=self.levels, foreground="#a7bbd4", padding=(0, 8)).pack(
            anchor="w"
        )

        archive_box = ttk.LabelFrame(outer, text="KONUŞMA ARŞİVİ", padding=12)
        archive_box.pack(fill="both", expand=True, pady=(16, 0))
        search = ttk.Frame(archive_box)
        search.pack(fill="x", pady=(0, 10))
        self.search_text = tk.StringVar()
        self.search_day = tk.StringVar()
        self._field(search, "Kanal adı / başlık / ID", self.search_text, 32)
        self._field(search, "Tarih / YYYY-MM-DD (yerel)", self.search_day, 24)
        ttk.Button(search, text="Ara / yenile", command=self.refresh_archive).pack(
            side="left", padx=10, pady=(16, 0)
        )
        ttk.Button(search, text="▶ Seçili kaydı dinle", command=self.play).pack(
            side="left", pady=(16, 0)
        )
        ttk.Button(search, text="Sesi kes", command=lambda: winsound.PlaySound(None, 0)).pack(
            side="left", padx=8, pady=(16, 0)
        )
        columns = ("time", "channel", "frequency", "duration", "source", "identity")
        self.calls = ttk.Treeview(archive_box, columns=columns, show="headings", height=6)
        for key, label, width in zip(
            columns,
            [
                "Tarih ve saat (yerel)",
                "Kanal / başlık",
                "MHz",
                "Kayıt süresi",
                "Kaynak",
                "ID / Grup / Slot",
            ],
            [195, 220, 120, 105, 90, 145],
            strict=True,
        ):
            self.calls.heading(key, text=label)
            self.calls.column(key, width=width)
        scrollbar = ttk.Scrollbar(archive_box, orient="vertical", command=self.calls.yview)
        self.calls.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.calls.pack(fill="both", expand=True)
        self.calls.bind("<Double-1>", lambda event: self.play())
        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(12, 0), side="bottom", before=archive_box)
        self.count = tk.StringVar(value="")
        ttk.Label(footer, textvariable=self.count, foreground="#a7bbd4").pack(side="left")
        ttk.Button(
            footer, text="Kayıt klasörünü aç", command=lambda: os.startfile(str(self.archive.root))
        ).pack(side="right")
        ttk.Label(
            footer, text="Analog FM'de ID / grup / slot bilgisi yoktur.  ", foreground="#a7bbd4"
        ).pack(side="right")
        self.refresh_archive()
        root.after(200, self.poll)

    def _field(self, parent, label, variable, width, choices=None):
        frame = ttk.Frame(parent)
        frame.pack(side="left", padx=(0, 8))
        ttk.Label(frame, text=label, foreground="#a7bbd4").pack(anchor="w", pady=(0, 4))
        widget = (
            ttk.Entry(frame, textvariable=variable, width=width)
            if choices is None
            else ttk.Combobox(
                frame, textvariable=variable, values=choices, width=width, state="readonly"
            )
        )
        widget.pack()

    def refresh_channels(self):
        self.channel_table.delete(*self.channel_table.get_children())
        for i, c in enumerate(self.channels):
            self.channel_table.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    c.name,
                    f"{c.frequency_hz / 1e6:.5f}",
                    c.spacing_hz,
                    c.bandwidth_hz,
                    c.squelch_db,
                ),
            )

    def select_channel(self, event=None):
        selected = self.channel_table.selection()
        if selected:
            c = self.channels[int(selected[0])]
            for variable, value in [
                (self.name, c.name),
                (self.freq, f"{c.frequency_hz / 1e6:.5f}"),
                (self.spacing, c.spacing_hz),
                (self.bandwidth, c.bandwidth_hz),
                (self.squelch, c.squelch_db),
            ]:
                variable.set(str(value))

    def save_channel(self):
        if self.receiver.running:
            messagebox.showinfo("Alım açık", "Kanal ayarını değiştirmeden önce alımı durdurun.")
            return
        try:
            channel = Channel(
                self.name.get().strip(),
                round(float(self.freq.get().replace(",", ".")) * 1e6),
                int(self.spacing.get()),
                int(self.bandwidth.get()),
                float(self.squelch.get()),
            )
            found = next(
                (
                    i
                    for i, c in enumerate(self.channels)
                    if c.name.casefold() == channel.name.casefold()
                ),
                None,
            )
            if found is not None:
                self.channels[found] = channel
            else:
                if len(self.channels) >= 8:
                    raise ValueError("En fazla 8 kanal eklenebilir.")
                self.channels.append(channel)
            self._save()
        except ValueError as exc:
            messagebox.showerror("Kanal ayarı", str(exc))

    def remove_channel(self):
        if self.receiver.running:
            return
        selected = self.channel_table.selection()
        if selected:
            self.channels.pop(int(selected[0]))
            self._save()

    def _save(self):
        self.config_path.write_text(
            json.dumps([asdict(c) for c in self.channels], ensure_ascii=False, indent=2), "utf-8"
        )
        self.refresh_channels()

    def start(self):
        try:
            ppm = int(self.ppm.get())
            port = int(self.port.get())
            usb_gain = float(self.usb_gain.get())
            if not math.isfinite(usb_gain) or not -10 <= usb_gain <= 50:
                raise ValueError("USB kazancı −10…50 dB aralığında olmalı.")
            if not -200 <= ppm <= 200 or not 1 <= port <= 65535:
                raise ValueError("PPM −200…200, port 1…65535 aralığında olmalı.")
            self.receiver.start(
                self.channels.copy(),
                self.project / "vendor/rtl-sdr/package/x64/rtlsdr.dll",
                self.source.get(),
                self.host.get(),
                port,
                ppm,
                usb_gain,
            )
            self.start_button.configure(state="disabled")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Alıcı", str(exc))

    def refresh_archive(self):
        try:
            rows = self.archive.search(self.search_text.get(), self.search_day.get())
        except ValueError:
            messagebox.showerror("Tarih", "Tarihi YYYY-MM-DD biçiminde yazın veya boş bırakın.")
            return
        selected = self.calls.selection()
        self.calls.delete(*self.calls.get_children())
        for r in rows:
            identities = " / ".join(
                str(r[k]) if r[k] is not None else "—" for k in ("radio_id", "group_id", "slot")
            )
            self.calls.insert(
                "",
                "end",
                iid=r["id"],
                values=(
                    datetime.fromisoformat(r["started_utc"])
                    .astimezone()
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    r["title"] or r["channel"],
                    f"{r['frequency_hz'] / 1e6:.5f}",
                    f"{r['duration']:.2f} sn",
                    r["source"],
                    identities,
                ),
            )
        if selected and self.calls.exists(selected[0]):
            self.calls.selection_set(selected)
        self.count.set(f"{len(rows)} kayıt gösteriliyor • En yeni 1000 sonuç • WAV / 16 kHz / mono")

    def play(self):
        selected = self.calls.selection()
        if not selected:
            return
        try:
            winsound.PlaySound(
                str(self.archive.audio_path(selected[0])),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        except (RuntimeError, ValueError) as exc:
            messagebox.showerror("Dinleme", str(exc))

    def poll(self):
        try:
            while True:
                message = self.receiver.messages.get_nowait()
                kind = message["kind"]
                if kind in ("status", "error"):
                    self.status.set(message["text"])
                elif kind == "levels":
                    self.levels.set(
                        "   |   ".join(
                            f"{c['name']}: {c['level']:.1f} dBFS  {'● KAYIT' if c['active'] else 'Bekliyor'}"
                            for c in message["channels"]
                        )
                    )
                    completed = sum(c["completed"] for c in message["channels"])
                    if completed != self.last_count:
                        self.last_count = completed
                        self.refresh_archive()
                elif kind == "stopped":
                    self.start_button.configure(state="normal")
                    self.levels.set("Alım kapalı • Etkin kayıt yok")
                    if message["reason"] != "error":
                        self.status.set("Alım durduruldu • Kayıtlar arşivde")
                    self.refresh_archive()
                try:
                    (self.archive.root / "receiver-status.json").write_text(
                        json.dumps(
                            {"at": datetime.now().isoformat(), **message}, ensure_ascii=False
                        ),
                        "utf-8",
                    )
                except OSError:
                    logging.exception("Cannot write diagnostic status")
        except queue.Empty:
            pass
        if self.closing and not self.receiver.running:
            winsound.PlaySound(None, 0)
            self.root.destroy()
            return
        self.root.after(200, self.poll)

    def close(self):
        self.closing = True
        self.status.set("Alıcı kapatılıyor ve kayıtlar tamamlanıyor…")
        self.receiver.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--listen", action="store_true")
    args = parser.parse_args()
    (args.project / "data").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=args.project / "data/radia.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    root = tk.Tk()
    app = RadiaApp(root, args.project)
    if args.listen:
        root.after(500, app.start)
    root.mainloop()


if __name__ == "__main__":
    main()
