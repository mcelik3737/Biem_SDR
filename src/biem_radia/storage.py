from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dmr import DmrEvent
    from .models import Channel


class Archive:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "radia.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY, channel TEXT NOT NULL, frequency_hz INTEGER NOT NULL,
                    started_utc TEXT NOT NULL, duration REAL NOT NULL, path TEXT NOT NULL,
                    source TEXT NOT NULL, end_reason TEXT NOT NULL,
                    radio_id TEXT, group_id TEXT, slot INTEGER, title TEXT,
                    CHECK (slot IS NULL OR slot IN (1,2))
                );
                CREATE INDEX IF NOT EXISTS calls_time ON calls(started_utc);
                CREATE INDEX IF NOT EXISTS calls_channel ON calls(channel);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, at_utc TEXT NOT NULL, level TEXT NOT NULL,
                    message TEXT NOT NULL
                );
            """)
            columns = {row[1] for row in db.execute("PRAGMA table_info(calls)")}
            for name, declaration in {
                "system": "TEXT NOT NULL DEFAULT 'Default'",
                "destination_id": "TEXT",
                "call_type": "TEXT",
                "color_code": "INTEGER",
                "decoder_slot": "INTEGER",
                "timing_basis": "TEXT NOT NULL DEFAULT 'sample_clock'",
            }.items():
                if name not in columns:
                    db.execute(f"ALTER TABLE calls ADD COLUMN {name} {declaration}")
            db.execute(
                "CREATE TABLE IF NOT EXISTS aliases (system TEXT NOT NULL, kind TEXT NOT NULL, identity TEXT NOT NULL, name TEXT NOT NULL, PRIMARY KEY(system,kind,identity))"
            )

    def set_alias(self, system: str, kind: str, identity: str, name: str):
        if kind not in ("radio", "group") or not system.strip() or not name.strip():
            raise ValueError("Sistem, tür ve isim gerekli.")
        if not identity.isdecimal() or not 1 <= int(identity) <= 0xFFFFFF:
            raise ValueError("DMR ID 1–16777215 arasında olmalı.")
        identity = str(int(identity))
        with self.connect() as db:
            db.execute(
                "INSERT INTO aliases VALUES(?,?,?,?) ON CONFLICT(system,kind,identity) DO UPDATE SET name=excluded.name",
                (system.strip(), kind, identity, name.strip()),
            )
            field = "radio_id" if kind == "radio" else "group_id"
            db.execute(
                f"UPDATE calls SET title=? WHERE system=? AND {field}=?",
                (name.strip(), system.strip(), identity),
            )

    def aliases(self, system: str):
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM aliases WHERE system=? ORDER BY kind,identity", (system,)
            ).fetchall()

    def add_dmr(
        self,
        call_id: str,
        channel: Channel,
        event: DmrEvent,
        started: datetime,
        duration: float,
        path: Path,
    ):
        radio = str(event.radio) if event.radio is not None else None
        target = str(event.target) if event.target is not None else None
        group = target if event.kind == "group" else None
        with self.connect() as db:
            alias = db.execute(
                "SELECT name FROM aliases WHERE system=? AND ((kind='radio' AND identity=?) OR (kind='group' AND identity=?)) ORDER BY CASE kind WHEN 'radio' THEN 0 ELSE 1 END LIMIT 1",
                (channel.system, radio, group),
            ).fetchone()
            db.execute(
                """INSERT OR IGNORE INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason,radio_id,group_id,slot,title,system,destination_id,call_type,color_code,timing_basis)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    call_id,
                    channel.name,
                    channel.frequency_hz,
                    started.isoformat(),
                    duration,
                    str(path.relative_to(self.root)),
                    "DMR/DSD-FME",
                    "decoder_closed",
                    radio,
                    group,
                    event.slot,
                    alias[0] if alias else None,
                    channel.system,
                    target,
                    event.kind,
                    event.color_code,
                    "decoder_last_event_minus_audio",
                ),
            )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        db.create_function(
            "fold",
            1,
            lambda value: (
                str(value or "").translate(str.maketrans({"I": "ı", "İ": "i"})).casefold()
            ),
            deterministic=True,
        )
        try:
            with db:
                yield db
        finally:
            db.close()

    def event(self, level: str, message: str):
        with self.connect() as db:
            db.execute(
                "INSERT INTO events(at_utc,level,message) VALUES(?,?,?)",
                (datetime.now(timezone.utc).isoformat(), level, message),
            )

    def search(
        self, text: str = "", day: str = "", *, slot: int | None = None, system: str = ""
    ) -> list[sqlite3.Row]:
        clauses = []
        parameters: list[str] = []
        if text:
            clauses.append(
                "(instr(fold(channel),fold(?)) > 0 OR instr(fold(coalesce(title,'')),fold(?)) > 0 OR radio_id = ? OR group_id = ? OR destination_id = ? OR EXISTS(SELECT 1 FROM aliases a WHERE a.system=calls.system AND ((a.kind='radio' AND a.identity=calls.radio_id) OR (a.kind='group' AND a.identity=calls.group_id)) AND instr(fold(a.name),fold(?)) > 0))"
            )
            parameters += [text] * 6
        if slot is not None:
            if slot not in (1, 2):
                raise ValueError("Slot 1 veya 2 olmalı.")
            clauses.append("slot=?")
            parameters.append(str(slot))
        if system:
            clauses.append("system=?")
            parameters.append(system)
        if day:
            selected = date.fromisoformat(day)
            # Datetimes without tzinfo are interpreted in the PC's local timezone.
            start = datetime.combine(selected, datetime.min.time()).astimezone(timezone.utc)
            end = datetime.combine(selected + timedelta(days=1), datetime.min.time()).astimezone(
                timezone.utc
            )
            clauses.append("started_utc >= ? AND started_utc < ?")
            parameters += [start.isoformat(), end.isoformat()]
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM calls" + where + " ORDER BY started_utc DESC LIMIT 1000", parameters
            ).fetchall()

    def audio_path(self, call_id: str) -> Path:
        with self.connect() as db:
            row = db.execute("SELECT path FROM calls WHERE id=?", (call_id,)).fetchone()
        if row is None:
            raise ValueError("Kayıt bulunamadı.")
        path = (self.root / row["path"]).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError("Ses dosyası bulunamadı veya geçersiz.")
        return path
