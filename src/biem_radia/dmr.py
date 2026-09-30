from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import time
import uuid
import wave
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy import signal

from .digital_log import DigitalJournal
from .filenames import available_path, recording_name
from .live_audio import WavTap
from .models import SAMPLE_RATE, Channel
from .storage import Archive

BACKEND_PATH = Path("vendor/dsd-fme/package/dsd-fme-portable")
# Contracts verified against release 20260715, bundled source 69d3115:
# dsd_file.c close_and_rename_wav_file, dsd_events.c write_event_to_log_file.
WAV_NAME = re.compile(
    r"(?P<date>\d{8})_(?P<time>\d{6})_\d+_(?P<system>DMR(?:_[A-F0-9]+)?_CC_\d+|P25_[A-F0-9]+(?:_\d+_\d+)?|NXDN(?:_\d+_\d+)?_RAN_\d+)_(?P<kind>GROUP|PRIVATE)?_TGT_(?P<target>\d+)_SRC_(?P<radio>\d+)\.wav"
)
EVENT = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<protocol>DMR|P25p1|P25p2|P25|NXDN) TGT: (?P<target>\d+); SRC: (?P<radio>\d+); (?P<label>CC|NAC|RAN): (?P<cc>[\dA-Fa-f]+);(?P<extra>.*)"
)


@dataclass(frozen=True)
class DmrEvent:
    observed: datetime
    radio: int | None
    target: int | None
    color_code: int
    kind: str | None
    slot: int | None
    encrypted: bool
    protocol: str = "DMR"


def parse_event(line: str) -> DmrEvent | None:
    m = EVENT.fullmatch(line.strip())
    if m is None:
        return None
    protocol = "P25" if m["protocol"].startswith("P25") else m["protocol"]
    try:
        cc = int(m["cc"], 16 if protocol == "P25" else 10)
    except ValueError:
        return None
    radio, target = int(m["radio"]), int(m["target"])
    if (
        m["label"] != {"DMR": "CC", "P25": "NAC", "NXDN": "RAN"}[protocol]
        or cc > {"DMR": 15, "P25": 4095, "NXDN": 63}[protocol]
        or radio > 0xFFFFFF
        or target > 0xFFFFFF
    ):
        return None
    extra = m["extra"]
    slots = set(re.findall(r"\bSlot ([12]);", extra))
    kind = "group" if "Group;" in extra else "private" if "Private;" in extra else None
    return DmrEvent(
        datetime.fromisoformat(f"{m['date']}T{m['time']}").astimezone(timezone.utc),
        radio or None,
        target or None,
        cc,
        kind,
        int(next(iter(slots))) if len(slots) == 1 else None,
        "ENC;" in extra,
        protocol,
    )


def decoder_slot(log: str, event: DmrEvent) -> int | None:
    """Read the MS/DM decoder lane, not a verified physical TDMA slot."""
    stamp = event.observed.astimezone().strftime("%H:%M:%S")
    slots = set()
    matched = False
    for line in log.splitlines():
        if "Sync:" in line:
            code = re.search(r"\bColor Code=(\d{1,2})\b", line)
            matched = (
                line.startswith(stamp + " Sync:")
                and "DMR MS/DM MODE/MONO" in line
                and code is not None
                and int(code[1]) == event.color_code
                and re.search(r"\b(?:ERR|ERROR)\b", line) is None
            )
        elif matched:
            m = re.search(r"SLOT ([12]) TGT=(\d+) SRC=(\d+)\b", line)
            if m and int(m[2]) == event.target and int(m[3]) == event.radio:
                slots.add(int(m[1]))
    return next(iter(slots)) if len(slots) == 1 else None


class DmrDiscriminator:
    """48 kHz mono discriminator. No voice HPF, de-emphasis, audio gain or squelch."""

    def __init__(self, channel: Channel, center_hz: int):
        self.offset = channel.frequency_hz - center_hz
        self.position = 0
        self.previous = 0j
        self.offset_hz = 0.0
        self.last_hz = np.zeros(0)
        self.sos = np.asarray(
            signal.butter(8, channel.bandwidth_hz / 2, fs=SAMPLE_RATE, output="sos")
        )
        self.state = np.zeros((len(self.sos), 2), dtype=np.complex128)

    def process(self, iq: np.ndarray) -> tuple[bytes, float]:
        n = np.arange(len(iq)) + self.position
        shifted = iq * np.exp(-2j * np.pi * self.offset / SAMPLE_RATE * (n % SAMPLE_RATE))
        filtered, self.state = signal.sosfilt(self.sos, shifted, zi=self.state)
        narrow = filtered[(-self.position) % 20 :: 20]
        self.position += len(iq)
        if not len(narrow):
            self.last_hz = np.zeros(0)
            return b"", -120.0
        hz = np.angle(narrow * np.conj(np.concatenate(([self.previous], narrow[:-1])))) * (
            48000 / (2 * np.pi)
        )
        self.previous = narrow[-1]
        self.offset_hz = float(np.mean(hz))
        self.last_hz = hz
        level = float(10 * np.log10(max(float(np.mean(abs(narrow) ** 2)), 1e-12)))
        return np.clip(hz * (32767 / 12000), -32767, 32767).astype("<i2").tobytes(), level


