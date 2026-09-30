"""Install optional user-supplied XYZ data, independently of application binaries."""

import argparse
import hashlib
import json
import re
import shutil
import uuid
import zipfile
from pathlib import Path

from PIL import Image


def install(archive: Path, root: Path) -> Path:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", archive.stem)[:64]
    target = root / f"{slug}-{digest[:12]}"
    if (target / "manifest.json").exists():
        return target
    staging = root / f".incoming-{uuid.uuid4().hex}"
    staging.mkdir()
    levels: dict[int, int] = {}
    try:
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist()) > 2_000_000_000:
                raise ValueError("Harita paketi açıldığında 2 GB sınırını aşıyor.")
            for item in z.infolist():
                match = re.search(r"(?:^|/)(\d+)/(\d+)/(\d+)\.(png|jpg|jpeg)$", item.filename, re.I)
                if not match or item.is_dir():
                    continue
                level, x, y = map(int, match.group(1, 2, 3))
                if (
                    not (0 <= level <= 22 and 0 <= x < 2**level and 0 <= y < 2**level)
                    or item.file_size > 8_000_000
                ):
                    raise ValueError(f"Geçersiz karo: {item.filename}")
                destination = staging / "tiles" / str(level) / str(x) / f"{y}.{match[4].lower()}"
                destination.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as source, destination.open("xb") as out:
                    shutil.copyfileobj(source, out)
                with Image.open(destination) as image:
                    if image.size != (256, 256):
                        raise ValueError("256×256 XYZ parçaları gerekli.")
                    image.verify()
                levels[level] = levels.get(level, 0) + 1
        if not levels:
            raise ValueError("Pakette kullanılabilir XYZ görüntüsü bulunamadı.")
        manifest = {
            "format": "biem-xyz-v1",
            "name": archive.stem,
            "sha256": digest,
            "tile_count": sum(levels.values()),
            "levels": levels,
            "source": "Kullanıcının yerel harita paketi",
            "network": False,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8"
        )
        staging.rename(target)
        return target
    except Exception:
        # Preserve a failed import for diagnosis, never activate it without a manifest.
        raise


def main():
    parser = argparse.ArgumentParser(
        description="BİEM Radio Integrated Solution XYZ harita paketi yükle"
    )
    parser.add_argument("archive", type=Path)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(install(args.archive, args.project / "data/map-packs"))


if __name__ == "__main__":
    main()
