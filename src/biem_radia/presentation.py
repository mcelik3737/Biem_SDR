"""Touch console over the existing receiver controls and archive commands."""

import json
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from . import playback
from .branding import MODEL
from .console_theme import DARK, LIGHT, channel_status, grid_shape


class ChannelPresentation:
    def __init__(self, owner, card):
        self.owner, self.card = owner, card
        self.original = [(w, w.pack_info()) for w in card.frame.winfo_children()]
        for widget, _ in self.original:
            widget.pack_forget()
        self.expanded = False
        self.summary = tk.Frame(card.frame, bd=0)
        self.summary.pack(fill="both", expand=True)
        self.head = tk.Frame(self.summary)
        self.head.pack(fill="x", pady=(0, 4))
        self.name = tk.Label(
            self.head, textvariable=card.name, anchor="w", font=("Segoe UI", 15, "bold")
        )
        self.name.pack(side="left", fill="x", expand=True)
        self.mode = tk.Label(self.head, font=("Segoe UI", 9, "bold"), padx=6, pady=3)
        self.mode.pack(side="right")
        self.frequency = tk.Label(self.summary, anchor="w", font=("Consolas", 10))
        self.frequency.pack(fill="x")
        self.status = tk.Label(self.summary, anchor="w", font=("Segoe UI", 11, "bold"))
        self.status.pack(fill="x", pady=(6, 3))
        self.more = tk.Frame(self.summary)
        self.more.pack(fill="x", pady=3)
        self.peak = tk.Label(
            self.more, textvariable=card.peak, anchor="w", justify="left", font=("Consolas", 10)
        )
        self.peak.pack(fill="x")
        self.detail = tk.Label(
            self.more, textvariable=card.details, anchor="w", justify="left", font=("Segoe UI", 10)
        )
        self.detail.pack(fill="x", pady=(5, 0))
        # Original RF text remains distinct from decoded audio activity.
        self.state = tk.Label(self.more, textvariable=card.state, anchor="w", font=("Segoe UI", 9))
        # Kept for telemetry bindings, but status is already shown above.
        self.meter = tk.Canvas(self.summary, height=38, highlightthickness=0)
        self.meter.pack(fill="x", pady=(3, 4), before=self.more)
        self.actions = tk.Frame(self.summary)
        self.actions.pack(side="bottom", fill="x", pady=(4, 0), before=self.head)
        self.actions.columnconfigure((0, 1), weight=1)
        self.speaker = tk.Button(
            self.actions,
            text="▶ Dinle",
            command=self.listen,
            relief="flat",
            bd=0,
            pady=9,
            font=("Segoe UI", 10),
        )
        self.speaker.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.message = tk.Button(
            self.actions,
            text="✉ 0",
            command=self.messages,
            relief="flat",
            bd=0,
            pady=9,
            font=("Segoe UI", 10),
        )
        self.message.grid(row=0, column=1, sticky="ew", padx=(0, 4))
        self.button = tk.Button(
            self.actions,
            text="⚙",
            command=self.toggle,
            relief="flat",
            bd=0,
            width=3,
            pady=9,
            font=("Segoe UI", 11),
        )
        self.button.grid(row=0, column=2, sticky="ew")
        self.save_button = ttk.Button(
            card.frame, text="✓ Kanal ayarlarını kaydet", command=self.save
        )
        self.compact = False
        self.status_key = "stopped"
        self.meter.bind("<Configure>", lambda e: self.update())

    def save(self):
        if self.owner.app.save_cards():
            self.toggle()
            self.owner.arrange()

    def toggle(self):
        self.expanded = not self.expanded
        for widget, options in self.original:
            if self.expanded:
                widget.pack(**options)
            else:
                widget.pack_forget()
        if self.expanded:
            self.save_button.pack(fill="x", pady=8)
        else:
            self.save_button.pack_forget()
        self.button.configure(text="×" if self.expanded else "⚙")
        self.owner.arrange()

    def listen(self):
        app = self.owner.app
        name = self.card.channel.name if self.card.channel else self.card.name.get()
        monitor = app.receiver.monitor
        if monitor.selected == name:
            monitor.stop()
        elif app.receiver.running and self.card.enabled.get():
            playback.stop()
            try:
                monitor.select(name)
            except RuntimeError as exc:
                messagebox.showerror("Canlı dinleme", str(exc), parent=app.root)
        else:
            app.status.set("Canlı dinleme için önce alımı başlatın.")
        self.update()

    def messages(self):
        app = self.owner.app
        app.inbox.query.set(self.card.name.get())
        app.inbox.day.set("")
        app.inbox.refresh()
        app.tabs.select(app.inbox)

    def set_compact(self, value):
        if value == self.compact:
            return
        self.compact = value
        if value:
            self.more.pack_forget()
        else:
            self.more.pack(fill="x", pady=3)
        self.name.configure(font=("Segoe UI", 11 if value else 15, "bold"))
        self.status.configure(font=("Segoe UI", 9 if value else 11, "bold"))
        self.frequency.configure(font=("Consolas", 9 if value else 10))
        self.speaker.configure(text="▶" if value else "▶ Dinle")

    def update(self):
        app, c, t = self.owner.app, self.card, self.owner.colors
        state = c.latest_state
        try:
            threshold = float(c.threshold.get())
        except ValueError:
            threshold = -45
        connected = self.owner.connected
        if (
            not app.receiver.running
            and app.source.get() == "USB"
            and app.devices.last_refresh > self.owner.connection_time
        ):
            connected = getattr(app.devices, "detected", connected)
        audio = app.receiver.monitor.state(c.channel.name if c.channel else c.name.get())
        current = {**state, **audio} if state else None
        self.status_key, text, tone = channel_status(
            connected=connected,
            running=app.receiver.running,
            enabled=c.enabled.get(),
            state=current,
            threshold=threshold,
        )
        background = t["off"] if connected is False else t["surface"]
        style_name = f"Card{c.index}.TLabelframe"
        ttk.Style(app.root).configure(
            style_name, background=background, bordercolor=t["line"], relief="solid", borderwidth=1
        )
        c.frame.configure(style=style_name, padding=8 if self.compact else 16, text="")
        for frame in (self.summary, self.head, self.more, self.actions):
            frame.configure(bg=background)
        for label in (
            self.name,
            self.mode,
            self.frequency,
            self.status,
            self.peak,
            self.detail,
            self.state,
        ):
            label.configure(bg=background, fg=t["ink"])
        self.mode.configure(text=(state or {}).get("detected_mode") or c.mode.get(), fg=t["orange"])
        self.frequency.configure(
            text=f"CH {c.index + 1:02d}  ·  {c.freq.get() or '—'} MHz", fg=t["muted"]
        )
        self.status.configure(text="● " + text, fg=t[tone])
        self.peak.configure(fg=c.peak_color if c.peak_color != "#5c6e83" else t["muted"])
        self.detail.configure(fg=t["muted"], wraplength=max(150, c.frame.winfo_width() - 35))
        self.state.configure(fg=t["muted"])
        selected = app.receiver.monitor.selected == c.name.get()
        count = app.inbox.unread.get(c.name.get(), 0)
        for button in (self.speaker, self.message, self.button):
            button.configure(
                bg=t["raised"],
                fg=t["ink"],
                activebackground=t["selected"],
                activeforeground=t["ink"],
            )
        self.speaker.configure(
            text=("■" if selected else "▶")
            if self.compact
            else ("■ Sustur" if selected else "▶ Dinle"),
            bg=t["selected"] if selected else t["raised"],
        )
        self.message.configure(text=f"✉ {count}", fg=t["orange"] if count else t["muted"])
        self.meter.configure(bg=background)
        self.meter.delete("all")
        width = max(1, self.meter.winfo_width())
        for y, title, level, fraction, color in (
            (
                8,
                "RF",
                (state or {}).get("level", -120),
                max(0, min(1, ((state or {}).get("level", -120) + 100) / 100)),
                t[tone],
            ),
            (
                27,
                "SES",
                audio["audio_dbfs"],
                max(0, min(1, (audio["audio_dbfs"] + 65) / 65)),
                t["green"],
            ),
        ):
            self.meter.create_text(
                0, y, anchor="w", text=title, fill=t["muted"], font=("Segoe UI", 8, "bold")
            )
            end = max(42, width - 76)
            self.meter.create_rectangle(30, y - 3, end, y + 3, fill=t["line"], outline="")
            if fraction and app.devices.last_refresh > self.owner.connection_time:
                self.meter.create_rectangle(
                    30, y - 3, 30 + (end - 30) * fraction, y + 3, fill=color, outline=""
                )
            self.meter.create_text(
                width,
                y,
                anchor="e",
                text=f"{level:.0f} dBFS" if level > -120 else "—",
                fill=t["muted"],
                font=("Consolas", 8),
            )