class DmrImporter:
    def __init__(self, archive: Archive, channel: Channel, directory: Path):
        self.archive, self.channel, self.directory = archive, channel, directory
        self.completed = 0
        self.seen: set[str] = set()
        self.last_metadata = "Senkron / çağrı bekleniyor"
        self.recording_check: Callable[[], bool] | None = None

    def scan(self) -> int:
        if self.recording_check is not None and not self.recording_check():
            return 0
        events_path = self.directory / "events.log"
        if not events_path.exists():
            return 0
        events = [
            event
            for line in events_path.read_text("utf-8", errors="replace").splitlines()
            if (event := parse_event(line)) is not None
        ]
        count = 0
        if events:
            e = events[-1]
            target_label = (
                "Grup" if e.kind == "group" else "Özel hedef" if e.kind == "private" else "Hedef"
            )
            self.last_metadata = f"Son çağrı: ID {e.radio or '—'} • {target_label} {e.target or '—'} • Slot {e.slot or '—'} • CC {e.color_code}"
        for path in self.directory.glob("*.wav"):
            if path.name in self.seen:
                continue
            m = WAV_NAME.fullmatch(path.name)
            if m is None:
                continue  # TEMP files are never considered complete recordings.
            protocol = "P25" if self.channel.mode == "APCO25" else self.channel.mode
            if not m["system"].startswith(protocol + "_"):
                continue
            if protocol == "P25":
                net = m["system"].split("_")[1]
                code = int(net[-3:], 16)
            else:
                code = int(m["system"].rsplit("_", 1)[1])
            observed = datetime.strptime(m["date"] + m["time"], "%Y%m%d%H%M%S").astimezone(
                timezone.utc
            )
            matches = [
                e
                for e in events
                if e.observed == observed
                and (e.radio or 0) == int(m["radio"])
                and (e.target or 0) == int(m["target"])
                and e.color_code == code
                and e.protocol == protocol
            ]
            if not matches:
                continue  # Wait for the matching committed event, never reuse the previous call.
            signatures = {
                (e.radio, e.target, e.color_code, e.kind, e.slot, e.encrypted) for e in matches
            }
            if len(signatures) != 1:
                # Same IDs/timestamp in both slots cannot be mapped safely from this backend's filenames.
                self.archive.event(
                    "WARNING", f"DMR belirsiz slot eşleştirmesi, dosya korundu: {path.name}"
                )
                self.seen.add(path.name)
                continue
            event = matches[0]
            if event.encrypted or (
                self.channel.color_code is not None and event.color_code != self.channel.color_code
            ):
                self.seen.add(path.name)
                self.archive.event(
                    "INFO", "DMR kayıt alınmadı: şifreli çağrı veya farklı color code."
                )
                continue
            if m["kind"] and m["kind"].lower() != event.kind:
                continue
            try:
                with wave.open(str(path), "rb") as wav:
                    if (
                        wav.getnchannels() != 1
                        or wav.getsampwidth() != 2
                        or wav.getframerate() != 8000
                    ):
                        raise ValueError(
                            "DSD-FME WAV sözleşmesi değişti; beklenen 8 kHz/16-bit/mono."
                        )
                    frames = wav.getnframes()
                    pcm = wav.readframes(frames)
                    if len(pcm) != frames * 2:
                        continue
            except FileNotFoundError:
                continue  # Upstream removes empty WAVs immediately after closing.
            self.seen.add(path.name)
            if not frames or not np.any(np.frombuffer(pcm, dtype="<i2")):
                self.archive.event(
                    "INFO", "DMR yalnız metadata/sessiz PCM: ses kaydı oluşturulmadı."
                )
                continue
            full_duration = frames / 8000
            origin = event.observed - timedelta(seconds=full_duration)
            # DSD-FME commits WAVs when the call closes. Apply the archive policy
            # independently to each committed call/slot; preserve decoder evidence.
            for offset in range(0, frames, 92 * 8000):
                part = pcm[offset * 2 : min(offset + 90 * 8000, frames) * 2]
                duration = len(part) / 16000
                identity = str(path.resolve()) + (f"#frame={offset}" if offset else "")
                call_id = uuid.uuid5(uuid.NAMESPACE_URL, identity).hex
                started = origin + timedelta(seconds=offset / 8000)
                directory = (
                    self.archive.root / "recordings" / started.astimezone().strftime("%Y-%m-%d")
                )
                with self.archive.connect() as db:
                    if db.execute("SELECT 1 FROM calls WHERE id=?", (call_id,)).fetchone():
                        continue
                directory.mkdir(parents=True, exist_ok=True)
                destination = available_path(
                    directory,
                    recording_name(
                        self.channel.mode,
                        started,
                        duration,
                        event.radio,
                        event.target if event.kind == "group" else None,
                    ),
                )
                temporary = destination.with_suffix(".part")
                with wave.open(str(temporary), "wb") as out:
                    out.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                    out.writeframes(part)
                temporary.replace(destination)
                self.archive.add_dmr(call_id, self.channel, event, started, duration, destination)
                log_path = self.directory / "decoder.log"
                if event.protocol == "DMR" and event.slot is None and log_path.exists():
                    lane = decoder_slot(log_path.read_text("utf-8", errors="replace"), event)
                    if lane is not None:
                        with self.archive.connect() as db:
                            db.execute(
                                "UPDATE calls SET decoder_slot=? WHERE id=?", (lane, call_id)
                            )
                if duration == 90:
                    with self.archive.connect() as db:
                        db.execute(
                            "UPDATE calls SET end_reason='max_duration' WHERE id=?", (call_id,)
                        )
                count += 1
            self.archive.protect_file(path)
        self.completed += count
        return count


