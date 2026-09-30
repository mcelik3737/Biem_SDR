"""Download a bounded EOX 2016 detail patch, without modifying the installed map.

Only the CC BY 4.0 2016 layer is requested. Viewing the installed patch is offline.
https://cloudless.eox.at/license-non-commercial
"""

import argparse
import io
import json
import math
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image

RADIUS = 20037508.342789244


def tile_xy(lon, lat, zoom=14):
    n = 2**zoom
    return (
        math.floor((lon + 180) / 360 * n),
        math.floor((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n),
    )


def fetch(root, x, y):
    path = root / "tiles" / "14" / str(x) / f"{y}.jpg"
    if path.exists():
        try:
            with Image.open(path) as picture:
                picture.load()
                if picture.size == (256, 256):
                    return
        except OSError:
            pass
    unit = 2 * RADIUS / 2**14
    params = dict(
        service="WMS",
        version="1.1.1",
        request="GetMap",
        layers="s2cloudless_3857",
        styles="",
        srs="EPSG:3857",
        bbox=f"{x * unit - RADIUS},{RADIUS - (y + 1) * unit},{(x + 1) * unit - RADIUS},{RADIUS - y * unit}",
        width=256,
        height=256,
        format="image/jpeg",
    )
    request = Request(
        "https://tiles.maps.eox.at/wms?" + urlencode(params),
        headers={"User-Agent": "BIEM-OfflineMap/1.1"},
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                data = response.read(1_000_001)
                if (
                    "image/jpeg" not in response.headers.get("Content-Type", "")
                    or len(data) > 1_000_000
                ):
                    raise ValueError("Unexpected map response")
            with Image.open(io.BytesIO(data)) as picture:
                picture.load()
                if picture.size != (256, 256):
                    raise ValueError("Unexpected tile dimensions")
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(".tmp")
            temp.write_bytes(data)
            temp.replace(path)
            time.sleep(0.15)
            return
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--bbox", type=float, nargs=4, required=True, metavar=("WEST", "SOUTH", "EAST", "NORTH")
    )
    args = parser.parse_args()
    west, south, east, north = args.bbox
    if not (25 <= west < east <= 45 and 35 <= south < north <= 43):
        parser.error("Use a bounded region within Turkey")
    x0, y0 = tile_xy(west, north)
    x1, y1 = tile_xy(east, south)
    todo = [
        (x, y)
        for x in range(x0 // 2 * 2, (x1 // 2 + 1) * 2)
        for y in range(y0 // 2 * 2, (y1 // 2 + 1) * 2)
    ]
    if len(todo) > 5000:
        parser.error("Maximum 5000 detail tiles per patch")
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < 1_000_000_000:
        raise RuntimeError("At least 1 GB free is required")
    print(f"Detail tiles: {len(todo)}", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for count, _ in enumerate(pool.map(lambda xy: fetch(root, *xy), todo, buffersize=3), 1):
            if count % 50 == 0:
                print(f"{count}/{len(todo)}", flush=True)
    # All four children must exist before publishing a parent; no blank map quadrants.
    for x, y in sorted({(x // 2, y // 2) for x, y in todo}):
        picture = Image.new("RGB", (512, 512))
        for dx in range(2):
            for dy in range(2):
                with Image.open(root / "tiles/14" / str(x * 2 + dx) / f"{y * 2 + dy}.jpg") as tile:
                    picture.paste(tile, (dx * 256, dy * 256))
        target = root / "tiles/13" / str(x) / f"{y}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        picture.resize((256, 256), Image.Resampling.LANCZOS).save(target, "JPEG", quality=92)
    files = list((root / "tiles").glob("*/*/*.jpg"))
    report = dict(
        bbox=args.bbox,
        detail_zoom=14,
        source_resolution_m=10,
        tile_count=len(files),
        bytes=sum(p.stat().st_size for p in files),
        source="https://cloudless.eox.at/license-non-commercial",
        license="CC BY 4.0",
        attribution="EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2016 & 2017)",
    )
    (root / "detail-patch.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), "utf-8"
    )
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
