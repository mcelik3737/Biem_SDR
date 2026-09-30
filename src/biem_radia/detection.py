"""Conservative, receive-only protocol evidence. Never changes RF tuning."""

import re
import time
from collections import deque

import numpy as np


class ProtocolEvidence:
    """Require repeated decoder evidence; never infer a manufacturer from DMR sync."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.hits = {name: deque(maxlen=12) for name in ("DMR", "TETRA", "XPT")}
        self.codes: dict[str, int] = {}
        self.confirmed: set[str] = set()
        self.last_digital = float("-inf")

    def hit(self, protocol, code):
        now = self.clock()
        if self.codes.get(protocol) != code:
            self.hits[protocol].clear()
            if protocol == "DMR":
                self.hits["XPT"].clear()
        self.codes[protocol] = code
        self.hits[protocol].append(now)
        self.last_digital = now
        if self.fresh(protocol):
            self.confirmed.add(protocol)

    def fresh(self, protocol):
        now = self.clock()
        hits = self.hits[protocol]
        needed = 2 if protocol == "XPT" else 3
        return sum(now - stamp <= 1.5 for stamp in hits) >= needed

    def observe_dmr(self, line):
        # Verbose AMBE output includes 'err = [0] [0]' on successful frames.
        # Only decoder sync/FEC/CRC failures invalidate the protocol candidate.
        if re.search(
            r"(?:CRC|FEC|CACH).*?\b(?:ERR\w*|FAIL\w*)\b|Sync:.*\b(?:ERR\w*|FAIL\w*)\b|no sync",
            line,
            re.I,
        ):
            self.hits["DMR"].clear()
            self.hits["XPT"].clear()
            return
        if "Sync:" in line and re.search(r"[+-]DMR\b", line):
            match = re.search(r"Color Code=(\d+)\b", line)
            if match and 0 <= int(match[1]) <= 15:
                self.hit("DMR", int(match[1]))
        # These exact messages are inside the CRC-correct CSBK branch in
        # the pinned DSD-FME source. Help text or a bare 'XPT' is not evidence.
        if self.fresh("DMR") and re.search(
            r"Hytera XPT (?:Site Status - Free LCN:|CSBK 0x0B - SN:)", line
        ):
            self.hit("XPT", self.codes["DMR"])

    def observe_tetra(self, event):
        if event.get("errors") is not False:
            self.hits["TETRA"].clear()
            return
        code = event.get("sync", {}).get("ColorCode")
        # The bridge emits only received bursts. Require decoded data as well
        # as sync, because sync fields may persist from an earlier burst.
        data_valid = any(event.get("data", []))
        voice_continuation = (
            "TETRA" in self.confirmed
            and self.codes.get("TETRA") == code
            and event.get("slot") in (1, 2, 3, 4)
            and bool(event.get("pcm"))
        )
        if isinstance(code, int) and 0 <= code <= 63 and (data_valid or voice_continuation):
            self.hit("TETRA", code)

    def digital_mode(self):
        dmr, tetra = self.fresh("DMR"), self.fresh("TETRA")
        if dmr and tetra:
            return "CONFLICT"
        return "DMR" if dmr else "TETRA" if tetra else None

    def label(self, mode):
        if mode == "DMR":
            return (
                "DMR / Hytera XPT"
                if self.fresh("XPT") and self.codes.get("XPT") == self.codes.get("DMR")
                else "DMR"
            )
        return {"NFM": "Analog FM (olası)", "CONFLICT": "Çakışan dijital kanıt"}.get(
            mode, mode or "Bilinmiyor / yayın bekleniyor"
        )


def fm_voice_candidate(hz):
    """Positive FM audio evidence, not 'digital decoding failed => analog'.

    This is deliberately a heuristic, not a universal modulation classifier.
    Reject broadband noise, an unmodulated carrier, FSK plateaus and common
    symbol clocks. Decoder evidence always overrides this result.
    """
    if len(hz) < 4800 or not np.all(np.isfinite(hz)):
        return False
    x = np.asarray(hz[-24000:], dtype=float)
    x = x - np.mean(x)
    rms = float(np.sqrt(np.mean(x * x)))
    if not 100 < rms < 3500:
        return False
    spectrum = abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    frequencies = np.fft.rfftfreq(len(x), 1 / 48000)
    voice = float(spectrum[(frequencies >= 250) & (frequencies <= 3000)].sum())
    total = float(spectrum[(frequencies >= 100) & (frequencies <= 12000)].sum())
    if voice / max(total, 1e-20) < 0.88:
        return False
    derivative = np.diff(x)
    clock_power = abs(np.fft.rfft(abs(derivative) * np.hanning(len(derivative)))) ** 2
    clock_freq = np.fft.rfftfreq(len(derivative), 1 / 48000)
    ac = float(clock_power[clock_freq > 100].sum())
    for symbol_rate in (2400, 4800):
        power = float(clock_power[abs(clock_freq - symbol_rate) < 25].sum())
        if power / max(ac, 1e-20) > 0.08:
            return False
    # Squared transitions expose the symbol clock even on pulse-shaped FSK,
    # whose discriminator spectrum can otherwise resemble band-limited speech.
    squared_power = abs(np.fft.rfft(derivative**2 * np.hanning(len(derivative)))) ** 2
    squared_ac = float(squared_power[clock_freq > 100].sum())
    for symbol_rate in (2400, 4800):
        if (
            float(squared_power[abs(clock_freq - symbol_rate) < 25].sum()) / max(squared_ac, 1e-20)
            > 0.01
        ):
            return False
    # Four equally spaced FSK levels sampled at each possible symbol phase.
    # This also blocks FSK for which a decoder is not available in Auto mode.
    for samples_per_symbol in (10, 20):
        for phase in range(samples_per_symbol):
            samples = x[phase::samples_per_symbol]
            scale = np.percentile(abs(samples), 85) / 3
            if scale < 50:
                continue
            normalized = samples / scale
            distance = np.min((normalized[:, None] - np.array([-3, -1, 1, 3])) ** 2, axis=1)
            if float(np.mean(distance)) < 0.18:
                return False
    return True


class AnalogEvidence:
    def __init__(self):
        self.samples = np.zeros(0)
        self.since_check = 0
        self.qualified_seconds = 0.0

    def feed(self, hz, allowed):
        if not allowed:
            self.samples = np.zeros(0)
            self.since_check = 0
            self.qualified_seconds = 0.0
            return False
        self.samples = np.concatenate((self.samples, hz))[-24000:]
        self.since_check += len(hz)
        if self.since_check >= 9600:
            seconds = self.since_check / 48000
            self.since_check = 0
            self.qualified_seconds = (
                self.qualified_seconds + seconds if fm_voice_candidate(self.samples) else 0.0
            )
        return self.qualified_seconds >= 2.0
