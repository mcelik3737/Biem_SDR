from datetime import datetime
from pathlib import Path


def recording_name(mode: str, started: datetime, duration: float, radio=None, group=None) -> str:
    stamp = started.astimezone().strftime("%Y-%m-%d_%H_%M_%S")
    length = f"{duration:.2f}sn"
    if mode == "NFM":
        return f"analog_{stamp}_{length}.wav"

    def identity(value):
        return str(value) if value is not None and str(value).isdigit() else "bilinmiyor"

    prefix = "" if mode == "DMR" else f"{mode.lower()}_"
    return f"{prefix}{identity(radio)}_{identity(group)}_{stamp}_{length}.wav"


def available_path(directory: Path, name: str) -> Path:
    """Never replace another call with an identical second and duration."""
    path = directory / name
    suffix = 2
    while path.exists() or path.with_name(path.name + ".radia").exists():
        path = directory / f"{Path(name).stem}_{suffix:02d}.wav"
        suffix += 1
    return path