class Presentation:
    def __init__(self, app, outer, header):
        self.app = app
        self.preference = app.archive.root / "console-ui.json"
        try:
            saved = json.loads(self.preference.read_text("utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.dark = bool(saved.get("dark", False)) if isinstance(saved, dict) else False
        self.colors = DARK if self.dark else LIGHT
        self.connected = None
        self.connection_time = 0.0
        self.after_id = None
        self.show_all = tk.BooleanVar(master=app.root, value=False)
        self.last_layout = None
        self.header = header
        self.nav = {}
        self.cards = []
        self.footer_labels = []
        self.theme()
        outer.configure(padding=0)
        header.configure(style="Paper.TFrame", padding=(14, 8))
        for child in header.winfo_children():
            child.pack_forget()
        with Image.open(Path(__file__).parent / "assets/biem-logo.png") as image:
            image.thumbnail((126, 40), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(image, master=app.root)
        # The original logo stays on a light plaque in both themes.
        self.logo_label = tk.Label(header, image=self.logo, bg="white", padx=5, pady=3)
        self.logo_label.pack(side="left", padx=(0, 12))
        self.brand = ttk.Label(header, text=MODEL, style="Brand.TLabel")
        self.brand.pack(side="left")
        self.theme_button = ttk.Button(header, text="◐ Koyu", command=self.toggle_theme, width=8)
        self.theme_button.pack(side="right", padx=(6, 0))
        self.settings_button = ttk.Button(header, text="⚙ Ayarlar", command=self.settings, width=10)
        self.settings_button.pack(side="right", padx=6)
        self.stop = ttk.Button(header, text="■ Durdur", command=app.receiver.stop, width=10)
        self.stop.pack(side="right", padx=6)
        self.start = ttk.Button(
            header, text="▶ Başlat", command=app.start, style="Primary.TButton", width=10
        )
        self.start.pack(side="right", padx=6)
        for child in outer.winfo_children():
            if isinstance(child, ttk.Label):
                child.pack_forget()
                self.footer_labels.append(child)
                child.configure(style="Paper.TLabel", padding=(14, 6), font=("Segoe UI", 9))
                child.pack(side="bottom", fill="x")
        self.body = ttk.Frame(outer)
        self.body.pack(fill="both", expand=True)
        self.rail = tk.Frame(self.body, width=188)
        self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)
        self.rail_title = tk.Label(
            self.rail, text="OPERASYON", anchor="w", font=("Segoe UI", 9, "bold"), padx=14, pady=18
        )
        self.rail_title.pack(fill="x")
        self.content = ttk.Frame(self.body, padding=8)
        self.content.pack(side="left", fill="both", expand=True)
        app.tabs.pack_forget()
        app.tabs.configure(style="Sidebar.TNotebook")
        app.tabs.pack(in_=self.content, fill="both", expand=True)
        app.tabs.lift()
        names = [
            ("Canlı Kanallar", "◉", "Canlı izleme"),
            ("Kayıt Arşivi", "▤", "Kayıt arşivi"),
            ("Gelen Mesajlar", "✉", "Gelen mesajlar"),
            ("Harita", "⌖", "Harita"),
            ("Dijital Veri Günlüğü", "≡", "Veri günlüğü"),
            ("Spektrum / Yönetici", "∿", "Spektrum"),
            ("Alıcı / Gelişmiş Ayarlar", "⚙", "Alıcı ayarları"),
            ("SDR Cihazları", "▣", "SDR cihazları"),
            ("Hytera Ethernet", "⇄", "Hytera Ethernet"),
            ("FM Radio", "♫", "FM radyo"),
            ("BİEM", "ⓘ", "BİEM"),
        ]
        pages = {app.tabs.tab(tab, "text").strip(): tab for tab in app.tabs.tabs()}
        self.nav_items = []
        for label, icon, caption in names:
            tab = pages.get(label)
            if tab is None and label != "FM Radio":
                continue
            button = tk.Button(
                self.rail,
                text=f"{icon}   {caption}",
                command=app.toggle_radio if tab is None else lambda tab=tab: app.tabs.select(tab),
                relief="flat",
                bd=0,
                anchor="w",
                padx=12,
                pady=11,
                font=("Segoe UI", 10),
            )
            button.pack(fill="x", padx=6, pady=2)
            self.nav_items.append((button, icon, caption, tab))
            if tab is not None:
                self.nav[tab] = button
        self.more_nav = tk.Menubutton(
            self.rail, text="☰", relief="flat", bd=0, font=("Segoe UI", 14), pady=10
        )
        self.nav_menu = tk.Menu(self.more_nav, tearoff=False, font=("Segoe UI", 13))
        self.more_nav.configure(menu=self.nav_menu)
        for button, _, caption, _ in self.nav_items:
            self.nav_menu.add_command(label=caption, command=button.invoke)
        # Keep existing controls intact, but remove technical rows from the daily monitoring view.
        for child in app.live_tab.winfo_children():
            if child is not app.card_canvas.master:
                child.pack_forget()
        self.toolbar = ttk.Frame(app.live_tab)
        self.toolbar.pack(fill="x", before=app.card_canvas.master, pady=(0, 6))
        self.title = ttk.Label(self.toolbar, text="Canlı izleme", style="PageTitle.TLabel")
        self.title.pack(side="left")
        self.edit_button = ttk.Button(
            self.toolbar, text="⚙ Kanal düzeni", command=self.edit_channels
        )
        self.edit_button.pack(side="right")
        for label, direction in (("▼", 1), ("▲", -1)):
            ttk.Button(
                self.toolbar,
                text=label,
                width=2,
                command=lambda direction=direction: app.card_canvas.yview_scroll(
                    direction, "pages"
                ),
            ).pack(side="right", padx=3)
        self.source_note = ttk.Label(self.toolbar, text="", style="Muted.TLabel")
        self.source_note.pack(side="left", padx=14)
        self.cards = [ChannelPresentation(self, c) for c in app.cards]
        app.card_canvas.bind("<Configure>", self.arrange, add="+")
        app.root.bind("<Configure>", self.resize, add="+")
        app.root.bind("<MouseWheel>", self.scroll_cards, add="+")
        self.archive_layout()
        app.tabs.bind("<<NotebookTabChanged>>", self.highlight, add="+")
        self.theme()
        self.highlight()
        self.arrange()
        self.update()

    def edit_channels(self):
        self.show_all.set(not self.show_all.get())
        self.edit_button.configure(
            text="✓ İzlemeye dön" if self.show_all.get() else "⚙ Kanal düzeni"
        )
        self.arrange()

    def settings(self):
        app = self.app
        existing = getattr(self, "settings_window", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        win = tk.Toplevel(app.root)
        self.settings_window = win
        win.title("BİEM · Hızlı alıcı ayarları")
        win.geometry("580x460")
        win.transient(app.root)
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Alıcı ayarları", style="PageTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14)
        )
        for n, (label, var, values) in enumerate(
            [
                ("USB kazancı / dB", app.usb_gain, None),
                ("Kazanç kontrolü", app.usb_agc, ["Manuel", "Tuner AGC"]),
                ("PPM düzeltmesi", app.ppm, None),
                ("Alım biçimi", app.receive_mode, ["Sabit", "Tarama"]),
                ("Kanal dinleme / saniye", app.scan_dwell, None),
                ("Eşik altı bekleme / saniye", app.scan_release, None),
            ],
            1,
        ):
            ttk.Label(frame, text=label).grid(row=n, column=0, sticky="w", pady=6)
            field = (
                ttk.Combobox(frame, textvariable=var, values=values, state="readonly", width=18)
                if values
                else ttk.Entry(frame, textvariable=var, width=20)
            )
            field.grid(row=n, column=1, sticky="ew", padx=12, pady=6)
            if app.receiver.running and n >= 3:
                field.configure(state="disabled")
        ttk.Button(frame, text="Kazancı uygula", command=app.apply_gain).grid(
            row=7, column=0, sticky="ew", pady=16
        )
        ttk.Button(
            frame,
            text="Gelişmiş ayarlar",
            command=lambda: (app.tabs.select(app.settings_tab), win.destroy()),
        ).grid(row=7, column=1, sticky="ew", padx=12)
        ttk.Button(frame, text="Kapat", command=win.destroy).grid(
            row=8, column=1, sticky="ew", padx=12
        )
        ttk.Label(
            frame,
            text="PPM ve tarama ayarları sonraki alım başlangıcında uygulanır.",
            style="Muted.TLabel",
            wraplength=500,
        ).grid(row=9, column=0, columnspan=2, sticky="w", pady=8)
        win.configure(bg=self.colors["bg"])

    def archive_layout(self):
        app = self.app
        box = app.calls.master
        box.configure(text="Konuşma kayıtları")
        search = box.winfo_children()[0]
        for widget in search.winfo_children():
            widget.pack_forget()
        for n, widget in enumerate(search.winfo_children()):
            widget.grid(
                row=0 if n < 3 else 1, column=n if n < 3 else n - 3, sticky="w", padx=(0, 8), pady=6
            )
        app.calls.configure(
            displaycolumns=("time", "channel", "identity", "slot", "code", "duration")
        )
        for key, width in (
            ("time", 155),
            ("channel", 160),
            ("identity", 120),
            ("slot", 120),
            ("code", 110),
            ("duration", 85),
        ):
            app.calls.column(key, width=width, minwidth=75)
        self.archive_detail = ttk.Label(
            app.archive_tab,
            text="Bir kayıt seçin. Dinleme için yönetici oturumu gerekir.",
            style="Muted.TLabel",
            wraplength=1100,
            padding=(0, 8),
        )
        self.archive_detail.pack(side="bottom", fill="x")
        app.calls.bind("<<TreeviewSelect>>", self.archive_selection, add="+")
        app.calls.bind("<Return>", lambda event: app.play())

    def archive_selection(self, event=None):
        chosen = self.app.calls.selection()
        if chosen:
            values = self.app.calls.item(chosen[0], "values")
            self.archive_detail.configure(
                text=f"{values[1]}  •  {values[0]}  •  {values[2]} MHz  •  {values[4]}  •  ID / Grup {values[5]}  •  Slot {values[6]}  •  {values[7]}"
            )

    def receiver_event(self, message):
        if message["kind"] == "connection":
            self.connected = message["connected"]
            self.connection_time = time.monotonic()
        elif message["kind"] == "levels":
            self.connected = True
            self.connection_time = time.monotonic()
        elif message["kind"] == "stopped":
            self.app.receiver.monitor.stop()

    def toggle_theme(self):
        self.dark = not self.dark
        self.colors = DARK if self.dark else LIGHT
        try:
            self.preference.write_text(json.dumps({"dark": self.dark}), "utf-8")
        except OSError as exc:
            self.app.status.set(f"Görünüm tercihi kaydedilemedi: {exc}")
        self.theme()

    def theme(self):
        t = self.colors
        app = self.app
        style = ttk.Style(app.root)
        app.root.configure(bg=t["bg"])
        style.configure(".", background=t["bg"], foreground=t["ink"], font=("Segoe UI", 10))
        for name in (
            "TFrame",
            "TLabel",
            "TLabelframe",
            "TLabelframe.Label",
            "TCheckbutton",
            "TRadiobutton",
            "TNotebook",
        ):
            style.configure(name, background=t["bg"], foreground=t["ink"])
        style.configure("Paper.TFrame", background=t["surface"])
        style.configure("Paper.TLabel", background=t["surface"], foreground=t["muted"])
        style.configure(
            "Brand.TLabel",
            background=t["surface"],
            foreground=t["ink"],
            font=("Segoe UI", 14, "bold"),
        )
        style.configure("Muted.TLabel", foreground=t["muted"])
        style.configure("PageTitle.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure(
            "TButton",
            padding=(12, 10),
            background=t["surface"],
            foreground=t["ink"],
            bordercolor=t["line"],
            relief="flat",
            focusthickness=1,
            focuscolor=t["orange"],
        )
        style.map(
            "TButton",
            background=[("active", t["selected"]), ("disabled", t["off"])],
            foreground=[("disabled", t["muted"]), ("!disabled", t["ink"])],
        )
        style.configure("Primary.TButton", background=t["accent"], foreground="#ffffff")
        style.map(
            "Primary.TButton",
            background=[
                ("disabled", t["off"]),
                ("active", t["orange"]),
                ("!disabled", t["accent"]),
            ],
            foreground=[("disabled", t["muted"]), ("!disabled", "#ffffff")],
        )
        for name in ("TEntry", "TCombobox", "TSpinbox"):
            style.configure(
                name,
                fieldbackground=t["surface"],
                foreground=t["ink"],
                insertcolor=t["ink"],
                bordercolor=t["line"],
                padding=7,
            )
            style.map(
                name,
                fieldbackground=[("disabled", t["off"]), ("readonly", t["surface"])],
                foreground=[("disabled", t["muted"]), ("readonly", t["ink"])],
            )
        style.configure(
            "Treeview",
            rowheight=40,
            background=t["surface"],
            fieldbackground=t["surface"],
            foreground=t["ink"],
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=t["raised"],
            foreground=t["muted"],
            padding=10,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", t["selected"])],
            foreground=[("selected", t["ink"])],
        )
        style.configure("Vertical.TScrollbar", width=22, background=t["line"], troughcolor=t["bg"])
        style.configure(
            "Horizontal.TScrollbar", width=22, background=t["line"], troughcolor=t["bg"]
        )
        style.configure(
            "Sidebar.TNotebook",
            background=t["bg"],
            bordercolor=t["bg"],
            lightcolor=t["bg"],
            darkcolor=t["bg"],
            borderwidth=0,
        )
        style.layout("Sidebar.TNotebook.Tab", [])
        if hasattr(self, "rail"):
            self.rail.configure(bg=t["nav"])
            self.rail_title.configure(bg=t["nav"], fg=t["muted"])
            self.theme_button.configure(text="◐ Açık" if self.dark else "◐ Koyu")
            app.card_canvas.configure(bg=t["bg"])
            for text in (app.inbox.detail, app.digital_log.text):
                text.configure(
                    bg=t["surface"],
                    fg=t["ink"],
                    insertbackground=t["ink"],
                    selectbackground=t["selected"],
                    relief="flat",
                    padx=12,
                    pady=8,
                )
            self.more_nav.configure(
                bg=t["nav"],
                fg=t["nav_ink"],
                activebackground=t["selected"],
                activeforeground=t["ink"],
            )
            self.nav_menu.configure(
                bg=t["surface"],
                fg=t["ink"],
                activebackground=t["selected"],
                activeforeground=t["ink"],
            )
            self.highlight()
        for label in self.footer_labels:
            label.configure(foreground=t["muted"])
        for view in self.cards:
            view.update()

    def highlight(self, event=None):
        for tab, button in self.nav.items():
            button.configure(
                bg=self.colors["selected"] if tab == self.app.tabs.select() else self.colors["nav"],
                fg=self.colors["ink"] if tab == self.app.tabs.select() else self.colors["nav_ink"],
                activebackground=self.colors["selected"],
                activeforeground=self.colors["ink"],
            )
        for button, _, _, tab in getattr(self, "nav_items", []):
            if tab is None:
                button.configure(
                    bg=self.colors["nav"],
                    fg=self.colors["nav_ink"],
                    activebackground=self.colors["selected"],
                    activeforeground=self.colors["ink"],
                )
        if self.app.tabs.select() == str(self.app.inbox):
            self.app.inbox.refresh()

    def scroll_cards(self, event):
        if self.app.tabs.select() == str(self.app.live_tab):
            self.app.card_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def resize(self, event=None):
        if event is not None and event.widget is not self.app.root:
            return
        self.arrange()

    def arrange(self, event=None):
        app = self.app
        narrow = app.root.winfo_width() < 1100
        self.rail.configure(width=58 if narrow else 188)
        self.rail_title.configure(
            text="BM" if narrow else "OPERASYON", pady=8 if app.root.winfo_height() < 650 else 18
        )
        for index, (button, icon, caption, _) in enumerate(self.nav_items):
            if narrow and index >= 4:
                button.pack_forget()
            else:
                button.pack(fill="x", padx=6, pady=2)
            button.configure(
                text=icon if narrow else f"{icon}   {caption}",
                anchor="center" if narrow else "w",
                pady=6 if app.root.winfo_height() < 650 else 11,
            )
        if narrow:
            self.more_nav.pack(fill="x", padx=6, pady=2)
        else:
            self.more_nav.pack_forget()
        visible = [
            v for v in self.cards if self.show_all.get() or v.card.enabled.get() or v.expanded
        ]
        if not visible:
            visible = self.cards
        width = max(1, app.card_canvas.winfo_width())
        height = max(1, app.card_canvas.winfo_height())
        columns, rows = grid_shape(len(visible), width)
        compact = height / max(rows, 1) < 260 and not any(v.expanded for v in visible)
        target = max(230 if compact else 350, height // max(rows, 1) - 12)
        layout = (
            tuple(v.card.index for v in visible),
            columns,
            rows,
            compact,
            target,
            any(v.expanded for v in visible),
        )
        if layout == self.last_layout:
            return
        self.last_layout = layout
        for n in range(8):
            app.card_grid.columnconfigure(
                n, weight=1 if n < columns else 0, uniform="cards" if n < columns else ""
            )
            app.card_grid.rowconfigure(
                n, weight=1 if n < rows else 0, minsize=target if n < rows else 0
            )
        for view in self.cards:
            view.card.frame.grid_remove()
        for n, view in enumerate(visible):
            view.card.frame.grid(
                row=n // columns, column=n % columns, sticky="nsew", padx=5, pady=6
            )
            view.set_compact(compact)
        app.card_canvas.itemconfigure(
            app.card_window,
            height=0 if any(v.expanded for v in visible) else max(height, rows * (target + 12)),
        )
        self.source_note.configure(
            text=f"{len([v for v in visible if v.card.enabled.get()])} etkin kanal · {app.receive_mode.get()}"
        )

    def update(self):
        if self.app.closing:
            return
        self.arrange()
        self.start.configure(state=str(self.app.start_button.cget("state")))
        count = sum(v.card.enabled.get() for v in self.cards)
        self.source_note.configure(text=f"{count} etkin kanal · {self.app.receive_mode.get()}")
        for view in self.cards:
            view.update()
        for button, icon, caption, tab in self.nav_items:
            if tab == str(self.app.inbox):
                count = sum(self.app.inbox.unread.values())
                text = (
                    f"{icon} {count}"
                    if self.app.root.winfo_width() < 1100
                    else f"{icon}   {caption}" + (f"  {count}" if count else "")
                )
                button.configure(text=text)
        self.after_id = self.app.root.after(250, self.update)
