"""Offline Shortbread MBTiles rendering, independent of the SDR receiver.

Geometries use the existing map canvas projection so radio anchors remain exact.
All file reading and drawing can run in a worker; no Tk objects are accessed here.
"""

import gzip
import io
import json
import math
import sqlite3
from collections import OrderedDict
from contextlib import closing
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import mapbox_vector_tile
from PIL import Image, ImageDraw, ImageFont

from .satellite import latitude, tile_y

COS39 = math.cos(math.radians(39))
VECTOR_NAME = "Türkiye • çevrimdışı sokak haritası"


@dataclass(frozen=True)
class Viewport:
    width: int
    height: int
    center: tuple[float, float]
    scale: float
    labels: bool = True
    borders: bool = True

    def screen(self, lon, lat):
        return (
            (lon * COS39 - self.center[0]) * self.scale + self.width / 2,
            (-lat - self.center[1]) * self.scale + self.height / 2,
        )

    def coordinates(self, x, y):
        return (
            (self.center[0] + (x - self.width / 2) / self.scale) / COS39,
            -self.center[1] - (y - self.height / 2) / self.scale,
        )

    @property
    def display_zoom(self):
        return math.log2(max(1, self.scale * COS39 * 360 / 256))


def visible_tiles(view, max_zoom=14):
    z = min(max_zoom, max(0, math.floor(view.display_zoom)))
    west, north = view.coordinates(0, 0)
    east, south = view.coordinates(view.width, view.height)
    n = 2**z
    x0, x1 = (
        max(0, math.floor((west + 180) / 360 * n)),
        min(n - 1, math.floor((east + 180) / 360 * n)),
    )
    y0, y1 = max(0, math.floor(tile_y(north, z))), min(n - 1, math.floor(tile_y(south, z)))
    return [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def find_package(data_root):
    """Only explicitly installed packages; no machine-specific path fallback."""
    for manifest in sorted((data_root / "map-packs").glob("*/manifest.json"), reverse=True):
        try:
            info = json.loads(manifest.read_text("utf-8"))
            if info.get("format") != "biem-shortbread-mbtiles-v1":
                continue
            filename = info["filename"]
            if Path(filename).name != filename or not filename.endswith(".mbtiles"):
                continue
            path = manifest.parent / filename
            if path.is_file():
                return path
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return None


@lru_cache(maxsize=4)
def label_font(size):
    for name in ("segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


class VectorMap:
    def __init__(self, path):
        self.path = path.resolve()
        self.cache = OrderedDict()
        with self.connection() as db:
            meta = dict(db.execute("SELECT name,value FROM metadata"))
        if meta.get("format") != "pbf":
            raise ValueError("Vektör PBF harita paketi gerekli")
        layers = json.loads(meta["json"])["vector_layers"]
        if not {"streets", "place_labels", "buildings"}.issubset({p["id"] for p in layers}):
            raise ValueError("Shortbread yol haritası katmanları eksik")
        self.max_zoom = min(14, int(meta["maxzoom"]))
        self.bounds = tuple(map(float, meta["bounds"].split(",")))

    def connection(self):
        return closing(sqlite3.connect(self.path.as_uri() + "?mode=ro&immutable=1", uri=True))

    def tile(self, db, z, x, y):
        key = z, x, y
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        row = db.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, 2**z - 1 - y),
        ).fetchone()
        decoded = {}
        if row:
            data = row[0]
            if data[:2] == b"\x1f\x8b":
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as source:
                    data = source.read(16_000_001)
            if len(data) > 16_000_000:
                raise ValueError("Harita karosu boyut sınırını aşıyor")
            decoded = mapbox_vector_tile.decode(data, default_options={"y_coord_down": True})
            # Do not retain bulky layers which this renderer does not use.
            decoded = {k: v for k, v in decoded.items() if k in LAYERS}
        self.cache[key] = decoded
        while len(self.cache) > 20:
            self.cache.popitem(last=False)
        return decoded

    def render(self, view, cancelled=lambda: False):
        image = Image.new("RGB", (view.width, view.height), "#f3f1eb")
        draw = ImageDraw.Draw(image)
        requested = visible_tiles(view, self.max_zoom)
        if len(requested) > 64:
            raise ValueError("Harita görünümü çok geniş")
        tiles = []
        with self.connection() as db:
            for z, x, y in requested:
                if cancelled():
                    return None
                data = self.tile(db, z, x, y)
                if data:
                    tiles.append((z, x, y, data))
        counts = {}
        labels = []
        for layer in LAYERS:
            if layer == "boundaries" and not view.borders:
                continue
            if layer in LABELS and not view.labels:
                continue
            if layer == "buildings" and view.display_zoom < 13:
                continue
            for z, x, y, data in tiles:
                content = data.get(layer)
                if not content:
                    continue
                extent = content["extent"]

                def transform(point, z=z, x=x, y=y, extent=extent):
                    lon = (x + point[0] / extent) / 2**z * 360 - 180
                    lat = latitude(y + point[1] / extent, z)
                    return view.screen(lon, lat)

                for i, feature in enumerate(content["features"]):
                    if i % 128 == 0 and cancelled():
                        return None
                    geometry = feature["geometry"]
                    props = feature["properties"]
                    kind, coords = geometry["type"], geometry["coordinates"]
                    counts[layer] = counts.get(layer, 0) + 1
                    if layer in LABELS:
                        text = props.get("name") or props.get("name_en")
                        if not text or len(text) > 90:
                            continue
                        if kind == "Point":
                            point = transform(coords)
                        elif kind == "LineString" and coords and view.display_zoom >= 14:
                            point = transform(coords[len(coords) // 2])
                        else:
                            continue
                        priority = 0 if layer == "place_labels" else 1
                        population = float(props.get("population", 0))
                        labels.append((priority, -population, str(text), point))
                    elif kind in ("Polygon", "MultiPolygon"):
                        color = polygon_color(layer, props.get("kind"))
                        polygons = coords if kind == "MultiPolygon" else [coords]
                        for polygon in polygons:
                            rings = [[transform(point) for point in ring] for ring in polygon]
                            paint_polygon(image, draw, rings, color)
                    elif kind in ("LineString", "MultiLineString"):
                        color, width = line_style(layer, props, view.display_zoom)
                        lines = coords if kind == "MultiLineString" else [coords]
                        for line in lines:
                            points = [transform(point) for point in line]
                            if len(points) >= 2:
                                draw.line(points, fill=color, width=width, joint="curve")
        occupied = []
        labeled = set()
        for priority, _, text, (x, y) in sorted(labels):
            if not (12 <= x < view.width - 12 and 12 <= y < view.height - 12):
                continue
            cell = (text, round(x / 180), round(y / 180))
            if cell in labeled:
                continue
            font = label_font(13 if priority == 0 else 11)
            box = draw.textbbox((x, y), text, font=font, anchor="mm", stroke_width=2)
            box = (box[0] - 4, box[1] - 3, box[2] + 4, box[3] + 3)
            if any(
                box[0] < r[2] and box[2] > r[0] and box[1] < r[3] and box[3] > r[1]
                for r in occupied
            ):
                continue
            draw.text(
                (x, y),
                text,
                font=font,
                anchor="mm",
                fill="#33485c",
                stroke_width=2,
                stroke_fill="#f7f6f0",
            )
            occupied.append(box)
            labeled.add(cell)
        return image, {
            "requested": len(requested),
            "loaded": len(tiles),
            "zoom": requested[0][0] if requested else 0,
            "features": counts,
        }


LAYERS = (
    "land",
    "sites",
    "ocean",
    "water_polygons",
    "water_lines",
    "boundaries",
    "buildings",
    "street_polygons",
    "streets",
    "ferries",
    "pier_lines",
    "place_labels",
    "water_polygons_labels",
    "street_labels",
    "streets_polygons_labels",
)
LABELS = {"place_labels", "water_polygons_labels", "street_labels", "streets_polygons_labels"}


def polygon_color(layer, kind):
    if layer in ("ocean", "water_polygons"):
        return "#bcdae6"
    if layer == "buildings":
        return "#d5c9bd"
    if layer == "street_polygons":
        return "#faf9f5"
    if kind in ("forest", "wood", "grass", "park", "grassland", "meadow"):
        return "#d8e4cd"
    if kind in ("sand", "beach"):
        return "#f1e7c7"
    return "#e8e4de"


def line_style(layer, props, zoom):
    if layer == "boundaries":
        return "#b48a9b", 1
    if layer in ("water_lines", "ferries"):
        return "#95becc", max(1, round((zoom - 8) / 3))
    if props.get("rail"):
        return "#8a96a1", 1
    major = props.get("kind") in ("motorway", "trunk", "primary", "secondary")
    return ("#dfa86e" if major else "#ffffff"), max(1, round((zoom - 7) * (0.6 if major else 0.35)))


def paint_polygon(image, draw, rings, color):
    if not rings or len(rings[0]) < 3:
        return
    x0 = max(0, math.floor(min(p[0] for p in rings[0])))
    y0 = max(0, math.floor(min(p[1] for p in rings[0])))
    x1 = min(image.width, math.ceil(max(p[0] for p in rings[0])) + 1)
    y1 = min(image.height, math.ceil(max(p[1] for p in rings[0])) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    if len(rings) == 1:
        draw.polygon(rings[0], fill=color)
        return
    # Preserve underlying pixels in holes, including islands within water polygons.
    mask = Image.new("L", (x1 - x0, y1 - y0))
    pen = ImageDraw.Draw(mask)
    for i, ring in enumerate(rings):
        if len(ring) >= 3:
            pen.polygon([(x - x0, y - y0) for x, y in ring], fill=255 if i == 0 else 0)
    image.paste(color, (x0, y0, x1, y1), mask)