class DmrBackend:
    def __init__(self, archive: Archive, channel: Channel, project: Path):
        self.channel = channel
        self.base = (project / BACKEND_PATH).resolve()
        executable = self.base / "dsd-fme/dsd-fme.exe"
        if not executable.exists():
            raise RuntimeError("DSD-FME bulunamadı. Setup-DMR.ps1 dosyasını çalıştırın.")
        self.directory = archive.root / "dmr-sessions" / uuid.uuid4().hex
        self.directory.mkdir(parents=True)
        self.audio_tap = WavTap(self.directory)
        self.audio_packets = []
        self.importer = DmrImporter(archive, channel, self.directory)
        self.log = (self.directory / "decoder.log").open("wb")
        self.journal = DigitalJournal(self.directory, channel)
        self.capture: wave.Wave_write | None = None
        self.capture_frames = 0
        if os.environ.get("BIEM_DMR_DIAGNOSTIC") == "1":
            self.capture = wave.open(str(self.directory / "discriminator.wav"), "wb")
            self.capture.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        self.connection: socket.socket | None = None
        self.process: subprocess.Popen | None = None
        listener = socket.socket()
        try:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            listener.settimeout(10)
            command = [
                str(executable),
                {
                    "DMR": "-fs",
                    "APCO25": "-f1",
                    "NXDN": "-fi" if channel.spacing_hz == 6250 else "-fn",
                }[channel.mode],
                "-i",
                f"tcp:127.0.0.1:{listener.getsockname()[1]}",
                "-o",
                "null",
                "-7",
                self.directory.as_posix(),
                "-P",
                "-Z",
                "-L",
                (self.directory / "lrrp.tsv").as_posix(),
                "-J",
                (self.directory / "events.log").as_posix(),
            ]
            (self.directory / "session.json").write_text(
                json.dumps(
                    {
                        "channel": channel.name,
                        "system": channel.system,
                        "frequency_hz": channel.frequency_hz,
                        "decoder": "20260715 / 69d3115",
                        "input": "48000 Hz S16LE mono discriminator",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "utf-8",
            )
            self.process = subprocess.Popen(
                command,
                cwd=self.base,
                stdout=self.log,
                stderr=self.log,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            self.connection, _ = listener.accept()
            self.connection.settimeout(1)
        except Exception:
            self.close()
            raise
        finally:
            listener.close()
        self.last_scan = 0.0

    @property
    def completed(self):
        return self.importer.completed

    def feed(self, pcm: bytes):
        if self.capture is not None:
            remaining = max(0, 120 * 48000 - self.capture_frames)
            self.capture.writeframes(pcm[: remaining * 2])
            self.capture_frames += min(len(pcm) // 2, remaining)
            if not remaining:
                self.capture.close()
                self.capture = None
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError(f"DMR çözücüsü kapandı. Günlük: {self.directory / 'decoder.log'}")
        assert self.connection is not None
        self.connection.sendall(pcm)
        if time.monotonic() - self.last_scan > 0.4:
            self.journal.poll()
            self.importer.scan()
            if time.monotonic() - self.journal.updated < 2:
                self.importer.last_metadata = self.journal.latest
            self.last_scan = time.monotonic()
        packets = self.audio_tap.poll()
        cc_allowed = self.channel.color_code is None or (
            self.journal.cc == self.channel.color_code
            and time.monotonic() - self.journal.sync_time < 2
        )
        permitted = self.importer.recording_check
        self.audio_packets = packets if cc_allowed and (permitted is None or permitted()) else []

    def close(self):
        if self.capture is not None:
            self.capture.close()
            self.capture = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        forced = False
        if self.process is not None:
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                forced = True
                self.process.terminate()
                self.process.wait(timeout=3)
        self.log.close()
        self.journal.poll()
        self.importer.scan()
        for path in self.directory.glob("*.wav"):
            self.importer.archive.protect_file(path)
        if forced:
            self.importer.archive.event(
                "WARNING", "DMR kapanışta zaman aşımı. Tamamlanmamış TEMP dosyaları korunuyor."
            )
