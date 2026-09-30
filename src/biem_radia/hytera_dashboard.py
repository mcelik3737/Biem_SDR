"""Touch-friendly repeater telemetry; scale fill is not an alarm threshold."""

from __future__ import annotations

import math
import time
import tkinter as tk
from tkinter import ttk
from typing import Literal

from .console_theme import DARK, LIGHT
from .hytera_metrics import measurement_cell
from .hytera_snmp import ALARM_BASE

# Measurement, title, subtitle, scale minimum/maximum, associated alarm.
SCALES = (
    (1, "Besleme", "PSU VOLTAGE", 0, 30, 1),
    (2, "Sıcaklık", "PA TEMPERATURE", 0, 100, 2),
    (4, "Anten uyumu", "VSWR", 1, 6, 6),
    (5, "İleri güç", "TX FWD POWER", 0, 70, 4),
    (6, "Yansıyan güç", "TX REF POWER", 0, 15, 5),
)


def alarm_display(record, now: float, running: bool) -> tuple[str, str]:
    if record is None:
        return "Bilgi yok", "gray"
    value, at, label = record
    text = label.split(": ", 1)[-1]
    if not running or now - at > 35:
        return text + " • eski", "gray"
    return text, "gray" if value is None else "red" if value > 0 else "green"


class HyteraDashboard(ttk.Frame):
    def __init__(self, parent, read_rssi):
        super().__init__(parent)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(12, 8))
        ttk.Label(toolbar, text="Röle ölçümleri", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.rssi_button = ttk.Button(
            toolbar, text="↻ RSSI oku", command=read_rssi, padding=(20, 12)
        )
        self.rssi_button.pack(side="right")
        self.canvas = tk.Canvas(self, highlightthickness=0, height=390)
        self.canvas.pack(fill="x")
        self.telemetry: dict = {}
        self.last_key = None
        self.canvas.bind("<Configure>", lambda event: self.redraw())
        ttk.Label(
            self,
            text="Ölçümler 10 sn'de bir yenilenir. RSSI oku: iki slotu şimdi sorgula. RSSI birimi: dB (MIB).",
            wraplength=820,
        ).pack(anchor="w", pady=(6, 10))

    def update_state(self, state: dict):
        self.telemetry = state
        pending = any(r["status"] == "pending" for r in state.get("rssi_read", {}).values())
        self.rssi_button.configure(
            state="normal" if state["running"] and not pending else "disabled"
        )
        self.rssi_button.configure(text="RSSI okunuyor…" if pending else "↻ RSSI oku")
        self.redraw()

    def redraw(self):
        canvas, state = self.canvas, self.telemetry
        if not state:
            return
        width = max(300, canvas.winfo_width())
        background = ttk.Style(self).lookup("TFrame", "background")
        colors = DARK if background == DARK["bg"] else LIGHT
        now = time.monotonic()
        key = (
            width,
            colors["bg"],
            int(now),
            repr(state.get("measurements")),
            repr(state.get("fields")),
            repr(state.get("rssi_read")),
            state["running"],
        )
        if key == self.last_key:
            return
        self.last_key = key
        columns = min(5, max(1, width // 156))
        rows = math.ceil(5 / columns)
        small_cols = min(4, max(1, width // 185))
        top = rows * 254
        height = top + math.ceil(4 / small_cols) * 116
        canvas.configure(height=height, background=colors["bg"])
        canvas.delete("all")

        def text(
            x,
            y,
            label,
            size=10,
            color="ink",
            bold=False,
            anchor: Literal["w", "e"] = "w",
            wrap: float = 0,
        ):
            canvas.create_text(
                x,
                y,
                text=label,
                fill=colors[color],
                anchor=anchor,
                font=("Segoe UI", size, "bold" if bold else "normal"),
                width=wrap,
            )

        def card(x, y, w, h):
            canvas.create_rectangle(
                x + 1, y + 1, x + w - 8, y + h - 8, fill=colors["surface"], outline=colors["line"]
            )

        for index, (number, title, subtitle, low, high, alarm) in enumerate(SCALES):
            w = width / columns
            x, y = index % columns * w, index // columns * 254
            card(x, y, w, 254)
            text(x + 14, y + 24, title, 11, bold=True)
            text(x + 14, y + 44, subtitle, 8, "muted")
            record = state["measurements"].get(number)
            reading, age = measurement_cell(record, now, state["running"])
            alarm_text, alarm_color = alarm_display(
                state["fields"].get(f"{ALARM_BASE}{alarm}.0"), now, state["running"]
            )
            fresh = record is not None and state["running"] and now - record["at"] <= 35
            value = record["value"] if record else None
            valid = value is not None and fresh
            gauge_color = "red" if alarm_color == "red" else "blue" if valid else "gray"
            bx, by, bottom = x + w / 2 - 2, y + 64, y + 164
            canvas.create_rectangle(bx, by, bx + 24, bottom, fill=colors["raised"], outline="")
            if value is not None:
                ratio = max(0, min(1, (value - low) / (high - low)))
                if ratio:
                    canvas.create_rectangle(
                        bx,
                        bottom - ratio * 100,
                        bx + 24,
                        bottom,
                        fill=colors[gauge_color],
                        outline="",
                    )
            for tick in range(6):
                ty = bottom - tick * 20
                label = f"{low + (high - low) * tick / 5:g}" + (":1" if number == 4 else "")
                text(bx - 10, ty, label, 8, "muted", anchor="e")
                canvas.create_line(bx - 6, ty, bx - 2, ty, fill=colors["muted"])
            text(
                x + 14,
                y + 190,
                reading if value is not None else "Ölçüm yok",
                16,
                "ink" if fresh else "muted",
                True,
            )
            text(x + 14, y + 216, age, 8, "muted")
            clipped = valid and value is not None and (value < low or value > high)
            text(
                x + 14,
                y + 236,
                "Skala dışında" if clipped else alarm_text,
                8,
                "orange" if clipped else alarm_color,
                wrap=w - 25,
            )

        for index in range(4):
            w = width / small_cols
            x, y = index % small_cols * w, top + index // small_cols * 116
            card(x, y, w, 116)
            if index < 2:
                alarm = 8 if index == 0 else 7
                label, color = alarm_display(
                    state["fields"].get(f"{ALARM_BASE}{alarm}.0"), now, state["running"]
                )
                title = "Alıcı PLL" if index == 0 else "Verici PLL"
                detail = "Rölenin kilit alarmı"
            else:
                slot = index - 1
                title = f"RSSI • Slot {slot}"
                manual = state.get("rssi_read", {}).get(slot)
                if manual:
                    label = manual["text"].replace("— / ölçüm yok", "Ölçüm yok")
                    age = max(0, now - manual["at"])
                    detail = (
                        "Yeni yanıt bekleniyor"
                        if manual["status"] == "pending"
                        else f"Elle okuma • {age:.0f} sn önce"
                    )
                    if age > 35 or not state["running"]:
                        detail += " • eski"
                    color = (
                        "blue"
                        if manual["status"] == "ok" and age <= 35 and state["running"]
                        else "gray"
                    )
                else:
                    label, detail = measurement_cell(
                        state["measurements"].get(slot + 8), now, state["running"]
                    )
                    label = label.replace("— / ölçüm yok", "Ölçüm yok")
                    color = "gray" if "eski" in detail or label.startswith("—") else "blue"
            text(x + 14, y + 22, title, 11, bold=True)
            text(x + 14, y + 53, label, 13, color, True, wrap=w - 28)
            text(x + 14, y + 88, detail, 8, "muted", wrap=w - 28)
