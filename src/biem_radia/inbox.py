"""Read-only presentation of existing digital logs; no RF or decoder changes."""

import hashlib
import json
import re
import sqlite3
import time
import tkinter as tk
from contextlib import closing
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from .digital_log import Tail
from .locations import LocationParser


def local_time(value):
    try:
        date = datetime.fromisoformat(value)
        return date.astimezone().strftime("%Y-%m-%d %H:%M:%S") if date.tzinfo else value
    except (ValueError, TypeError):
        return "—"


def raw_message(event):
    raw = event.get("raw", "")
    if not isinstance(raw, str) or not re.search(
        r"\b(SDS|UDT|PDU|Data Header|GPS|LRRP|LOCN)\b", raw, re.I
    ):
        return None
    result = {**event, "text": raw, "kind": "Ham veri · mesaj çözülmedi"}
    # Only metadata on this exact data header is associated with this row.
    header = re.search(r"Slot ([12]) Data Header - (Indiv|Group).*Source: (\d+) Target: (\d+)", raw)
    if header:
        result.update(
            source_id=int(header[3]),
            target_id=int(header[4]),
            call_type="group" if header[2] == "Group" else "private",
        )
    return result


class InboxStore:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.database = root / "message-index.sqlite3"
        self.readers = {}
        self.turn = 0
        with closing(sqlite3.connect(self.database, autocommit=True)) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY, at_local TEXT, channel TEXT, protocol TEXT,
                source_id TEXT, group_id TEXT, target_id TEXT, kind TEXT, text TEXT,
                provenance TEXT)""")

    def add(self, event, provenance, identity):
        if not isinstance(event.get("text"), str):
            return False
        key = hashlib.sha256(f"{provenance}:{identity}".encode()).hexdigest()
        group = event.get("target_id") if event.get("call_type") == "group" else None
        values = (
            key,
            local_time(event.get("observed_utc")),
            event.get("channel", ""),
            event.get("protocol", "DMR"),
            str(event.get("source_id") or ""),
            str(group or ""),
            str(event.get("target_id") or ""),
            event.get("kind", "Konum metni"),
            event["text"],
            provenance,
        )
        with closing(sqlite3.connect(self.database, autocommit=True)) as db:
            return bool(
                db.execute(
                    "INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?,?,?,?,?)", values
                ).rowcount
            )

    def poll(self):
        paths = sorted(
            list(self.root.glob("dmr-sessions/*/digital.jsonl"))
            + list(self.root.glob("tetra-sessions/*/events.jsonl"))
        )
        if not paths:
            return False
        chosen = [paths[(self.turn + n) % len(paths)] for n in range(min(4, len(paths)))]
        self.turn = (self.turn + len(chosen)) % len(paths)
        changed = False
        for path in chosen:
            if path not in self.readers or path.stat().st_size < self.readers[path][0].offset:
                self.readers[path] = (Tail(path), LocationParser(), 0)
            tail, parser, number = self.readers[path]
            for line in tail.read():
                number += 1
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        continue
                    message = parser.feed(event)
                    raw = raw_message(event)
                    for kind, value in (("text", message), ("raw", raw)):
                        if value:
                            changed |= self.add(
                                value, str(path.relative_to(self.root)), f"{number}:{kind}:{line}"
                            )
                except (ValueError, TypeError, KeyError):
                    continue
            self.readers[path] = tail, parser, number
        return changed

    def search(self, text="", day=""):
        with closing(sqlite3.connect(self.database, autocommit=True)) as db:
            db.row_factory = sqlite3.Row
            return db.execute(
                """SELECT * FROM messages WHERE
                (?='' OR instr(lower(channel||' '||source_id||' '||group_id||' '||target_id||' '||text),lower(?))>0)
                AND (?='' OR substr(at_local,1,10)=?)
                ORDER BY at_local DESC, rowid DESC LIMIT 1000""",
                (text, text, day, day),
            ).fetchall()


class InboxPanel(ttk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent, padding=14)
        self.store = InboxStore(root)
        self.last_poll = 0.0
        self.query = tk.StringVar()
        self.day = tk.StringVar()
        self.rows = {}
        ttk.Label(self, text="Gelen Mesajlar", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(self, text="Kanal, cihaz ID, grup veya mesaj metniyle arayın.").pack(
            anchor="w", pady=8
        )
        filters = ttk.Frame(self)
        filters.pack(fill="x", pady=10)
        for label, variable, width in (
            ("Kanal / ID / grup / metin", self.query, 35),
            ("Tarih / YYYY-MM-DD", self.day, 18),
        ):
            field = ttk.Frame(filters)
            field.pack(side="left", padx=(0, 12))
            ttk.Label(field, text=label).pack(anchor="w")
            entry = ttk.Entry(field, textvariable=variable, width=width)
            entry.pack()
            entry.bind("<Return>", lambda e: self.refresh())
        ttk.Button(filters, text="Ara / yenile", command=self.refresh).pack(
            side="left", pady=(16, 0)
        )
        ttk.Label(
            self,
            text="Özel hedef grup değildir. —: bilgi çözülmedi. Ham veri, okunabilir mesaj olduğu anlamına gelmez.",
            wraplength=900,
        ).pack(anchor="w", pady=8)
        self.note = ttk.Label(self)
        self.note.pack(side="bottom", anchor="w", pady=8)
        self.detail = tk.Text(self, height=7, wrap="word", state="disabled", font=("Segoe UI", 10))
        self.detail.pack(side="bottom", fill="x", pady=8)
        table = ttk.Frame(self)
        table.pack(fill="both", expand=True)
        columns = ("at_local", "channel", "source_id", "group_id", "target_id", "kind", "text")
        self.table = ttk.Treeview(table, columns=columns, show="headings")
        for key, label, width in zip(
            columns,
            ("Tarih / saat", "Kanal", "Cihaz ID", "Grup", "Hedef ID", "Tür", "Mesaj"),
            (155, 110, 75, 75, 75, 175, 250),
            strict=True,
        ):
            self.table.heading(key, text=label)
            self.table.column(key, width=width, minwidth=65)
        vertical = ttk.Scrollbar(table, command=self.table.yview)
        horizontal = ttk.Scrollbar(table, orient="horizontal", command=self.table.xview)
        vertical.pack(side="right", fill="y")
        horizontal.pack(side="bottom", fill="x")
        self.table.pack(fill="both", expand=True)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.table.bind("<<TreeviewSelect>>", self.select)
        self.refresh()

    def refresh(self):
        selected = self.table.selection()
        self.rows = {
            row["id"]: dict(row)
            for row in self.store.search(self.query.get().strip(), self.day.get().strip())
        }
        self.table.delete(*self.table.get_children())
        for key, row in self.rows.items():
            self.table.insert(
                "", "end", iid=key, values=[row[c] or "—" for c in self.table["columns"]]
            )
        if selected and selected[0] in self.rows:
            self.table.selection_set(selected[0])
        self.select()
        self.note.configure(
            text=f"{len(self.rows)} sonuç · En yeni 1000 sonuç · Yerel saat · Mevcut dijital günlüklerden"
        )

    def select(self, event=None):
        selected = self.table.selection()
        row = self.rows.get(selected[0]) if selected else None
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert(
            "end",
            f"{row['text']}\n\nKaynak: {row['provenance']} · {row['protocol']}"
            if row
            else "Mesaj ayrıntısı için bir satır seçin.",
        )
        self.detail.configure(state="disabled")

    def poll(self):
        if time.monotonic() - self.last_poll < 1:
            return
        self.last_poll = time.monotonic()
        if self.store.poll():
            self.refresh()
