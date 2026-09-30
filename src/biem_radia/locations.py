"""Read completed UTF-16LE DMR location messages, never the decoder's LOCN guess."""

import json
import math
import re
from datetime import datetime
from pathlib import Path

from .digital_log import Tail


def coordinates(text: str) -> tuple[float, float] | None:
    lat = re.search(r"Enlem:\s*([NS])\s*(\d+(?:\.\d+)?)\s*°", text)
    lon = re.search(r"Boylam:\s*([EW])\s*(\d+(?:\.\d+)?)\s*°", text)
    if not lat or not lon:
        return None
    latitude = float(lat[2]) * (-1 if lat[1] == "S" else 1)
    longitude = float(lon[2]) * (-1 if lon[1] == "W" else 1)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return latitude, longitude


class LocationParser:
    def __init__(self):
        self.header: dict | None = None
        self.cc: int | None = None
        self.clean_sync = False
        self.utf16 = False
        self.parts: list[str] | None = None

    def feed(self, event: dict) -> dict | None:
        raw = event.get("raw", "")
        if not isinstance(raw, str) or event.get("protocol") != "DMR":
            return None
        if re.search(r"(?:CRC|FEC).*?(?:ERR|FAIL)", raw):
            self.header, self.parts, self.utf16 = None, None, False
            self.clean_sync = False
            return None
        result = None
        if self.parts is not None:
            if re.fullmatch(r"\s*[0-9A-Fa-f]{8,}\s*", raw):
                if len(self.parts) < 512:
                    self.parts.append(raw.strip())
                else:
                    self.parts = None
                    self.header = None
                return None
            result = self.finish()
        if "Sync:" in raw:
            match = re.search(r"Color Code=(\d+)\b", raw)
            self.cc = int(match[1]) if match and 0 <= int(match[1]) <= 15 else None
            self.clean_sync = self.cc is not None and "ERR" not in raw
            if "no sync" in raw:
                self.header = None
                self.utf16 = False
        if "Data Header" in raw:
            self.header = None
            self.utf16 = False
            h = re.search(
                r"Slot ([12]) Data Header - (Indiv|Group) - Short Data: Defined.*Source: (\d+) Target: (\d+)",
                raw,
            )
            if h and self.clean_sync and all(0 < int(h[i]) <= 0xFFFFFF for i in (3, 4)):
                self.header = {
                    "source_id": int(h[3]),
                    "target_id": int(h[4]),
                    "call_type": "private" if h[2] == "Indiv" else "group",
                    "decoder_slot": int(h[1]),
                    "color_code": self.cc,
                    "observed_utc": event["observed_utc"],
                    "channel": event.get("channel", ""),
                    "frequency_hz": event.get("frequency_hz"),
                }
        if self.header and "FMT" in raw:
            self.utf16 = "[UTF-16LE]" in raw
        m = re.search(r"Slot ([12]) - Multi Block PDU Message", raw)
        if m and self.header and self.utf16 and int(m[1]) == self.header["decoder_slot"]:
            try:
                age = (
                    datetime.fromisoformat(event["observed_utc"])
                    - datetime.fromisoformat(self.header["observed_utc"])
                ).total_seconds()
                if 0 <= age <= 15:
                    self.parts = []
            except (ValueError, TypeError, KeyError):
                self.header = None
        return result

    def finish(self) -> dict | None:
        parts, header = self.parts, self.header
        self.parts, self.header = None, None
        if not parts or not header:
            return None
        try:
            payload = bytes.fromhex("".join(parts))
            # Short-data application prefix precedes the observed Turkish text.
            start = payload.find("Boylam:".encode("utf-16-le"))
            if start < 0 or start % 2:
                return None
            end = next(
                (i for i in range(start, len(payload) - 1, 2) if payload[i : i + 2] == b"\0\0"),
                None,
            )
            if end is None:
                return None
            text = payload[start:end].decode("utf-16-le", errors="strict")
            position = coordinates(text)
            if position is None:
                return None
            message_time = re.search(r"Zaman:\s*(\d{2}:\d{2}:\d{2})", text)
            day = re.search(r"Tarih:\s*(\d{4}-\d{2}-\d{2})", text)
            return {
                **header,
                "latitude": position[0],
                "longitude": position[1],
                "message_time": f"{day[1]} {message_time[1]}"
                if day and message_time
                else "Bilinmiyor",
                "text": text,
                "basis": "DMR UTF-16LE konum metni",
            }
        except (ValueError, UnicodeError):
            return None


def valid_location(value: dict) -> bool:
    try:
        return (
            all(math.isfinite(float(value[k])) for k in ("latitude", "longitude"))
            and -90 <= float(value["latitude"]) <= 90
            and -180 <= float(value["longitude"]) <= 180
            and 0 < int(value["source_id"]) <= 0xFFFFFF
            and datetime.fromisoformat(value["observed_utc"]).tzinfo is not None
        )
    except (TypeError, KeyError, ValueError, OverflowError):
        return False


class LocationReader:
    def __init__(self, root: Path):
        self.root = root
        self.cache = root / "locations/latest.json"
        self.latest: dict | None = None
        self.readers: dict[Path, tuple[Tail, LocationParser]] = {}
        self.turn = 0
        try:
            value = json.loads(self.cache.read_text("utf-8"))
            if isinstance(value, dict) and valid_location(value):
                self.latest = value
        except (OSError, ValueError):
            pass

    def poll(self) -> bool:
        paths = sorted(
            self.root.glob("dmr-sessions/*/digital.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        # Read newest files each time; also sweep older sessions in bounded groups.
        chosen = paths[:4]
        older = paths[4:]
        if older:
            self.turn %= len(older)
            chosen += older[self.turn : self.turn + 4]
            self.turn += 4
        changed = False
        for path in chosen:
            if path not in self.readers:
                self.readers[path] = Tail(path), LocationParser()
            tail, parser = self.readers[path]
            for line in tail.read():
                try:
                    event = json.loads(line)
                    result = parser.feed(event) if isinstance(event, dict) else None
                    if (
                        result
                        and valid_location(result)
                        and (
                            self.latest is None
                            or datetime.fromisoformat(result["observed_utc"])
                            > datetime.fromisoformat(self.latest["observed_utc"])
                        )
                    ):
                        self.latest = {**result, "session": path.parent.name}
                        changed = True
                except (ValueError, KeyError, TypeError):
                    continue
        if changed:
            self.cache.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.cache.with_suffix(".part")
            temporary.write_text(json.dumps(self.latest, ensure_ascii=False, indent=2), "utf-8")
            temporary.replace(self.cache)
        return changed
