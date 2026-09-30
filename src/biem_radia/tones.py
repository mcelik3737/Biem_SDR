"""Receive-only selective squelch on unfiltered FM discriminator samples."""

import numpy as np
from scipy import signal

CTCSS = (
    67.0,
    69.3,
    71.9,
    74.4,
    77.0,
    79.7,
    82.5,
    85.4,
    88.5,
    91.5,
    94.8,
    97.4,
    100.0,
    103.5,
    107.2,
    110.9,
    114.8,
    118.8,
    123.0,
    127.3,
    131.8,
    136.5,
    141.3,
    146.2,
    151.4,
    156.7,
    159.8,
    162.2,
    165.5,
    167.9,
    171.3,
    173.8,
    177.3,
    179.9,
    183.5,
    186.2,
    189.9,
    192.8,
    196.6,
    199.5,
    203.5,
    206.5,
    210.7,
    218.1,
    225.7,
    229.1,
    233.6,
    241.8,
    250.3,
    254.1,
)
DCS = tuple(
    "023 025 026 031 032 036 043 047 051 053 054 065 071 072 073 074 114 115 116 122 125 131 132 134 143 145 152 155 156 162 165 172 174 205 212 223 225 226 243 244 245 246 251 252 255 261 263 265 266 271 274 306 311 315 325 331 332 343 346 351 356 364 365 371 411 412 413 423 431 432 445 446 452 454 455 462 464 465 466 503 506 516 523 526 532 546 565 606 612 624 627 631 632 654 662 664 703 712 723 731 732 734 743 754".split()
)


def dcs_bits(code: str) -> np.ndarray:
    # Golay DCS parity matrix, bit order: code LSB, fixed 001, parity LSB.
    # Matrix reference: SDRangel NFMModDCS::setDCS.
    value = int(code, 8)
    masks = (0x9F, 0x13E, 0xE3, 0x1C6, 0x113, 0xB9, 0x1ED, 0x1DA, 0x1B4, 0x168, 0x4F)
    invert = (0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1)
    return np.array(
        [(value >> bit) & 1 for bit in range(9)]
        + [0, 0, 1]
        + [((value & mask).bit_count() + inv) % 2 for mask, inv in zip(masks, invert, strict=True)]
    )


class ToneGate:
    def __init__(self, mode="CSQ", value="67.0"):
        self.mode, self.value = mode, value
        self.open = mode == "CSQ"
        self.label = "CSQ" if self.open else "Ton bekleniyor"
        self.sos = np.asarray(
            signal.butter(
                4,
                [40, 280] if mode == "CTCSS" else 280,
                btype="bandpass" if mode == "CTCSS" else "lowpass",
                fs=48000,
                output="sos",
            )
        )
        self.state = np.zeros((len(self.sos), 2))
        self.position = 0
        self.samples = np.zeros(0)
        self.since_check = 0

    def feed(self, hz: np.ndarray) -> bool:
        if self.mode == "CSQ":
            return True
        filtered, self.state = signal.sosfilt(self.sos, hz, zi=self.state)
        down = filtered[(-self.position) % 40 :: 40]
        self.position += len(hz)
        self.samples = np.concatenate((self.samples, down))[-720:]
        self.since_check += len(down)
        if len(self.samples) < 600 or self.since_check < 120:
            return self.open
        self.since_check = 0
        x = self.samples - self.samples.mean()
        power = float(np.mean(x * x))
        self.open = False
        if power > 4:
            if self.mode == "CTCSS":
                t = np.arange(len(x)) / 1200
                strengths = np.abs(np.exp(-2j * np.pi * np.array(CTCSS)[:, None] * t) @ x) ** 2
                best = int(np.argmax(strengths))
                self.open = (
                    CTCSS[best] == float(self.value)
                    and 2 * strengths[best] / len(x) ** 2 > power * 0.6
                )
            else:
                bits = dcs_bits(self.value)
                if self.mode == "DCS-I":
                    bits = 1 - bits
                # Search symbol timing and word rotation. Require two full words,
                # each with at most one differing bit; no polarity auto-swap.
                for rate in (134.3, 134.4):
                    for phase in np.linspace(0, 1200 / rate, 12, endpoint=False):
                        indexes = np.arange(phase, len(x), 1200 / rate).astype(int)
                        observed = x[indexes] > 0
                        for offset in range(23):
                            if len(observed) < offset + 46:
                                continue
                            errors = np.count_nonzero(
                                observed[offset : offset + 46].reshape(2, 23) != bits, axis=1
                            )
                            if np.all(errors <= 1):
                                self.open = True
                                break
                        if self.open:
                            break
                    if self.open:
                        break
        self.label = f"{self.mode} {self.value}" + (" ✓" if self.open else " • eşleşmedi")
        return self.open
