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
