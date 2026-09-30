"""Read-only audio monitoring. Never writes recordings or blocks the RF worker."""

import logging
import queue
import struct
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly


class WavTap:
    """Tail the backend's open mono PCM files, keeping each file a separate stream."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.positions: dict[str, int] = {}
        self.last_poll = 0.0

    def poll(self):
        if time.monotonic() - self.last_poll < 0.08:
            return []
        self.last_poll = time.monotonic()
        packets = []
        paths = list(self.directory.glob("TEMP_*"))
        for path in paths:
            if path.suffix == ".radia":
                continue
            try:
                with path.open("rb") as source:
                    header = source.read(4096)
                    if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
                        continue
                    cursor, rate, data_at = 12, 0, 0
                    while cursor + 8 <= len(header):
                        tag, length = struct.unpack_from("<4sI", header, cursor)
                        if tag == b"fmt " and length >= 16:
                            fmt, channels, rate, _, _, bits = struct.unpack_from(
                                "<HHIIHH", header, cursor + 8
                            )
                            if (fmt, channels, bits) != (1, 1, 16) or rate != 8000:
                                break
                        if tag == b"data":
                            data_at = cursor + 8
                            break
                        cursor += 8 + length + length % 2
                    if not data_at or rate != 8000:
                        continue
                    end = source.seek(0, 2)
                    position = self.positions.get(path.name, data_at)
                    if position > end:
                        position = data_at
                    # Monitoring may drop old audio to stay live; archival audio is untouched.
                    position = max(position, data_at + max(0, (end - data_at) // 2 - 4000) * 2)
                    source.seek(position)
                    pcm = source.read((end - position) // 2 * 2)
                    self.positions[path.name] = position + len(pcm)
                    if pcm:
                        packets.append((path.name, np.frombuffer(pcm, "<i2") / 32768.0, rate))
            except (OSError, ValueError, struct.error):
                continue  # partial headers and close/rename races are normal here
        live_names = {p.name for p in paths}
        self.positions = {k: v for k, v in self.positions.items() if k in live_names}
        return packets


class LiveAudio:
    """One selected channel/stream at a time, with independent per-channel meters."""

    def __init__(self):
        self.selected: str | None = None
        self.stream_choice: str | None = None
        self.stream_labels: dict[tuple[str, str], str] = {}
        self.meters: dict[tuple[str, str], tuple[float, float]] = {}
        self.pending: queue.Queue = queue.Queue(maxsize=12)
        self.output = None
        self.volume = 0.65
        self.error = ""
        self.lock = threading.Lock()
        self.remainder = np.zeros(0, dtype=np.float32)
        self.generation = 0

    def select(self, channel: str | None, stream: str | None = None):
        self.stop()
        if channel is None:
            return
        output = None
        try:
            output = sd.OutputStream(
                samplerate=16000,
                channels=1,
                dtype="float32",
                blocksize=800,
                callback=self._callback,
            )
            output.start()
            self.output = output
            self.selected, self.stream_choice = channel, stream
            self.error = ""
        except (sd.PortAudioError, OSError, ValueError) as exc:
            if output is not None:
                try:
                    output.close()
                except (sd.PortAudioError, OSError):
                    pass
            self.error = f"Ses çıkışı açılamadı: {exc}"
            raise RuntimeError(self.error) from exc

    def stop(self):
        self.generation += 1
        self.selected = self.stream_choice = None
        if self.output is not None:
            try:
                self.output.stop()
            except (sd.PortAudioError, OSError) as exc:
                self.error = str(exc)
            finally:
                try:
                    self.output.close()
                except (sd.PortAudioError, OSError) as exc:
                    self.error = str(exc)
                self.output = None
        while not self.pending.empty():
            try:
                self.pending.get_nowait()
            except queue.Empty:
                break
        self.remainder = np.zeros(0, dtype=np.float32)

    def feed(self, channel: str, stream: str, audio: np.ndarray, rate: int, label: str):
        # Monitor failure must never interrupt the recording/decoder pipeline.
        try:
            self._feed(channel, stream, audio, rate, label)
        except Exception as exc:
            if not self.error:
                logging.exception("Live monitor failed; recording continues")
            self.error = str(exc)

    def _feed(self, channel: str, stream: str, audio: np.ndarray, rate: int, label: str):
        if not len(audio):
            return
        audio = np.clip(np.nan_to_num(np.asarray(audio, dtype=np.float32)), -1, 1)
        level = float(20 * np.log10(max(float(np.sqrt(np.mean(audio * audio))), 1e-6)))
        now = time.monotonic()
        with self.lock:
            self.meters[channel, stream] = now, level
            self.stream_labels[channel, stream] = label
            self.meters = {k: v for k, v in self.meters.items() if now - v[0] < 2}
            self.stream_labels = {k: v for k, v in self.stream_labels.items() if k in self.meters}
            if channel != self.selected:
                return
            selected = self.meters.get((channel, self.stream_choice or ""))
            if self.stream_choice is None or selected is None or now - selected[0] > 0.8:
                if level < -65:
                    return
                self.stream_choice = stream
            generation = self.generation
            if stream != self.stream_choice:
                return  # never sum two slots or two radio channels
        if rate == 8000:
            audio = resample_poly(audio, 2, 1).astype(np.float32)
        elif rate != 16000:
            return
        try:
            self.pending.put_nowait((now, generation, audio.copy()))
        except queue.Full:
            pass  # only the monitor drops; the recorder receives its original samples

    def _callback(self, outdata, frames, timing, status):
        outdata.fill(0)
        cursor = 0
        while cursor < frames:
            if not len(self.remainder):
                try:
                    stamp, generation, data = self.pending.get_nowait()
                except queue.Empty:
                    break
                if generation != self.generation or time.monotonic() - stamp > 0.75:
                    continue
                self.remainder = data
            size = min(frames - cursor, len(self.remainder))
            outdata[cursor : cursor + size, 0] = np.clip(
                self.remainder[:size] * self.volume, -0.98, 0.98
            )
            self.remainder = self.remainder[size:]
            cursor += size

    def state(self, channel):
        now = time.monotonic()
        with self.lock:
            fresh = {s: v for (c, s), v in self.meters.items() if c == channel and now - v[0] < 0.8}
            level = max((v[1] for v in fresh.values()), default=-120)
            label = self.stream_labels.get((channel, self.stream_choice or ""), "Ses bekleniyor")
        return {
            "audio_dbfs": round(level, 1),
            "audio_present": level > -65,
            "audio_stream_count": len(fresh),
            "monitor_stream": label,
        }

    def clear(self):
        with self.lock:
            self.meters.clear()
            self.stream_labels.clear()
