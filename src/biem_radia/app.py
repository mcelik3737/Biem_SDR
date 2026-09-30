from __future__ import annotations

import argparse
import json
import logging
import math
import os
import queue
import tkinter as tk
import wave
import webbrowser
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import sounddevice as sd

from . import playback
from .branding import MODEL, PRODUCT_NAME, WINDOW_TITLE
from .calibration import CalibrationPanel
from .cards import ChannelCard
from .devices import DevicesPanel
from .digital_log import DigitalLogPanel
from .engine import Receiver
from .fmradio import FMRadio
from .inbox import InboxPanel
from .map_panel import MapPanel
from .models import Channel
from .presentation import Presentation
from .protection import read_audio
from .repeater_settings import RepeaterSettingsPanel
from .spectrum import SpectrumPanel, is_admin
from .storage import Archive

ROOT = Path.cwd()


class RadiaApp:
    def __init__(self, root: tk.Tk, project: Path):
        self.root, self.project = root, project
        self.archive = Archive(project / "data", protected=True)
        self.receiver = Receiver(self.archive)
        self.radio = FMRadio()
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
        root.title(WINDOW_TITLE)
        root.geometry("1280x920")
        root.minsize(800, 480)
        root.configure(bg="#f3f5f8")
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#ffffff", foreground="#202b3a")
        style.configure("TFrame", background="#f3f5f8")
        style.configure("TLabel", background="#f3f5f8")
        style.configure("TLabelframe", background="#f3f5f8", bordercolor="#d4dbe5")
        style.configure("TLabelframe.Label", background="#f3f5f8", foreground="#246293")
        style.configure(
            "TEntry", fieldbackground="#ffffff", foreground="#202b3a", insertcolor="#202b3a"
        )
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#202b3a")
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#ffffff")],
            foreground=[("readonly", "#202b3a")],
        )
        style.configure("TButton", padding=(12, 7), background="#e3eaf3")
        style.map("TButton", background=[("active", "#d1e2f5")])
        style.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#202b3a",
            rowheight=31,
        )
        style.configure("Treeview.Heading", background="#e8edf4", foreground="#334155", padding=7)
        style.map("Treeview", background=[("selected", "#cfe4fa")])
        style.configure("TNotebook", background="#f3f5f8", borderwidth=0)
        style.configure(
            "TNotebook.Tab", background="#e8edf4", foreground="#202b3a", padding=(12, 8)
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#cfe4fa")],
            foreground=[("selected", "#174b78")],
        )
        style.configure(
            "Horizontal.TProgressbar", background="#2677b9", troughcolor="#ffffff", borderwidth=0
        )
        style.configure(
            "TSpinbox", fieldbackground="#ffffff", foreground="#202b3a", insertcolor="#202b3a"
        )

        outer = ttk.Frame(root, padding=22)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x")
        assets = Path(__file__).parent / "assets"
        self.logo = tk.PhotoImage(master=root, file=str(assets / "biem-logo.png")).subsample(5, 5)
        self.icon = tk.PhotoImage(master=root, file=str(assets / "biem-icon.png")).subsample(10, 10)
        root.iconphoto(True, self.icon)
        ttk.Label(header, image=self.logo).pack(side="left", padx=(0, 20))
        ttk.Label(
            header, text=f"Radio Integrated Solution  |  {MODEL}", font=("Segoe UI", 16, "bold")
        ).pack(side="left")
        ttk.Label(header, text="CANLI KANALLAR  /  KAYIT ARŞİVİ", foreground="#246293").pack(
            side="right"
        )
        self.status = tk.StringVar(value="Alıcı beklemede • Kayıt başlatılmadı")
        ttk.Label(
            outer,
            textvariable=self.status,
            font=("Segoe UI", 12),
            foreground="#246293",
            padding=(0, 14),
        ).pack(anchor="w")

        self.fm_panel = ttk.Frame(outer, padding=8)
        ttk.Button(header, text="♫ FM RADIO ▾", command=self.toggle_radio).pack(
            side="right", padx=18
        )
        self.fm_frequency = tk.StringVar(value="99.5")
        self.fm_status = tk.StringVar(
            value="88,5–108 MHz • 100 kHz adım • Ana alım açıkken bu alıcı kullanılamaz"
        )
        ttk.Label(self.fm_panel, text="FM RADIO / MHz").pack(side="left", padx=8)
        ttk.Spinbox(
            self.fm_panel,
            from_=88.5,
            to=108,
            increment=0.1,
            textvariable=self.fm_frequency,
            width=8,
        ).pack(side="left")
        ttk.Button(self.fm_panel, text="▶ Dinle", command=self.start_radio).pack(
            side="left", padx=8
        )
        ttk.Button(self.fm_panel, text="■ Kapat", command=self.radio.stop).pack(side="left")
        ttk.Scale(
            self.fm_panel,
            from_=0,
            to=1,
            value=0.7,
            command=lambda v: setattr(self.radio, "volume", float(v)),
        ).pack(side="left", padx=8)
        ttk.Label(self.fm_panel, textvariable=self.fm_status, wraplength=460).pack(
            side="left", padx=8
        )
        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True)
        self.live_tab = ttk.Frame(self.tabs, padding=10)
        self.archive_tab = ttk.Frame(self.tabs, padding=10)
        self.settings_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.live_tab, text="  Canlı Kanallar  ")
        self.tabs.add(self.archive_tab, text="  Kayıt Arşivi  ")
        self.tabs.add(self.settings_tab, text="  Alıcı / Gelişmiş Ayarlar  ")
        self.digital_log = DigitalLogPanel(self.tabs, self.archive)
        self.tabs.add(self.digital_log, text="  Dijital Veri Günlüğü  ")
        self.inbox = InboxPanel(self.tabs, self.archive.root)
        self.tabs.add(self.inbox, text="  Gelen Mesajlar  ")
        self.map_panel = MapPanel(self.tabs, self.archive)
        self.tabs.add(self.map_panel, text="  Harita  ")
        self.repeater_panel = RepeaterSettingsPanel(self.tabs, self.archive.root)
        self.tabs.add(self.repeater_panel, text="  Hytera Ethernet  ")
        live_controls = ttk.Frame(self.live_tab)
        live_controls.pack(fill="x")
        setup = ttk.LabelFrame(
            self.settings_tab, text="ALICI VE GELİŞMİŞ KANAL AYARLARI", padding=12
        )
        setup.pack(fill="x")
        row = ttk.Frame(setup)
        row.pack(fill="x")
        self.source = tk.StringVar(value="USB")
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="1234")
        self.ppm = tk.StringVar(value="0")
        self.usb_gain = tk.StringVar(value="19")
        self.usb_agc = tk.StringVar(value="Manuel")
        self.receive_mode = tk.StringVar(value="Sabit")
        self.scan_dwell = tk.StringVar(value="1.0")
        self.scan_release = tk.StringVar(value="1.0")
        self.receiver_config_path = self.archive.root / "receiver.json"
        self.receiver_fields = {
            "source": self.source,
            "host": self.host,
            "port": self.port,
            "ppm": self.ppm,
            "usb_gain": self.usb_gain,
            "usb_agc": self.usb_agc,
            "receive_mode": self.receive_mode,
            "scan_dwell": self.scan_dwell,
            "scan_release": self.scan_release,
        }
        if self.receiver_config_path.exists():
            try:
                settings = json.loads(self.receiver_config_path.read_text("utf-8"))
                if not isinstance(settings, dict):
                    raise ValueError("Alıcı ayarı nesne olmalı.")
                for key, variable in self.receiver_fields.items():
                    if key in settings:
                        variable.set(str(settings[key]))
            except (ValueError, OSError) as exc:
                messagebox.showerror("Alıcı ayarı", str(exc))
        self._field(row, "Kaynak", self.source, 10, ["USB", "rtl_tcp"])
        self._field(row, "Ethernet SDR adresi", self.host, 17)
        self._field(row, "Port", self.port, 7)
        self._field(row, "PPM düzeltme", self.ppm, 8)
        self._field(row, "USB kazanç / dB", self.usb_gain, 10)
        self.devices = DevicesPanel(self.tabs, self)
        self.tabs.add(self.devices, text="  SDR Cihazları  ")
        self.spectrum = SpectrumPanel(self.tabs, self)
        self.tabs.add(self.spectrum, text="  Spektrum / Yönetici  ")
        self.calibration = CalibrationPanel(self.settings_tab, self)
        self.calibration.pack(fill="x", pady=10)
        about = ttk.Frame(self.tabs, padding=28)
        self.tabs.add(about, text="  BİEM  ")
        ttk.Label(about, image=self.logo).pack(anchor="w", pady=16)
        ttk.Label(about, text="BİEM Teknoloji Elektronik", font=("Segoe UI", 20, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            about,
            text="Telsiz haberleşmesi • Raylı sistemler • DAS / RF kapsama\n\nGSM: +90 532 524 40 37\nOfis: +90 216 807 24 36 – 37\nE-posta: proje@biemelektronik.com\n\nBarbaros Mah. Begonya Sok. Batı Nida Kule No:1\nAtaşehir / İstanbul",
            font=("Segoe UI", 11),
            justify="left",
        ).pack(anchor="w", pady=20)
        ttk.Button(
            about,
            text="biemelektronik.com ↗",
            command=lambda: webbrowser.open("https://biemelektronik.com/"),
        ).pack(anchor="w")
        ttk.Label(about, text=WINDOW_TITLE, foreground="#526174").pack(anchor="w", pady=28)
        gain_row = ttk.Frame(self.live_tab)
        gain_row.pack(fill="x", pady=8)
        self._field(gain_row, "USB donanım kazancı / dB", self.usb_gain, 12)
        self._field(gain_row, "Kazanç kontrolü", self.usb_agc, 14, ["Manuel", "Tuner AGC"])
        ttk.Button(gain_row, text="+10 dB", command=self.boost_gain).pack(
            side="left", padx=8, pady=(16, 0)
        )
        ttk.Button(gain_row, text="Kazancı uygula", command=self.apply_gain).pack(
            side="left", pady=(16, 0)
        )
        self.gain_status = tk.StringVar(value="USB • Alım sırasında değiştirilebilir")
        ttk.Label(gain_row, textvariable=self.gain_status).pack(side="left", padx=10, pady=(16, 0))
        self.start_button = ttk.Button(live_controls, text="▶ Alımı başlat", command=self.start)
        self.start_button.pack(side="left", padx=(20, 6), pady=(16, 0))
        self.stop_button = ttk.Button(live_controls, text="■ Durdur", command=self.receiver.stop)
        self.stop_button.pack(side="left", pady=(16, 0))

        scan_row = ttk.Frame(self.live_tab)
        scan_row.pack(fill="x", pady=(8, 0))
        self._field(scan_row, "Alım biçimi", self.receive_mode, 12, ["Sabit", "Tarama"])
        self._field(scan_row, "Kanalı dinle / sn", self.scan_dwell, 12)
        self._field(scan_row, "Eşik altı bekle / sn", self.scan_release, 14)
        ttk.Label(
            scan_row,
            text="Kayıt: 90 sn / 2 sn ara • TETRA: sessiz taşıyıcı 20 sn • DMR tarama: otomatik CC 0–15",
        ).pack(side="left", padx=12, pady=(16, 0))

        mode_row = ttk.Frame(setup)
        mode_row.pack(fill="x", pady=(8, 0))
        self.mode = tk.StringVar(value="NFM")
        self.system = tk.StringVar(value="Default")
        self.color_code = tk.StringVar()
        self.enabled = tk.BooleanVar(value=True)
        self._field(
            mode_row, "Kanal modu", self.mode, 8, ["NFM", "DMR", "TETRA", "APCO25", "NXDN", "AUTO"]
        )
        self._field(mode_row, "Sistem / müşteri kapsamı", self.system, 22)
        self._field(mode_row, "Color code (boş = tümü)", self.color_code, 18)
        ttk.Button(mode_row, text="ID → İsim eşleştirme", command=self.alias_dialog).pack(
            side="left", padx=10, pady=(16, 0)
        )
        ttk.Checkbutton(mode_row, text="Kanal etkin", variable=self.enabled).pack(
            side="left", pady=(16, 0)
        )

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
            height=2,
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
        initial = next((i for i, c in enumerate(self.channels) if c.enabled), None)
        if initial is not None:
            self.channel_table.selection_set(str(initial))
            self.select_channel()
        self.levels = tk.StringVar(
            value="Sabit: bant içi eşzamanlı alım. Tarama: etkin kanallar sırayla alınır."
        )
        ttk.Label(setup, textvariable=self.levels, foreground="#526174", padding=(0, 8)).pack(
            anchor="w"
        )

        ttk.Button(live_controls, text="Kanalları kaydet", command=self.save_cards).pack(
            side="left", padx=10, pady=(16, 0)
        )
        card_view = ttk.Frame(self.live_tab)
        card_view.pack(fill="both", expand=True, pady=(8, 0))
        card_canvas = tk.Canvas(card_view, bg="#f3f5f8", highlightthickness=0)
        card_scroll = ttk.Scrollbar(card_view, orient="vertical", command=card_canvas.yview)
        card_canvas.configure(yscrollcommand=card_scroll.set)
        card_scroll.pack(side="right", fill="y")
        card_canvas.pack(side="left", fill="both", expand=True)
        self.card_grid = ttk.Frame(card_canvas)
        card_window = card_canvas.create_window((0, 0), window=self.card_grid, anchor="nw")
        self.card_canvas, self.card_window = card_canvas, card_window
        self.card_grid.bind(
            "<Configure>", lambda e: card_canvas.configure(scrollregion=card_canvas.bbox("all"))
        )
        card_canvas.bind(
            "<Configure>", lambda e: card_canvas.itemconfigure(card_window, width=e.width)
        )
        for col in range(3):
            self.card_grid.columnconfigure(col, weight=1, uniform="cards")
        for row in range(2):
            self.card_grid.rowconfigure(row, weight=1)
        self.cards = [ChannelCard(self.card_grid, i) for i in range(max(6, len(self.channels)))]
        self.load_cards()
        archive_box = ttk.LabelFrame(self.archive_tab, text="KONUŞMA ARŞİVİ", padding=12)
        archive_box.pack(fill="both", expand=True, pady=(16, 0))
        search = ttk.Frame(archive_box)
        search.pack(fill="x", pady=(0, 10))
        self.search_text = tk.StringVar()
        self.search_day = tk.StringVar()
        self.search_slot = tk.StringVar(value="Tümü")
        self._field(search, "Kanal adı / başlık / ID", self.search_text, 32)
        self._field(search, "Tarih / YYYY-MM-DD (yerel)", self.search_day, 24)
        self._field(search, "Slot", self.search_slot, 6, ["Tümü", "1", "2", "3", "4"])
        ttk.Button(search, text="Ara / yenile", command=self.refresh_archive).pack(
            side="left", padx=10, pady=(16, 0)
        )
        ttk.Button(search, text="▶ Seçili kaydı dinle", command=self.play).pack(
            side="left", pady=(16, 0)
        )
        ttk.Button(search, text="Sesi kes", command=playback.stop).pack(
            side="left", padx=8, pady=(16, 0)
        )
        columns = ("time", "channel", "frequency", "duration", "source", "identity", "slot", "code")
        self.calls = ttk.Treeview(archive_box, columns=columns, show="headings", height=6)
        for key, label, width in zip(
            columns,
            [
                "Tarih ve saat (yerel)",
                "Kanal / başlık",
                "MHz",
                "Kayıt süresi",
                "Kaynak",
                "ID / Grup",
                "Slot",
                "CC / NAC / RAN",
            ],
            [155, 175, 100, 85, 130, 120, 150, 110],
            strict=True,
        ):
            self.calls.heading(key, text=label)
            self.calls.column(key, width=width, minwidth=width)
        scrollbar = ttk.Scrollbar(archive_box, orient="vertical", command=self.calls.yview)
        horizontal = ttk.Scrollbar(archive_box, orient="horizontal", command=self.calls.xview)
        self.calls.configure(yscrollcommand=scrollbar.set, xscrollcommand=horizontal.set)
        horizontal.pack(side="bottom", fill="x")
        scrollbar.pack(side="right", fill="y")
        self.calls.pack(fill="both", expand=True)
        self.calls.bind("<Double-1>", lambda event: self.play())
        footer = ttk.Frame(self.archive_tab)
        footer.pack(fill="x", pady=(12, 0), side="bottom", before=archive_box)
        self.count = tk.StringVar(value="")
        ttk.Label(footer, textvariable=self.count, foreground="#526174").pack(side="left")
        ttk.Button(
            footer, text="Kayıt klasörünü aç", command=lambda: os.startfile(str(self.archive.root))
        ).pack(side="right")
        ttk.Label(
            footer, text="Analog FM'de ID / grup / slot bilgisi yoktur.  ", foreground="#526174"
        ).pack(side="right")
        self.refresh_archive()
        self.presentation = Presentation(self, outer, header)
        root.after(200, self.poll)

    def toggle_radio(self):
        if self.fm_panel.winfo_manager():
            self.fm_panel.pack_forget()
        else:
            self.fm_panel.pack(fill="x", before=self.presentation.body)

    def start_radio(self):
        if self.spectrum.worker.running:
            messagebox.showerror("FM RADIO", "Önce spektrum ölçümünü durdurun.")
            return
        try:
            if self.receiver.running:
                raise ValueError(
                    "Ana telsiz alımı sürüyor. FM RADIO aynı USB alıcıyı kullanamaz; ana alımı durdurun veya ayrı alıcı kullanın."
                )
            frequency = round(float(self.fm_frequency.get().replace(",", ".")) * 10) * 100000
            self.fm_frequency.set(f"{frequency / 1e6:.1f}")
            self.radio.start(
                self.project / "vendor/rtl-sdr/package/x64/rtlsdr.dll",
                frequency,
                int(self.ppm.get()),
                float(self.usb_gain.get()),
                index=self.devices.selected_index(),
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("FM RADIO", str(exc))

    def load_cards(self):
        if not hasattr(self, "cards"):
            return
        for i, card in enumerate(self.cards):
            card.load(self.channels[i] if i < len(self.channels) else None)

    def save_cards(self):
        if self.receiver.running:
            messagebox.showinfo("Alım açık", "Kanal değişikliği için önce Durdur düğmesine basın.")
            return False
        try:
            channels = [c for card in self.cards if (c := card.value()) is not None]
            if len({c.name.casefold() for c in channels}) != len(channels):
                raise ValueError("Kanal adları farklı olmalı.")
            self.channels = channels
            self.config_path.write_text(
                json.dumps([asdict(c) for c in channels], ensure_ascii=False, indent=2), "utf-8"
            )
            self.refresh_channels()
            # Keep empty card positions while editing, and bind telemetry to saved values.
            for card in self.cards:
                card.channel = card.value()
            return True
        except (ValueError, OSError) as exc:
            messagebox.showerror("Kanal ayarları", str(exc))
            return False

    def _field(self, parent, label, variable, width, choices=None):
        frame = ttk.Frame(parent)
        frame.pack(side="left", padx=(0, 8))
        ttk.Label(frame, text=label, foreground="#526174").pack(anchor="w", pady=(0, 4))
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
                    f"{c.name} [{c.mode}]" + (" • kapalı" if not c.enabled else ""),
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
            self.enabled.set(c.enabled)
            for variable, value in [
                (self.name, c.name),
                (self.freq, f"{c.frequency_hz / 1e6:.5f}"),
                (self.spacing, c.spacing_hz),
                (self.bandwidth, c.bandwidth_hz),
                (self.squelch, c.squelch_db),
                (self.mode, c.mode),
                (self.system, c.system),
                (self.color_code, "" if c.color_code is None else c.color_code),
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
                mode=self.mode.get(),
                system=self.system.get().strip(),
                color_code=int(self.color_code.get())
                if self.mode.get() != "AUTO" and self.color_code.get().strip()
                else None,
                enabled=self.enabled.get(),
                tone_mode=next(
                    (c.tone_mode for c in self.channels if c.name == self.name.get().strip()), "CSQ"
                ),
                tone_value=next(
                    (c.tone_value for c in self.channels if c.name == self.name.get().strip()),
                    "67.0",
                ),
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
        self.load_cards()

    def boost_gain(self):
        try:
            self.usb_gain.set(f"{min(50, float(self.usb_gain.get()) + 10):g}")
            self.usb_agc.set("Manuel")
            self.apply_gain()
        except ValueError:
            messagebox.showerror("USB kazancı", "Sayısal bir kazanç girin.")

    def apply_gain(self):
        try:
            gain = float(self.usb_gain.get().replace(",", "."))
            if not math.isfinite(gain) or not -10 <= gain <= 50:
                raise ValueError("Kazanç −10…50 dB aralığında olmalı.")
            if self.source.get() != "USB" or self.radio.running:
                raise ValueError("Bu kontrol USB ana alıcısı içindir. FM RADIO kapalı olmalı.")
            self.receiver.usb_settings = (gain, self.usb_agc.get() == "Tuner AGC")
            self.receiver_config_path.write_text(
                json.dumps({key: var.get() for key, var in self.receiver_fields.items()}, indent=2),
                "utf-8",
            )
            self.gain_status.set(
                "Kazanç ayarı kaydedildi"
                if self.receiver.running
                else "Kaydedildi • Alım başladığında uygulanacak"
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("USB kazancı", str(exc))

    def start(self):
        try:
            if self.spectrum.worker.running:
                raise ValueError("Önce spektrum ölçümünü durdurun.")
            if self.radio.running:
                raise ValueError(
                    "Önce FM RADIO dinlemeyi kapatın; USB alıcı radyo tarafından kullanılıyor."
                )
            if hasattr(self, "cards"):
                if not self.save_cards():
                    return
            ppm = int(self.ppm.get())
            port = int(self.port.get())
            usb_gain = float(self.usb_gain.get())
            if not math.isfinite(usb_gain) or not -10 <= usb_gain <= 50:
                raise ValueError("USB kazancı −10…50 dB aralığında olmalı.")
            if not -200 <= ppm <= 200 or not 1 <= port <= 65535:
                raise ValueError("PPM −200…200, port 1…65535 aralığında olmalı.")
            self.receiver_config_path.write_text(
                json.dumps({key: var.get() for key, var in self.receiver_fields.items()}, indent=2),
                "utf-8",
            )
            self.receiver.start(
                [c for c in self.channels if c.enabled],
                self.project / "vendor/rtl-sdr/package/x64/rtlsdr.dll",
                self.source.get(),
                self.host.get(),
                port,
                ppm,
                usb_gain,
                scan=self.receive_mode.get() == "Tarama",
                scan_dwell=float(self.scan_dwell.get()),
                scan_release=float(self.scan_release.get()),
                usb_agc=self.usb_agc.get() == "Tuner AGC",
                usb_index=self.devices.selected_index() if self.source.get() == "USB" else 0,
            )
            self.start_button.configure(state="disabled")
            for card in self.cards:
                card.set_editable(False)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Alıcı", str(exc))

    def refresh_archive(self):
        try:
            rows = self.archive.search(
                self.search_text.get(),
                self.search_day.get(),
                slot=None if self.search_slot.get() == "Tümü" else int(self.search_slot.get()),
            )
        except ValueError:
            messagebox.showerror("Tarih", "Tarihi YYYY-MM-DD biçiminde yazın veya boş bırakın.")
            return
        selected = self.calls.selection()
        self.calls.delete(*self.calls.get_children())
        for r in rows:
            slot_label = (
                str(r["protocol_slot"])
                if r["protocol_slot"] is not None
                else str(r["slot"])
                if r["slot"] is not None
                else f"{r['decoder_slot']} (çözücü)"
                if r["decoder_slot"] is not None
                else "Doğrulanmadı"
                if r["source"].startswith(("DMR/", "TETRA/", "P25/", "APCO25/", "NXDN/"))
                else "—"
            )
            identities = " / ".join(
                str(r[k]) if r[k] is not None else "—" for k in ("radio_id", "group_id")
            )
            code = r["color_code"]
            code_label = (
                "—"
                if code is None
                else f"NAC {code:03X}"
                if r["source"].startswith(("APCO25/", "P25/"))
                else f"RAN {code}"
                if r["source"].startswith("NXDN/")
                else f"CC {code}"
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
                    slot_label,
                    code_label,
                ),
            )
        if selected and self.calls.exists(selected[0]):
            self.calls.selection_set(selected)
        self.count.set(
            f"{len(rows)} kayıt • Slot (çözücü): fiziksel slot doğrulanmadı; slot filtresine dahil değil"
        )

    def alias_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("DMR • Sistem kapsamında ID → İsim")
        dialog.geometry("720x400")
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        fields = ttk.Frame(frame)
        fields.pack(fill="x")
        system = tk.StringVar(value=self.system.get())
        kind = tk.StringVar(value="radio")
        identity = tk.StringVar()
        name = tk.StringVar()
        for label, var, width, choices in [
            ("Sistem", system, 16, None),
            ("Tür", kind, 8, ["radio", "group"]),
            ("ID", identity, 10, None),
            ("İsim", name, 20, None),
        ]:
            self._field(fields, label, var, width, choices)
        table = ttk.Treeview(frame, columns=("kind", "id", "name"), show="headings", height=7)
        for key, label in [("kind", "Tür"), ("id", "ID"), ("name", "İsim")]:
            table.heading(key, text=label)

        def refresh():
            table.delete(*table.get_children())
            for row in self.archive.aliases(system.get()):
                table.insert("", "end", values=(row["kind"], row["identity"], row["name"]))

        def save():
            try:
                self.archive.set_alias(system.get(), kind.get(), identity.get(), name.get())
                refresh()
                self.refresh_archive()
            except ValueError as exc:
                messagebox.showerror("ID eşleştirme", str(exc), parent=dialog)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=12)
        ttk.Button(buttons, text="Kaydet", command=save).pack(side="left")
        ttk.Button(buttons, text="Sistemi listele", command=refresh).pack(side="left", padx=8)
        table.pack(fill="both", expand=True)
        refresh()

    def play(self):
        if not is_admin():
            messagebox.showerror(
                "Yetki gerekli",
                f"Kayıt dinlemek için {PRODUCT_NAME} uygulamasını Windows yönetici yetkisiyle açın.",
            )
            return
        selected = self.calls.selection()
        if not selected:
            return
        self.receiver.monitor.stop()
        try:
            path = self.archive.audio_path(selected[0])
            with self.archive.connect() as db:
                call = db.execute("SELECT source FROM calls WHERE id=?", (selected[0],)).fetchone()
            playback.play(read_audio(path), boost=bool(call and call["source"] == "DMR/DSD-FME"))
        except (RuntimeError, ValueError, OSError, wave.Error, sd.PortAudioError) as exc:
            messagebox.showerror("Dinleme", str(exc))

    def poll(self):
        self.map_panel.poll()
        self.digital_log.poll()
        self.inbox.poll()
        try:
            while True:
                message = self.receiver.messages.get_nowait()
                kind = message["kind"]
                if hasattr(self, "presentation"):
                    self.presentation.receiver_event(message)
                if kind in ("status", "error"):
                    self.status.set(message["text"])
                elif kind == "tuning":
                    for card in self.cards:
                        card.telemetry(None)
                        if card.channel and card.channel.name in message["names"]:
                            card.state.set("◌ Alıcı ayarlanıyor…")
                elif kind == "gain":
                    self.gain_status.set(message["text"])
                elif kind == "levels":
                    by_name = {c["name"]: c for c in message["channels"]}
                    for card in self.cards:
                        card.telemetry(by_name.get(card.channel.name) if card.channel else None)
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
                    for card in self.cards:
                        card.set_editable(True)
                        card.telemetry(None)
                        if card.channel:
                            card.state.set("○ Alım kapalı")
                    self.start_button.configure(state="normal")
                    self.levels.set("Alım kapalı • Etkin kayıt yok")
                    if message["reason"] != "error":
                        self.status.set("Alım durduruldu • Kayıtlar arşivde")
                    self.refresh_archive()
                elif kind == "archive_changed":
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
        try:
            while True:
                self.fm_status.set(self.radio.messages.get_nowait())
        except queue.Empty:
            pass
        self.spectrum.poll()
        self.devices.poll()
        if (
            self.closing
            and not self.receiver.running
            and not self.radio.running
            and not self.spectrum.worker.running
        ):
            playback.stop()
            self.root.destroy()
            return
        self.root.after(200, self.poll)

    def close(self):
        self.closing = True
        self.radio.stop()
        self.spectrum.worker.stop()
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
    root.after(100, app.devices.refresh)
    if args.listen:
        root.after(500, app.start)
    root.mainloop()


if __name__ == "__main__":
    main()
