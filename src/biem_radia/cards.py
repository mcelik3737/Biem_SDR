import tkinter as tk
from tkinter import ttk

from .models import Channel
from .signal_follow import GREEN_RANGE_HZ
from .tones import CTCSS, DCS

MODES = {
    "Otomatik": "AUTO",
    "Analog": "NFM",
    "DMR": "DMR",
    "TETRA": "TETRA",
    "APCO25": "APCO25",
    "NXDN": "NXDN",
}


class ChannelCard:
    def __init__(self, parent, index):
        self.index = index
        self.frame = ttk.LabelFrame(parent, text=f"KANAL {index + 1:02d}", padding=12)
        self.frame.grid(row=index // 3, column=index % 3, sticky="nsew", padx=6, pady=6)
        self.name = tk.StringVar()
        self.enabled = tk.BooleanVar()
        self.mode = tk.StringVar(value="Analog")
        self.freq = tk.StringVar()
        self.peak = tk.StringVar(value="Tepe: — MHz\nΔ — kHz")
        self.peak_color = "#5c6e83"
        self.follow_signal = tk.BooleanVar(value=True)
        self.code = tk.StringVar()
        self.tone_mode = tk.StringVar(value="CSQ")
        self.tone = tk.StringVar(value="67.0")
        self.threshold = tk.StringVar(value="-45")
        self.state = tk.StringVar(value="○ Frekans girin")
        self.details = tk.StringVar(value="Henüz veri yok")
        self.level = tk.DoubleVar(value=0)
        self.channel: Channel | None = None
        head = ttk.Frame(self.frame)
        head.pack(fill="x")
        ttk.Checkbutton(head, text="Etkin", variable=self.enabled).pack(side="left")
        ttk.Entry(head, textvariable=self.name, width=22).pack(side="left", fill="x", expand=True)
        row = ttk.Frame(self.frame)
        row.pack(fill="x", pady=(8, 0))
        ttk.Label(row, text="Mod").grid(row=0, column=0, sticky="w")
        ttk.Label(row, text="Frekans / MHz").grid(row=0, column=1, sticky="w", padx=6)
        self.mode_box = ttk.Combobox(
            row, textvariable=self.mode, values=list(MODES), state="readonly", width=10
        )
        self.mode_box.grid(row=1, column=0, sticky="ew")
        self.mode_box.bind("<<ComboboxSelected>>", lambda e: self.update_options())
        ttk.Entry(row, textvariable=self.freq, width=16).grid(row=1, column=1, sticky="ew", padx=6)
        row.columnconfigure(1, weight=1)
        row2 = ttk.Frame(self.frame)
        row2.pack(fill="x", pady=8)
        self.code_label = ttk.Label(row2, text="Color code")
        self.code_label.grid(row=0, column=0, sticky="w")
        ttk.Label(row2, text="Eşik / dBFS").grid(row=0, column=1, sticky="w", padx=6)
        self.code_entry = ttk.Entry(row2, textvariable=self.code, width=11)
        self.code_entry.grid(row=1, column=0)
        ttk.Entry(row2, textvariable=self.threshold, width=12).grid(row=1, column=1, padx=6)
        tones = ttk.Frame(self.frame)
        tones.pack(fill="x")
        self.tone_box = ttk.Combobox(
            tones,
            textvariable=self.tone_mode,
            values=["CSQ", "CTCSS", "DCS", "DCS-I"],
            state="readonly",
            width=10,
        )
        self.tone_box.pack(side="left")
        self.value_box = ttk.Combobox(tones, textvariable=self.tone, width=12, state="readonly")
        self.value_box.pack(side="left", padx=6)
        self.tone_box.bind("<<ComboboxSelected>>", lambda e: self.update_options())
        ttk.Checkbutton(
            self.frame, text="Yakın sinyale kilitlen (±6,5 kHz)", variable=self.follow_signal
        ).pack(anchor="w", pady=(8, 0))
        ttk.Label(self.frame, textvariable=self.state, foreground="#246293").pack(
            anchor="w", pady=(10, 4)
        )
        ttk.Progressbar(self.frame, variable=self.level, maximum=100).pack(fill="x")
        tk.Label(
            self.frame,
            textvariable=self.details,
            wraplength=330,
            foreground="#526174",
            background="#f3f5f8",
            anchor="w",
            justify="left",
            font=("Segoe UI", 9),
            height=2,
        ).pack(anchor="w", pady=(5, 0))
        self.update_options()

    def update_options(self):
        analog = self.mode.get() == "Analog"
        automatic = self.mode.get() == "Otomatik"
        self.code_entry.configure(state="disabled" if analog or automatic else "normal")
        self.code_label.configure(
            text={"APCO25": "NAC (ondalık)", "NXDN": "RAN", "DMR": "CC (boş: otomatik)"}.get(
                self.mode.get(), "Color code"
            )
        )
        self.tone_box.configure(state="readonly" if analog else "disabled")
        values: list[str] = (
            [str(v) for v in CTCSS] if self.tone_mode.get() == "CTCSS" else list(DCS)
        )
        self.value_box.configure(
            values=values,
            state="readonly" if analog and self.tone_mode.get() != "CSQ" else "disabled",
        )
        if self.tone_mode.get() != "CSQ" and self.tone.get() not in values:
            self.tone.set(values[0])
        if self.mode.get() == "DMR":
            self.details.set("CC boş: otomatik keşif • ID / grup için yayın beklenir")
        if automatic:
            self.details.set("Otomatik: Analog / DMR / TETRA • XPT yalnız protokol kanıtıyla")
        if analog:
            self.details.set("Analog • " + self.tone_mode.get())
        if self.mode.get() in ("TETRA", "APCO25", "NXDN"):
            self.details.set("Deneysel çözücü • gerçek RF kabul testi bekliyor")

    def load(self, channel):
        self.peak.set("Tepe: — MHz\nΔ — kHz")
        self.peak_color = "#5c6e83"
        self.channel = channel
        if channel is None:
            self.name.set("")
            self.freq.set("")
            self.code.set("")
            self.enabled.set(False)
            self.mode.set("Analog")
            self.follow_signal.set(True)
            self.tone_mode.set("CSQ")
            self.tone.set("67.0")
            self.state.set("○ Frekans girin")
            self.details.set("Henüz veri yok")
            self.update_options()
            return
        self.name.set(channel.name)
        self.enabled.set(channel.enabled)
        self.follow_signal.set(channel.follow_signal)
        self.mode.set(next(k for k, v in MODES.items() if v == channel.mode))
        self.freq.set(f"{channel.frequency_hz / 1e6:.5f}")
        self.code.set("" if channel.color_code is None else str(channel.color_code))
        self.threshold.set(str(channel.squelch_db))
        self.tone_mode.set(channel.tone_mode)
        self.tone.set(channel.tone_value)
        self.state.set("○ Beklemede" if channel.enabled else "○ Devre dışı")
        self.update_options()

    def value(self):
        if not self.freq.get().strip():
            if self.enabled.get():
                raise ValueError(f"Kanal {self.index + 1}: frekans girin.")
            return None
        mode = MODES[self.mode.get()]
        spacing = 25000 if mode == "TETRA" else 12500
        if self.channel and self.channel.mode == mode:
            spacing = self.channel.spacing_hz
        bandwidth = (
            25000 if mode == "TETRA" else 12500 if mode != "NXDN" or spacing != 6250 else 6250
        )
        if self.channel and self.channel.mode == mode:
            bandwidth = self.channel.bandwidth_hz
        return Channel(
            self.name.get().strip() or f"Kanal {self.index + 1}",
            round(float(self.freq.get().replace(",", ".")) * 1e6),
            spacing,
            bandwidth,
            float(self.threshold.get()),
            mode=mode,
            system=self.channel.system if self.channel else "Default",
            color_code=int(self.code.get())
            if mode not in ("NFM", "AUTO") and self.code.get().strip()
            else None,
            enabled=self.enabled.get(),
            tone_mode=self.tone_mode.get() if mode == "NFM" else "CSQ",
            tone_value=self.tone.get(),
            follow_signal=self.follow_signal.get(),
        )

    def telemetry(self, state):
        self.peak.set("Tepe: — MHz\nΔ — kHz")
        self.peak_color = "#5c6e83"
        if state is None:
            self.level.set(0)
            self.state.set(
                "○ Sırası bekleniyor"
                if self.enabled.get() and self.freq.get()
                else "○ Devre dışı / boş"
            )
            return
        peak_hz = state.get("peak_hz")
        offset_hz = state.get("peak_offset_hz")
        follow_state = state.get("follow_state", "disabled")
        locked = follow_state in ("locked", "holding")
        if locked:
            peak_hz = state.get("locked_hz")
            offset_hz = state.get("lock_offset_hz")
        if peak_hz is not None and offset_hz is not None:
            offset_khz = round(offset_hz / 1000, 2)
            if offset_khz == 0:
                offset_khz = 0.0
            label = "RF" if locked else "Tepe ≈"
            suffix = " · KİLİT" if follow_state == "locked" else " · BEKLE" if locked else ""
            self.peak.set(f"{label} {peak_hz / 1e6:.5f} MHz\nΔ {offset_khz:+.2f} kHz{suffix}")
            if follow_state != "holding":
                self.peak_color = "#18784a" if abs(offset_hz) <= GREEN_RANGE_HZ else "#b42336"
        db = state["level"]
        self.level.set(max(0, min(100, db + 100)))
        self.state.set(f"{'● KAYIT' if state['active'] else '◉ DİNLENİYOR'} • {db:.1f} dBFS")
        self.details.set(state.get("data", "Analog • CSQ")[:150])

    def set_editable(self, enabled):
        def visit(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Checkbutton, ttk.Combobox)):
                    widget.configure(
                        state=("readonly" if isinstance(widget, ttk.Combobox) else "normal")
                        if enabled
                        else "disabled"
                    )
                visit(widget)

        visit(self.frame)
        if enabled:
            self.update_options()
