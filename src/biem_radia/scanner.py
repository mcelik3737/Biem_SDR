from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScanGate:
    threshold: float
    dwell: float = 1.0
    release: float = 1.0
    elapsed: float = 0.0
    quiet: float = 0.0
    held: bool = False

    def advance(self, level: float, seconds: float) -> bool:
        """True means move on; every above-threshold block restarts quiet time."""
        self.elapsed += seconds
        if level >= self.threshold:
            self.held = True
            self.quiet = 0.0
            return False
        self.quiet += seconds
        return self.quiet >= self.release if self.held else self.elapsed >= self.dwell


@dataclass
class TetraScanGate(ScanGate):
    no_voice: float = 0.0
    reason: str = ""

    def advance_tetra(self, level: float, seconds: float, voice: bool, control: bool) -> bool:
        self.no_voice = 0.0 if voice else self.no_voice + seconds
        move = super().advance(level, seconds)
        if voice:
            return False
        if control and self.no_voice >= 2.0:
            self.reason = "Kontrol kanalı bilgisi alındı"
            return True
        if self.no_voice >= 20.0:
            self.reason = "20 sn boyunca çözülen ses yok"
            return True
        return move


@dataclass
class DmrScanGate(ScanGate):
    color_code: int | None = None

    def advance_dmr(self, level: float, seconds: float, color_code: int | None) -> bool:
        self.elapsed += seconds
        valid = color_code is not None and 0 <= color_code <= 15
        if (
            valid
            and level >= self.threshold
            and (self.color_code is None or self.color_code == color_code)
        ):
            self.color_code = color_code
            self.held = True
            self.quiet = 0.0
            return False
        self.quiet += seconds
        # Allow the asynchronous decoder time to report synchronization.
        return self.quiet >= self.release if self.held else self.elapsed >= max(2.0, self.dwell)


@dataclass
class AutoScanGate(ScanGate):
    no_voice: float = 0.0

    def advance_auto(self, state, seconds):
        self.elapsed += seconds
        mode = state.get("detected_mode")
        valid = mode in ("DMR", "TETRA", "NFM") and state["level"] >= self.threshold
        self.no_voice = 0.0 if state.get("voice") else self.no_voice + seconds
        if mode == "TETRA" and not state.get("voice"):
            if self.no_voice >= 20 or (state.get("control_channel") and self.no_voice >= 2):
                return True
        if valid:
            self.held = True
            self.quiet = 0.0
            return False
        self.quiet += seconds
        # Digital probes and the conservative FM classifier need acquisition time.
        return self.quiet >= self.release if self.held else self.elapsed >= max(3.0, self.dwell)
