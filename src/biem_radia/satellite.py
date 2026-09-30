"""Local XYZ tiles reprojected to the dispatcher's geographic canvas. No network IO."""

import json
import math
import re
from collections import OrderedDict
from pathlib import Path

from PIL import Image, ImageTk


def latitude(y: float, zoom: int) -> float:
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / (2**zoom)))))


def tile_y(lat: float, zoom: int) -> float:
    lat = max(-85.05112878, min(85.05112878, lat))
    return (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * (2**zoom)


def bounds(z: int, x: int, y: int):
    n = 2**z
    return x / n * 360 - 180, latitude(y + 1, z), (x + 1) / n * 360 - 180, latitude(y, z)


class SatelliteTiles:
    def __init__(self, root: Path):
        self.tiles: list[tuple[int, int, int, Path]] = []
        self.cache: OrderedDict[Path, Image.Image] = OrderedDict()
        self.images: list[ImageTk.PhotoImage] = []
        self.errors: list[str] = []
        index = root.parent / "tile-index.json"
        paths = None
        if index.exists():
            try:
                entries = json.loads(index.read_text("utf-8"))
                paths = []
                for z, x, y, relative in entries:
                    if relative != f"{int(z)}/{int(x)}/{int(y)}.png" and not re.fullmatch(
                        r"content/[0-9a-f]{64}\.png", relative
                    ):
                        raise ValueError("Geçersiz karo indeksi")
                    z, x, y = int(z), int(x), int(y)
                    if not (0 <= z <= 22 and 0 <= x < 2**z and 0 <= y < 2**z):
                        raise ValueError("Geçersiz XYZ koordinatı")
                    self.tiles.append((z, x, y, root / relative))
            except (OSError, ValueError, TypeError):
                paths = None
                self.tiles.clear()
        for path in paths if paths is not None else sorted(root.glob("*/*/*")):
            if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            try:
                z, x, y = int(path.parent.parent.name), int(path.parent.name), int(path.stem)
                if not (0 <= z <= 22 and 0 <= x < 2**z and 0 <= y < 2**z):
                    continue
                self.tiles.append((z, x, y, path))
            except (ValueError, OSError) as exc:
                self.errors.append(f"{path.name}: {exc}")
        self.tiles.sort(key=lambda t: t[:3])
        self.by_level: dict[int, dict[tuple[int, int], Path]] = {}
        for z, x, y, path in self.tiles:
            self.by_level.setdefault(z, {})[x, y] = path
        self.level_bounds = {
            z: (
                min(x for x, y in tiles),
                min(y for x, y in tiles),
                max(x for x, y in tiles),
                max(y for x, y in tiles),
            )
            for z, tiles in self.by_level.items()
        }

    def visible_tiles(self, panel, desired):
        scale = panel.scale()
        cosine = math.cos(math.radians(39))
        west = (panel.center[0] - panel.canvas.winfo_width() / (2 * scale)) / cosine
        east = (panel.center[0] + panel.canvas.winfo_width() / (2 * scale)) / cosine
        north = -panel.center[1] + panel.canvas.winfo_height() / (2 * scale)
        south = -panel.center[1] - panel.canvas.winfo_height() / (2 * scale)
        for z, tiles in sorted(self.by_level.items()):
            if z > desired:
                break
            n = 2**z
            x0 = max(0, math.floor((west + 180) / 360 * n))
            x1 = min(n - 1, math.floor((east + 180) / 360 * n))
            y0 = max(0, math.floor(tile_y(north, z)))
            y1 = min(n - 1, math.floor(tile_y(south, z)))
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    path = tiles.get((x, y))
                    if path is not None:
                        yield z, x, y, path

    def load(self, path):
        if path not in self.cache:
            with Image.open(path) as image:
                if image.size != (256, 256):
                    raise ValueError("256×256 karo gerekli")
                self.cache[path] = image.convert("RGBA")
            while len(self.cache) > 128:
                self.cache.popitem(last=False)
        self.cache.move_to_end(path)
        return self.cache[path]

    def render(self, panel):
        self.images.clear()
        w, h = panel.canvas.winfo_width(), panel.canvas.winfo_height()
        used = set()
        # Draw coarse coverage first, then overwrite with available finer tiles.
        # Choose a native level for current pixel density; coarser levels fill gaps.
        desired = max(
            0, math.ceil(math.log2(panel.scale() * math.cos(math.radians(39)) * 360 / 256))
        )
        for z, x, y, path in self.visible_tiles(panel, desired):
            west, south, east, north = bounds(z, x, y)
            left, top = panel.screen(west, north)
            right, bottom = panel.screen(east, south)
            x0, y0 = max(0, math.floor(left)), max(0, math.floor(top))
            x1, y1 = min(w, math.ceil(right)), min(h, math.ceil(bottom))
            width, height = x1 - x0, y1 - y0
            if width <= 0 or height <= 0 or right <= left or bottom <= top:
                continue
            try:
                image = self.load(path)
            except (OSError, ValueError) as exc:
                if str(exc) not in self.errors:
                    self.errors.append(str(exc))
                continue
            sx0 = (x0 - left) / (right - left) * 256
            sx1 = (x1 - left) / (right - left) * 256
            sx0, sx1 = max(0.0, min(255.0, sx0)), max(0.0, min(255.0, sx1))
            mesh = []
            # Geographic Y is linear in latitude; tile Y is Web Mercator.
            # Small strips preserve coordinate alignment across each image.
            for row in range(0, height, 8):
                end = min(height, row + 8)
                lat_top = north + (y0 + row - top) / (bottom - top) * (south - north)
                lat_bottom = north + (y0 + end - top) / (bottom - top) * (south - north)
                sy0, sy1 = (tile_y(lat_top, z) - y) * 256, (tile_y(lat_bottom, z) - y) * 256
                sy0, sy1 = max(0.0, min(255.0, sy0)), max(0.0, min(255.0, sy1))
                mesh.append(((0, row, width, end), (sx0, sy0, sx0, sy1, sx1, sy1, sx1, sy0)))
            raster = image.transform(
                (width, height), Image.Transform.MESH, mesh, Image.Resampling.BILINEAR
            )
            photo = ImageTk.PhotoImage(raster, master=panel.canvas)
            self.images.append(photo)
            panel.canvas.create_image(x0, y0, image=photo, anchor="nw", tags="satellite")
            used.add(z)
        return used
