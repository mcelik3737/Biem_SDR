from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


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

    def search(self, text: str = "", day: str = "") -> list[sqlite3.Row]:
        clauses = []
        parameters: list[str] = []
        if text:
            clauses.append(
                "(instr(fold(channel),fold(?)) > 0 OR instr(fold(coalesce(title,'')),fold(?)) > 0 OR radio_id = ? OR group_id = ?)"
            )
            parameters += [text] * 4
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
