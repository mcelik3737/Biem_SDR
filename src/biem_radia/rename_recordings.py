"""Rename existing archive files without changing audio, retaining a recovery manifest."""

import argparse
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from .filenames import available_path, recording_name
from .storage import Archive


def migrate(archive: Archive, apply=False):
    with archive.connect() as db:
        rows = db.execute("SELECT * FROM calls ORDER BY started_utc,id").fetchall()
    plan = []
    reserved = set()
    root = (archive.root / "recordings").resolve()
    for row in rows:
        old = archive.audio_path(row["id"]).resolve()
        if not old.is_relative_to(root):
            raise ValueError(f"Kayıt klasörü dışında dosya: {old}")
        mode = row["source"].split("/")[0]
        if mode in ("USB", "rtl_tcp"):
            mode = "NFM"
        name = recording_name(
            mode,
            datetime.fromisoformat(row["started_utc"]),
            row["duration"],
            row["radio_id"],
            row["group_id"],
        )
        if re.fullmatch(re.escape(Path(name).stem) + r"(?:_\d+)?\.wav", old.name):
            continue
        new = available_path(old.parent, name)
        suffix = 2
        while new in reserved or new.exists():
            new = old.parent / f"{Path(name).stem}_{suffix:02d}.wav"
            suffix += 1
        if not new.resolve().is_relative_to(root):
            raise ValueError("Hedef kayıt klasörü dışında.")
        reserved.add(new)
        plan.append({"id": row["id"], "old": str(old), "new": str(new)})
    if not apply or not plan:
        return plan
    backup = archive.root / "backups" / datetime.now().strftime("rename-%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True)
    with archive.connect() as db, closing(sqlite3.connect(backup / "radia.sqlite3")) as copy:
        db.backup(copy)
    (backup / "rename-manifest.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), "utf-8"
    )
    moved = []
    try:
        with archive.connect() as db:
            for item in plan:
                old, new = Path(item["old"]), Path(item["new"])
                if new.exists():
                    raise FileExistsError(new)
                old.rename(new)
                moved.append((old, new))
                db.execute(
                    "UPDATE calls SET path=? WHERE id=?",
                    (str(new.relative_to(archive.root)), item["id"]),
                )
    except Exception:
        for old, new in reversed(moved):
            new.rename(old)
        raise
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate(Archive(args.data), args.apply), ensure_ascii=False, indent=2))
