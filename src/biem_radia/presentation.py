"""Visual layout only. Reuses the original widgets, variables and commands."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from .branding import MODEL

BG = "#edf2f7"
INK = "#203045"
MUTED = "#5c6e83"
NAV = "#142638"
BLUE = "#2464b4"


class ChannelPresentation:
    def __init__(self, card):
        self.card = card
        self.original = [(w, w.pack_info()) for w in card.frame.winfo_children()]
        for widget, _ in self.original:
            widget.pack_forget()
        card.frame.configure(style="Channel.TLabelframe", padding=14)
        self.summary = ttk.Frame(card.frame, style="Paper.TFrame")
        self.summary.pack(fill="x")
        self.name = ttk.Label(self.summary, textvariable=card.name, style="ChannelTitle.TLabel")
        self.name.pack(anchor="w")
        self.frequency_row = ttk.Frame(self.summary, style="Paper.TFrame")
        self.frequency_row.pack(fill="x", pady=(6, 12))
        self.frequency_row.columnconfigure(0, weight=1)
        self.frequency = ttk.Label(
            self.frequency_row, style="Paper.TLabel", font=("Consolas", 9), justify="left"
        )
        self.frequency.grid(row=0, column=0, sticky="nw")
        self.peak = ttk.Label(
            self.frequency_row,
            textvariable=card.peak,
            style="Paper.TLabel",
            font=("Consolas", 9),
            foreground=BLUE,
            justify="right",
        )
        self.peak.grid(row=0, column=1, sticky="ne", padx=(6, 0))
        self.state = ttk.Label(self.summary, textvariable=card.state, style="Paper.TLabel")
        self.state.pack(anchor="w")
        ttk.Progressbar(self.summary, variable=card.level, maximum=100).pack(fill="x", pady=10)
        self.detail = ttk.Label(
            self.summary, textvariable=card.details, style="Paper.TLabel", wraplength=300
        )
        self.detail.pack(fill="x", anchor="w")
        self.button = ttk.Button(self.summary, text="Kanal ayarları ▾", command=self.toggle)
        self.button.pack(anchor="e", pady=(10, 0))
        self.expanded = False
        self.update()

    def toggle(self):
        self.expanded = not self.expanded
        for widget, options in self.original:
            if self.expanded:
                widget.pack(**options)
            else:
                widget.pack_forget()
        self.button.configure(text="Ayarları gizle ▴" if self.expanded else "Kanal ayarları ▾")

    def update(self):
        c = self.card
        self.frequency.configure(
            text=f"{c.freq.get() or '—'} MHz\n{c.mode.get()} · {'Etkin' if c.enabled.get() else 'Devre dışı'}"
        )
        self.detail.configure(wraplength=max(180, c.frame.winfo_width() - 35))
        self.peak.configure(foreground=c.peak_color)
        self.state.configure(foreground="#c03550" if "KAYIT" in c.state.get() else INK)


class Presentation:
    def __init__(self, app, outer, header):
        self.app = app
        self.theme()
        outer.configure(padding=0)
        header.configure(style="Paper.TFrame", padding=(20, 10))
        with Image.open(Path(__file__).parent / "assets/biem-logo.png") as image:
            image.thumbnail((145, 46), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(image, master=app.root)
        for widget in header.winfo_children():
            if isinstance(widget, ttk.Button) and "FM RADIO" in str(widget.cget("text")):
                widget.pack_forget()
            if isinstance(widget, ttk.Label):
                widget.configure(style="Paper.TLabel")
                if widget.cget("image"):
                    widget.configure(image=self.logo)
                elif widget.cget("text") == "CANLI KANALLAR  /  KAYIT ARŞİVİ":
                    widget.configure(text="İzleme ve kayıt")
        # Move the original status label; it stays attached to the original status variable.
        for widget in outer.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.pack_forget()
                widget.configure(style="Paper.TLabel", padding=(18, 8), font=("Segoe UI", 10))
                widget.pack(side="bottom", fill="x")
        self.body = ttk.Frame(outer)
        self.body.pack(fill="both", expand=True)
        rail = tk.Frame(self.body, bg=NAV, width=178)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        tk.Label(
            rail, text=f"BİEM / {MODEL}", bg=NAV, fg="white", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=16, pady=(22, 5))
        tk.Label(rail, text="İZLEME VE KAYIT", bg=NAV, fg="#9bb1c7", font=("Segoe UI", 9)).pack(
            anchor="w", padx=16, pady=(0, 18)
        )
        content = ttk.Frame(self.body, padding=12)
        content.pack(side="left", fill="both", expand=True)
        app.tabs.pack_forget()
        app.tabs.configure(style="Sidebar.TNotebook")
        app.tabs.pack(in_=content, fill="both", expand=True)
        app.tabs.lift()
        self.nav = {}
        names = {
            "Canlı Kanallar": "◉  Canlı izleme",
            "Kayıt Arşivi": "▤  Kayıt arşivi",
            "Gelen Mesajlar": "✉  Gelen mesajlar",
            "Harita": "⌖  Harita",
            "Dijital Veri Günlüğü": "≡  Dijital veri günlüğü",
            "Spektrum / Yönetici": "∿  Spektrum",
            "Alıcı / Gelişmiş Ayarlar": "⚙  Alıcı / kanal ayarları",
            "SDR Cihazları": "▣  SDR cihazları",
            "Hytera Ethernet": "⇄  Hytera Ethernet",
            "FM Radio": "♫  FM Radio ▾",
            "BİEM": "ⓘ  BİEM",
        }
        pages = {app.tabs.tab(tab, "text").strip(): tab for tab in app.tabs.tabs()}
        for label, caption in names.items():
            if label not in pages and label != "FM Radio":
                continue
            tab = pages.get(label)
            button = tk.Button(
                rail,
                text=caption,
                command=app.toggle_radio if tab is None else lambda p=tab: app.tabs.select(p),
                bg=NAV,
                fg="#e0e8f0",
                activebackground="#2a4c6d",
                activeforeground="white",
                relief="flat",
                bd=0,
                anchor="w",
                padx=10,
                pady=11,
                font=("Segoe UI", 10),
            )
            button.pack(fill="x", padx=8, pady=2)
            if tab is not None:
                self.nav[tab] = button
        ttk.Label(app.live_tab, text="Canlı izleme", style="PageTitle.TLabel").pack(
            anchor="w", before=app.live_tab.winfo_children()[0], pady=(0, 10)
        )
        app.start_button.configure(style="Primary.TButton")
        self.cards = [ChannelPresentation(card) for card in app.cards]
        app.card_grid.bind("<Configure>", self.arrange, add="+")
        self.arrange()
        app.calls.bind("<Return>", lambda event: app.play())
        search = app.calls.master.winfo_children()[0]
        for widget in search.winfo_children():
            if isinstance(widget, tk.Widget):
                widget.pack_forget()
        for n, widget in enumerate(search.winfo_children()):
            if isinstance(widget, tk.Widget):
                widget.grid(
                    row=0 if n < 3 else 1,
                    column=n if n < 3 else n - 3,
                    sticky="w",
                    padx=(0, 8),
                    pady=6,
                )
        app.tabs.bind("<<NotebookTabChanged>>", self.highlight, add="+")
        self.highlight()
        self.update()

    def theme(self):
        style = ttk.Style(self.app.root)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=INK)
        style.configure("Paper.TFrame", background="white")
        style.configure("Paper.TLabel", background="white", foreground=MUTED)
        style.configure("PageTitle.TLabel", font=("Segoe UI", 21, "bold"))
        style.configure(
            "Channel.TLabelframe", background="white", bordercolor="#d7e0ea", relief="solid"
        )
        style.configure(
            "Channel.TLabelframe.Label", background=BG, foreground=MUTED, font=("Segoe UI", 9)
        )
        style.configure(
            "ChannelTitle.TLabel", background="white", foreground=INK, font=("Segoe UI", 14, "bold")
        )
        style.configure("TButton", background="white", bordercolor="#d7e0ea", padding=(12, 7))
        style.configure("Primary.TButton", background=BLUE, foreground="white")
        style.map(
            "Primary.TButton",
            background=[("active", "#174c8e"), ("disabled", "#d5dde7")],
            foreground=[("disabled", "#637285")],
        )
        style.configure("Treeview", rowheight=36, borderwidth=0)
        style.configure("Treeview.Heading", background="#e7edf4", padding=9)
        style.map("Treeview", background=[("selected", "#dae8fa")], foreground=[("selected", INK)])
        style.configure("Sidebar.TNotebook", background=BG, borderwidth=0)
        style.layout("Sidebar.TNotebook.Tab", [])

    def highlight(self, event=None):
        for tab, button in self.nav.items():
            button.configure(bg="#2a4c6d" if tab == self.app.tabs.select() else NAV)

    def arrange(self, event=None):
        columns = 3 if self.app.card_grid.winfo_width() >= 950 else 2
        for n in range(3):
            self.app.card_grid.columnconfigure(
                n, weight=1 if n < columns else 0, uniform="cards" if n < columns else ""
            )
        for n, card in enumerate(self.app.cards):
            card.frame.grid(row=n // columns, column=n % columns, sticky="nsew", padx=6, pady=8)

    def update(self):
        if self.app.closing:
            return
        for card in self.cards:
            card.update()
        self.app.root.after(300, self.update)
