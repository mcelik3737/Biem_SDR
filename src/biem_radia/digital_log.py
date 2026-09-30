"""Bounded incremental decoder log reader. Labels describe text, not RF validation."""

import json
import re
import time
import tkinter as tk
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from tkinter import ttk

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class Tail:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.pending = b""

    def read(self) -> list[str]:
        if not self.path.exists():
            return []
        if self.path.stat().st_size < self.offset:
            self.offset, self.pending = 0, b""
        with self.path.open("rb") as stream:
            stream.seek(self.offset)
            data = stream.read(131072)
            self.offset = stream.tell()
        chunks = (self.pending + data.replace(b"\r", b"\n")).split(b"\n")
        self.pending = chunks.pop()[-131072:]
        return [ANSI.sub("", c.decode("utf-8", errors="replace")) for c in chunks if c]


class DigitalJournal:
    def __init__(self, directory: Path, channel):
        self.directory, self.channel = directory, channel
        self.tail = Tail(directory / "decoder.log")
        self.latest = ""
        self.updated = 0.0
        self.cc = None
        self.sync_time = 0.0
        self.direct = False
        self.observer: Callable[[str], None] | None = None

    def poll(self):
        lines = self.tail.read()
        if not lines:
            return
        with (self.directory / "digital.jsonl").open("a", encoding="utf-8") as stream:
            for line in lines:
                category = (
                    "konum/veri çıktısı"
                    if re.search(
                        r"\b(GPS|LRRP|LOCN|SDS|Latitude|Longitude|UDT|PDU|Data Header)\b",
                        line,
                        re.I,
                    )
                    else "çözücü"
                )
                stream.write(
                    json.dumps(
                        {
                            "observed_utc": datetime.now(timezone.utc).isoformat(),
                            "channel": self.channel.name,
                            "frequency_hz": self.channel.frequency_hz,
                            "protocol": self.channel.mode,
                            "category": category,
                            "raw": line,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                self.observe(line)

    def observe(self, line: str):
        if self.observer is not None:
            self.observer(line)
        if re.search(r"no sync|(?:CRC|FEC).*?(?:ERR|FAIL)", line, re.I):
            self.cc = None
            self.sync_time = 0.0
            return
        if "Sync:" in line:
            match = re.search(r"Color Code=(\d+)\b", line)
            self.cc = (
                int(match[1])
                if match and int(match[1]) <= 15 and "DMR" in line and "ERR" not in line
                else None
            )
            self.sync_time = time.monotonic()
            self.direct = "MS/DM" in line
            self.latest = f"Alınan CC {self.cc}" if self.cc is not None else "Senkron bekleniyor"
            self.updated = self.sync_time
        match = re.search(r"SLOT ([12]) TGT=(\d+) SRC=(\d+)\b", line)
        if match and self.cc is not None and time.monotonic() - self.sync_time < 2:
            # Label group/private only when that same decoder line explicitly says so.
            slot_label = "Çözücü slotu" if self.direct else "Slot"
            target_label = (
                "Grup"
                if re.search(r"\bGroup\b", line)
                else "Özel hedef"
                if re.search(r"\bPrivate\b", line)
                else "Hedef"
            )
            self.latest = f"CC {self.cc} • ID {match[3]} • {target_label} {match[2]} • {slot_label} {match[1]}"
            self.updated = time.monotonic()


class DigitalLogPanel(ttk.Frame):
    def __init__(self, parent, archive):
        super().__init__(parent, padding=12)
        self.archive = archive
        self.tails: dict[Path, Tail] = {}
        self.last_refresh = 0.0
        self.filter = tk.StringVar(value="Tümü")
        row = ttk.Frame(self)
        row.pack(fill="x")
        ttk.Label(row, text="DİJİTAL VERİ GÜNLÜĞÜ", font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Combobox(
            row,
            textvariable=self.filter,
            values=["Tümü", "GPS / SDS / Veri"],
            state="readonly",
            width=22,
        ).pack(side="right")
        ttk.Label(
            self,
            text="DMR: decoder.log + digital.jsonl + lrrp.tsv  |  TETRA: events.jsonl\n"
            "Ham çözücü çıktısıdır. Konum metni tek başına geçerli GPS tespiti değildir.",
        ).pack(anchor="w", pady=8)
        box = ttk.Frame(self)
        box.pack(fill="both", expand=True)
        self.text = tk.Text(box, state="disabled", wrap="word", font=("Consolas", 10))
        scroll = ttk.Scrollbar(box, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        ttk.Label(
            self, text="Ekran son 1000 satırı gösterir; dosyada kalan satırlar silinmez."
        ).pack(anchor="w")

    def poll(self):
        if time.monotonic() - self.last_refresh < 1:
            return
        self.last_refresh = time.monotonic()
        paths = list(self.archive.root.glob("dmr-sessions/*/digital.jsonl"))
        paths += list(self.archive.root.glob("hytera-sessions/*/digital.jsonl"))
        paths += list(self.archive.root.glob("hytera-status/*.jsonl"))
        paths += list(self.archive.root.glob("dmr-sessions/*/auto-detection.jsonl"))
        paths += list(self.archive.root.glob("tetra-sessions/*/events.jsonl"))
        paths = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)[:6]
        self.tails = {p: t for p, t in self.tails.items() if p in paths}
        output = []
        for path in reversed(paths):
            if path not in self.tails:
                tail = Tail(path)
                tail.offset = max(0, path.stat().st_size - 32768)
                self.tails[path] = tail
            for line in self.tails[path].read():
                if self.filter.get() != "Tümü" and not re.search(
                    r"GPS|LRRP|LOCN|SDS|Latitude|Longitude|Location|UDT|PDU|Data.Header", line, re.I
                ):
                    continue
                output.append(f"[{path.parent.name[:8]}] {line}\n")
        if output:
            self.text.configure(state="normal")
            self.text.insert("end", "".join(output))
            lines = int(self.text.index("end-1c").split(".")[0])
            if lines > 1000:
                self.text.delete("1.0", f"{lines - 1000}.0")
            self.text.see("end")
            self.text.configure(state="disabled")
