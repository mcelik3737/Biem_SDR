"""Offline cartographic detail; source geometries and labels are Natural Earth."""

import json
import math
from pathlib import Path

COS39 = math.cos(math.radians(39))


def scale_distance(pixels_per_km: float, target_pixels: float = 130) -> tuple[float, float]:
    """A 1/2/5 distance that fits the bar, including metre-scale street views."""
    target = target_pixels / pixels_per_km
    decade = 10 ** math.floor(math.log10(target))
    distance = max(value * decade for value in (1, 2, 5) if value * decade <= target)
    return distance, distance * pixels_per_km


def projected_geometry(geometry):
    polygons = (
        geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    )
    result = []
    for polygon in polygons:
        rings = [[(lon * COS39, -lat) for lon, lat in ring] for ring in polygon]
        outer = rings[0]
        bounds = (
            min(x for x, y in outer),
            min(y for x, y in outer),
            max(x for x, y in outer),
            max(y for x, y in outer),
        )
        result.append((bounds, rings))
    return result


def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


class MapDetail:
    def __init__(self):
        data = json.loads((Path(__file__).parent / "assets/turkey-detail.json").read_text("utf-8"))
        self.provinces = [(p["name"], projected_geometry(p["geometry"])) for p in data["provinces"]]
        self.lakes = [(p["name"], projected_geometry(p["geometry"])) for p in data["lakes"]]
        self.places = sorted(
            data["places"], key=lambda p: (p["name"] != "Ankara", -p["population"])
        )

    def draw_geometry(self, panel, geometry, fill, outline, tag):
        canvas = panel.canvas
        w, h, scale = canvas.winfo_width(), canvas.winfo_height(), panel.scale()
        cx, cy = panel.center
        view = (
            cx - w / (2 * scale),
            cy - h / (2 * scale),
            cx + w / (2 * scale),
            cy + h / (2 * scale),
        )
        for bounds, rings in geometry:
            if not overlaps(bounds, view):
                continue
            for i, ring in enumerate(rings):
                points = [
                    v for x, y in ring for v in ((x - cx) * scale + w / 2, (y - cy) * scale + h / 2)
                ]
                canvas.create_polygon(
                    *points,
                    fill=fill if i == 0 or not fill else "#dceef5",
                    outline=outline,
                    width=0.8,
                    tags=tag,
                )

    def draw_land(self, panel, satellite=False):
        colors = ["#f5f3e9", "#f0f2e6", "#f8f4e9", "#edf1e4", "#f3f0e3"]
        for i, (_, geometry) in enumerate(self.provinces):
            if satellite:
                if panel.show_borders.get():
                    self.draw_geometry(panel, geometry, "", "#e2d8bc", "province")
                continue
            fill = colors[i % len(colors)] if panel.show_borders.get() else "#f4f3e9"
            self.draw_geometry(
                panel, geometry, fill, "#bcc4b2" if panel.show_borders.get() else fill, "province"
            )
        for _, geometry in self.lakes:
            if satellite:
                continue
            self.draw_geometry(panel, geometry, "#badbe9", "#91bdd0", "lake")

    def draw_cities(self, panel):
        if not panel.show_cities.get():
            return
        canvas = panel.canvas
        w, h = canvas.winfo_width(), canvas.winfo_height()
        occupied = []
        if panel.reader.latest:
            point = panel.reader.latest
            x, y = panel.screen(point["longitude"], point["latitude"])
            occupied.append((x - 25, y - 60, x + 205, y + 40))
        for place in self.places:
            if panel.zoom < 1.8 and place["population"] < 250000 and place["name"] != "Ankara":
                continue
            x, y = panel.screen(place["lon"], place["lat"])
            if not (18 < x < w - 90 and 20 < y < h - 50):
                continue
            capital = place["name"] == "Ankara"
            label = canvas.create_text(
                x + 7,
                y - 2,
                anchor="w",
                text=place["name"],
                fill="#334c5b",
                font=("Segoe UI", 10 if panel.zoom < 2 else 11, "bold" if capital else "normal"),
                tags="city",
            )
            bounds = canvas.bbox(label)
            if bounds is None:
                continue
            box = (bounds[0] - 4, bounds[1] - 3, bounds[2] + 5, bounds[3] + 3)
            if any(overlaps(box, other) for other in occupied):
                canvas.delete(label)
                continue
            occupied.append(box)
            background = canvas.create_rectangle(*box, fill="#f6f5ed", outline="", tags="city")
            canvas.tag_lower(background, label)
            r = 4 if capital else 2.5
            canvas.create_oval(
                x - r, y - r, x + r, y + r, fill="#51657a", outline="white", tags="city"
            )
            if capital:
                canvas.create_oval(
                    x - 1, y - 1, x + 1, y + 1, fill="white", outline="", tags="city"
                )

    def draw_scale(self, panel):
        canvas = panel.canvas
        h = canvas.winfo_height()
        # Equirectangular local scale at the current map center latitude.
        latitude = -panel.center[1]
        pixels_per_km = (
            panel.scale() * COS39 / (111.32 * max(0.1, math.cos(math.radians(latitude))))
        )
        distance, length = scale_distance(pixels_per_km)
        label = f"{distance * 1000:g} m" if distance < 1 else f"{distance:g} km"
        canvas.create_rectangle(
            12, h - 56, max(180, length + 42), h - 10, fill="white", outline="#cfdae0", tags="scale"
        )
        canvas.create_line(26, h - 25, 26 + length, h - 25, fill="#455c6c", width=3, tags="scale")
        for x in (26, 26 + length):
            canvas.create_line(x, h - 30, x, h - 21, fill="#455c6c", width=2, tags="scale")
        canvas.create_text(
            26,
            h - 42,
            anchor="w",
            text=f"Yaklaşık {label}",
            fill="#455c6c",
            font=("Segoe UI", 9),
            tags="scale",
        )
