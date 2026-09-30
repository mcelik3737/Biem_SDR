import json
import math
import sqlite3
import time
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from .locations import LocationReader
from .map_detail import MapDetail
from .satellite import SatelliteTiles, bounds
from .vector_map import COS39, VECTOR_NAME, VectorMap, Viewport, find_package
from .vector_worker import MapWorker


def project(lon: float, lat: float) -> tuple[float, float]:
    return lon * math.cos(math.radians(39)), -lat


class MapPanel(ttk.Frame):
    def __init__(self, parent, archive):
        super().__init__(parent, padding=12)
        self.reader = LocationReader(archive.root)
        self.last_poll = 0.0
        self.zoom = 1.0
        self.center = project(35, 39)
        self.drag_origin = None
        with Image.open(Path(__file__).parent / "assets/radio-marker.webp") as icon:
            self.radio_icon = icon.convert("RGBA")
        self.radio_photo = None
        self.radio_size = 0
        data = json.loads(
            (Path(__file__).parent / "assets/turkey-region.geojson").read_text("utf-8")
        )
        self.features = data["features"]
        self.detail_layer = MapDetail()
        self.vector = None
        self.vector_worker = None
        self.vector_view = None
        self.vector_ready = None
        self.vector_photo = None
        self.vector_stats = None
        self.vector_error = ""
        self.vector_after = None
        package = find_package(archive.root)
        if package:
            try:
                self.vector = VectorMap(package)
                self.vector_worker = MapWorker(self.vector)
            except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
                self.vector_error = f"Türkiye paketi açılamadı: {exc}"
        self.satellite = SatelliteTiles(archive.root / "map-import/googlemaps/googlemaps/satellite")
        self.tile_sets = {"Uydu (yerel paket)": self.satellite} if self.satellite.tiles else {}
        self.tile_credits = {}
        self.tile_resolution = {}
        self.satellite_levels = set()
        for manifest in sorted((archive.root / "map-packs").glob("*/manifest.json")):
            try:
                info = json.loads(manifest.read_text("utf-8"))
                if info.get("format") != "biem-xyz-v1":
                    continue
                tiles = SatelliteTiles(manifest.parent / "tiles")
                if tiles.tiles:
                    name = f"{info['name']} (paket)"
                    self.tile_sets[name] = tiles
                    self.tile_resolution[name] = float(info.get("source_resolution_m", 0))
                    self.tile_credits[name] = " • ".join(
                        str(info[key])
                        for key in ("description", "attribution", "license")
                        if info.get(key)
                    )
            except (OSError, ValueError, KeyError):
                continue
        self.base_map = tk.StringVar(
            master=self,
            value=VECTOR_NAME if self.vector else next(reversed(self.tile_sets), "Standart"),
        )
        if self.base_map.get() in self.tile_sets:
            self.satellite = self.tile_sets[self.base_map.get()]
        self.show_borders = tk.BooleanVar(master=self, value=True)
        self.show_cities = tk.BooleanVar(
            master=self, value=not self.base_map.get().endswith("(paket)")
        )
        self.show_grid = tk.BooleanVar(master=self, value=False)
        ttk.Label(self, text="Harita · Telsiz konumu", font=("Segoe UI", 16, "bold")).pack(
            anchor="w", pady=(0, 8)
        )
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(0, 10))
        ttk.Button(row, text="Türkiye", command=self.reset).pack(side="right", padx=4)
        ttk.Button(row, text="Son telsize yaklaş", command=self.focus_radio).pack(
            side="right", padx=4
        )
        ttk.Button(row, text="−", width=3, command=lambda: self.change_zoom(1 / 1.4)).pack(
            side="right"
        )
        ttk.Button(row, text="+", width=3, command=lambda: self.change_zoom(1.4)).pack(
            side="right", padx=4
        )
        ttk.Button(row, text="Paket alanı", command=self.focus_pack).pack(side="right", padx=4)
        self.summary = tk.StringVar(master=self, value="Konum mesajı bekleniyor")
        self.detail = tk.StringVar(master=self)
        ttk.Label(
            self, textvariable=self.summary, font=("Segoe UI", 12, "bold"), style="Muted.TLabel"
        ).pack(anchor="w")
        ttk.Label(self, textvariable=self.detail, wraplength=1050).pack(anchor="w", pady=(4, 10))
        layers = ttk.Frame(self)
        layers.pack(fill="x", pady=(0, 8))
        self.street_button = ttk.Button(
            layers,
            text="Sokak",
            width=11,
            padding=(14, 12),
            command=lambda: self.select_layer(False),
        )
        self.street_button.pack(side="left", padx=(0, 6))
        self.satellite_button = ttk.Button(
            layers,
            text="Uydu",
            width=11,
            padding=(14, 12),
            command=lambda: self.select_layer(True),
        )
        self.satellite_button.pack(side="left", padx=(0, 14))
        if not self.tile_sets:
            self.satellite_button.state(["disabled"])
        self.city_places = {p["name"]: p for p in self.detail_layer.places}
        self.city_name = tk.StringVar(master=self, value="Şehre yaklaş…")
        self.city_box = ttk.Combobox(
            layers,
            textvariable=self.city_name,
            state="readonly",
            width=16,
            values=sorted(self.city_places),
        )
        self.city_box.pack(side="left", padx=(0, 14))
        self.city_box.bind("<<ComboboxSelected>>", lambda event: self.focus_city())
        self.native_button = ttk.Button(
            layers,
            text="Uygun yakınlık",
            command=self.focus_native,
        )
        self.satellite_hint = tk.StringVar(master=self)
        self.satellite_hint_label = ttk.Label(
            self,
            textvariable=self.satellite_hint,
            style="Muted.TLabel",
            wraplength=1000,
        )
        toggles = ttk.Frame(self)
        toggles.pack(fill="x", pady=(0, 8))
        self.map_toggles = toggles
        for label, variable in [
            ("İl sınırları", self.show_borders),
            ("Şehir adları", self.show_cities),
            ("Koordinat ızgarası", self.show_grid),
        ]:
            ttk.Checkbutton(toggles, text=label, variable=variable, command=self.render).pack(
                side="left", padx=(0, 18)
            )
        ttk.Label(toggles, text="● Son konum", style="Muted.TLabel").pack(side="right")
        self.canvas = tk.Canvas(
            self, background="#dceef5", highlightthickness=1, highlightbackground="#c5d6e2"
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.render())
        self.canvas.bind(
            "<MouseWheel>", lambda event: self.change_zoom(1.3 if event.delta > 0 else 1 / 1.3)
        )
        self.canvas.bind("<ButtonPress-1>", self.drag_start)
        self.canvas.bind("<B1-Motion>", self.drag_move)
        self.map_credit = tk.StringVar(master=self)
        ttk.Label(
            self,
            textvariable=self.map_credit,
            style="Muted.TLabel",
            wraplength=1150,
        ).pack(anchor="w", pady=(7, 0))
        self.update_credit()
        self.refresh_labels()
        self.bind("<Destroy>", self.close_vector, add="+")
        if self.vector_worker:
            self.vector_after = self.after(80, self.poll_vector)

    def select_layer(self, satellite):
        if satellite and not self.tile_sets:
            return
        self.base_map.set(
            next(reversed(self.tile_sets))
            if satellite
            else VECTOR_NAME
            if self.vector
            else "Standart"
        )
        # Keep the coordinate and scale for direct comparison between the two layers.
        self.render()

    def focus_native(self):
        tiles = self.tile_sets.get(self.base_map.get())
        if tiles:
            native = tiles.native_scale_at(self.center[0] / COS39, -self.center[1])
            if native:
                self.zoom = max(1, min(8192, self.zoom * native / self.scale()))
                self.render()

    def update_layer_controls(self):
        selected = self.tile_sets.get(self.base_map.get())
        self.street_button.configure(style="TButton" if selected else "Primary.TButton")
        self.satellite_button.configure(style="Primary.TButton" if selected else "TButton")
        if selected is None:
            self.native_button.pack_forget()
            self.satellite_hint_label.pack_forget()
            return
        self.native_button.pack(side="left")
        level = selected.detail_at(self.center[0] / COS39, -self.center[1])
        if level is None:
            hint = "Bu konum için çevrimdışı uydu görüntüsü yok."
        else:
            metres = 156543.03392 * math.cos(math.radians(-self.center[1])) / 2**level
            resolution = max(metres, self.tile_resolution.get(self.base_map.get(), 0))
            hint = f"Uydu • Bu konumdaki ayrıntı yaklaşık {resolution:.0f} m • İnternet gerekmez"
            native = selected.native_scale_at(self.center[0] / COS39, -self.center[1])
            if native and self.scale() > native * 1.05:
                hint += " • Ayrıntı sınırı: görüntü büyütülüyor. Uygun yakınlık düğmesini kullanın."
        self.satellite_hint.set(hint)
        if not self.satellite_hint_label.winfo_manager():
            self.satellite_hint_label.pack(before=self.map_toggles, anchor="w", pady=(0, 8))

    def close_vector(self, event):
        if event.widget is not self:
            return
        if self.vector_worker:
            self.vector_worker.close()
        if self.vector_after:
            self.after_cancel(self.vector_after)
            self.vector_after = None

    def poll_vector(self):
        result = self.vector_worker.take_result() if self.vector_worker else None
        if result:
            view, rendered, error = result
            if view == self.vector_view:
                self.vector_error = error or ""
                if rendered:
                    picture, self.vector_stats = rendered
                    self.vector_photo = ImageTk.PhotoImage(picture, master=self.canvas)
                    self.vector_ready = view
                self.render()
        self.vector_after = self.after(80, self.poll_vector)

    def focus_city(self):
        place = self.city_places.get(self.city_name.get())
        if place:
            self.center = project(place["lon"], place["lat"])
            self.zoom = 1
            # Start at street scale; subsequent zoom is still controlled by the user.
            self.zoom = min(8192, 256 * 2**14 / (360 * COS39) / self.scale())
            self.render()

    def draw_vector(self):
        view = Viewport(
            self.canvas.winfo_width(),
            self.canvas.winfo_height(),
            self.center,
            self.scale(),
            labels=self.show_cities.get(),
            borders=self.show_borders.get(),
        )
        if view != self.vector_view and self.vector_worker:
            self.vector_view = view
            self.vector_error = ""
            self.vector_worker.submit(view)
        if self.vector_ready == view and self.vector_photo:
            self.canvas.create_image(0, 0, anchor="nw", image=self.vector_photo, tags="vector-map")
            return True
        self.canvas.create_text(
            16,
            20,
            anchor="w",
            tags="map-loading",
            fill="#174b78",
            text=self.vector_error or "Çevrimdışı sokak ayrıntıları hazırlanıyor…",
        )
        return False

    def update_credit(self):
        selected = self.tile_sets.get(self.base_map.get())
        if self.base_map.get() == VECTOR_NAME and self.vector:
            credit = (
                "Türkiye • © OpenStreetMap katkıcıları / Geofabrik • ODbL 1.0 • İnternet gerekmez"
            )
            credit += "\nVeri z0–14; daha yakın görünüm aynı veriyi büyütür. Ayrıntı OSM kapsamına bağlıdır."
            if self.vector_stats and self.vector_ready == self.vector_view:
                stats = self.vector_stats
                credit += f" • Görünen karolar: {stats['loaded']}/{stats['requested']}"
                if stats["loaded"] < stats["requested"]:
                    credit += " • Bu görünümün bir bölümü paket dışında."
            if self.vector_error:
                credit += " • " + self.vector_error
        elif selected is not None:
            self.satellite = selected
            levels = sorted(selected.by_level)
            credit = f"{self.base_map.get()} • {len(selected.tiles)} parça • z{levels[0]}–{levels[-1]} • Eksik ayrıntılarda alt seviye kullanılır."
            if self.tile_credits.get(self.base_map.get()):
                credit += "\n" + self.tile_credits[self.base_map.get()]
            if self.satellite_levels:
                credit += f" • Görünümdeki en yüksek ayrıntı: z{max(self.satellite_levels)}"
        else:
            credit = "Çevrimdışı standart harita • Natural Earth / Public Domain"
        self.map_credit.set(
            credit + "\nSon alınan konum gösterilir. Tekerlek: yakınlaştır • Sürükle: kaydır"
        )

    def focus_pack(self):
        if self.base_map.get() == VECTOR_NAME:
            self.reset()
            return
        tiles = self.tile_sets.get(self.base_map.get())
        if not tiles or not tiles.tiles:
            return
        level = max(tiles.by_level)
        x0, y0, x1, y1 = tiles.level_bounds[level]
        west, _, _, north = bounds(level, x0, y0)
        _, south, east, _ = bounds(level, x1, y1)
        self.center = project((west + east) / 2, (south + north) / 2)
        self.zoom = 1
        desired = min(
            self.canvas.winfo_width() / ((east - west) * math.cos(math.radians(39)) + 0.1),
            self.canvas.winfo_height() / (north - south + 0.1),
        )
        self.zoom = max(1, min(8192, desired / self.scale() * 0.9))
        self.render()

    def scale(self):
        return (
            max(1, min(self.canvas.winfo_width() / 18, self.canvas.winfo_height() / 9.5))
            * self.zoom
        )

    def screen(self, lon, lat):
        x, y = project(lon, lat)
        scale = self.scale()
        return (
            (x - self.center[0]) * scale + self.canvas.winfo_width() / 2,
            (y - self.center[1]) * scale + self.canvas.winfo_height() / 2,
        )

    def reset(self):
        self.center, self.zoom = project(35, 39), 1.0
        self.render()

    def focus_radio(self):
        if self.reader.latest:
            self.center = project(self.reader.latest["longitude"], self.reader.latest["latitude"])
            self.zoom = 5.0
            self.render()

    def change_zoom(self, factor):
        target = max(1, min(8192, self.zoom * factor))
        tiles = self.tile_sets.get(self.base_map.get())
        if tiles and factor > 1:
            native = tiles.native_scale_at(self.center[0] / COS39, -self.center[1])
            if native:
                # Allow modest enlargement; don't turn one source pixel into a huge blur.
                limit = self.zoom * native * 2 / self.scale()
                target = max(self.zoom, min(target, limit))
        self.zoom = target
        self.render()

    def drag_start(self, event):
        self.drag_origin = event.x, event.y, self.center

    def drag_move(self, event):
        if self.drag_origin:
            x, y, center = self.drag_origin
            self.center = (
                center[0] - (event.x - x) / self.scale(),
                center[1] - (event.y - y) / self.scale(),
            )
            self.render()

    def refresh_labels(self):
        point = self.reader.latest
        if not point:
            self.summary.set("Konum mesajı bekleniyor")
            self.detail.set(
                "Geçerli enlem ve boylam içeren bir DMR konum metni geldiğinde telsiz burada görünecek."
            )
            return
        age = max(
            0,
            (
                datetime.now(timezone.utc) - datetime.fromisoformat(point["observed_utc"])
            ).total_seconds(),
        )
        age_text = f"{int(age)} sn önce" if age < 60 else f"{int(age // 60)} dk önce"
        self.summary.set(
            f"Son konum • Telsiz {point['source_id']} • {point['latitude']:.6f}°, {point['longitude']:.6f}°"
        )
        self.detail.set(
            f"Alınma: {age_text}  |  Mesaj: {point.get('message_time', '—')}  |  CC {point.get('color_code', '—')}  |  Çözücü slotu {point.get('decoder_slot', '—')}  |  Hedef {point.get('target_id', '—')}  |  {point.get('channel', '')}"
        )

    def render(self):
        self.update_credit()
        self.update_layer_controls()
        canvas = self.canvas
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 10 or h < 10:
            return
        for feature in self.features:
            fill = "#f4f3e9" if feature["properties"]["turkey"] else "#e7ece2"
            for polygon in feature["geometry"]["coordinates"]:
                for i, ring in enumerate(polygon):
                    points = [self.screen(lon, lat) for lon, lat in ring]
                    if (
                        max(x for x, y in points) < 0
                        or min(x for x, y in points) > w
                        or max(y for x, y in points) < 0
                        or min(y for x, y in points) > h
                    ):
                        continue
                    canvas.create_polygon(
                        *[v for point in points for v in point],
                        fill=fill if i == 0 else "#dceef5",
                        outline="#9fae9d",
                        width=1,
                    )
        satellite = self.base_map.get() in self.tile_sets
        vector = self.base_map.get() == VECTOR_NAME and self.vector is not None
        vector_drawn = self.draw_vector() if vector else False
        if satellite:
            self.satellite_levels = self.satellite.render(self)
        if not vector_drawn:
            self.detail_layer.draw_land(self, satellite=satellite)
        canvas.tag_raise("map-loading")
        self.update_credit()
        if self.show_grid.get():
            for lon in range(24, 48, 2):
                x, _ = self.screen(lon, 39)
                canvas.create_line(x, 0, x, h, fill="#c8dce8", dash=(2, 8))
                if 20 < x < w - 20:
                    canvas.create_text(x, h - 12, text=f"{lon}° E", fill="#68879b")
            for lat in range(34, 46, 2):
                _, y = self.screen(35, lat)
                canvas.create_line(0, y, w, y, fill="#c8dce8", dash=(2, 8))
                if 15 < y < h - 25:
                    canvas.create_text(23, y - 8, text=f"{lat}° N", fill="#68879b")
        for lon, lat, label in [
            (35, 39, "T Ü R K İ Y E"),
            (35, 43, "KARADENİZ"),
            (31, 34.7, "AKDENİZ"),
            (28.1, 40.6, "Marmara Denizi"),
            (25.6, 38.6, "EGE DENİZİ"),
        ]:
            x, y = self.screen(lon, lat)
            if label != "T Ü R K İ Y E" or self.zoom < 1.8:
                canvas.create_text(
                    x, y, text=label, fill="#829b9b", font=("Segoe UI", 12, "italic")
                )
        if not vector_drawn:
            self.detail_layer.draw_cities(self)
        self.detail_layer.draw_scale(self)
        canvas.create_text(w - 26, 20, text="K", fill="#455c6c", font=("Segoe UI", 10, "bold"))
        canvas.create_line(w - 26, 54, w - 26, 32, arrow="last", fill="#455c6c", width=2)
        point = self.reader.latest
        if point:
            x, y = self.screen(point["longitude"], point["latitude"])
            if 0 <= x <= w and 0 <= y <= h:
                # Keep the coordinate anchor exact even when the radio body hits an edge.
                canvas.create_oval(
                    x - 17, y - 17, x + 17, y + 17, fill="#f1d8df", outline="#d8a8b6", tags="radio"
                )
                canvas.create_oval(
                    x - 3, y - 3, x + 3, y + 3, fill="#ae2447", outline="white", tags="radio"
                )
                # Scale gently with map zoom, keeping the photo usable at both extremes.
                icon_height = min(192, max(44, round(44 * math.sqrt(self.zoom))))
                if icon_height != self.radio_size:
                    icon_width = round(icon_height * self.radio_icon.width / self.radio_icon.height)
                    self.radio_photo = ImageTk.PhotoImage(
                        self.radio_icon.resize((icon_width, icon_height), Image.Resampling.LANCZOS),
                        master=canvas,
                    )
                    self.radio_size = icon_height
                anchor_y = max(min(h - 8, icon_height + 8), min(h - 8, y))
                if anchor_y != y:
                    canvas.create_line(x, y, x, anchor_y, fill="#ae2447", width=2, tags="radio")
                y = anchor_y
                canvas.create_image(
                    x, y, image=self.radio_photo, anchor="s", tags=("radio", "radio-photo")
                )
                photo_width = self.radio_photo.width() if self.radio_photo else 0
                tx = min(w - 208, max(12, x + photo_width / 2 + 12))
                ty = min(h - 78, max(12, y - 48))
                canvas.create_rectangle(
                    tx + 3, ty + 3, tx + 199, ty + 66, fill="#c5d0d4", outline="", tags="radio"
                )
                canvas.create_rectangle(
                    tx, ty, tx + 196, ty + 63, fill="white", outline="#c4cdd3", tags="radio"
                )
                canvas.create_rectangle(
                    tx, ty, tx + 4, ty + 63, fill="#ae2447", outline="", tags="radio"
                )
                canvas.create_text(
                    tx + 14,
                    ty + 18,
                    anchor="w",
                    text=f"Telsiz {point['source_id']}",
                    fill="#942240",
                    font=("Segoe UI", 11, "bold"),
                    tags="radio",
                )
                canvas.create_text(
                    tx + 14,
                    ty + 42,
                    anchor="w",
                    text=point.get("message_time", "Son alınan konum"),
                    fill="#586f7e",
                    font=("Segoe UI", 9),
                    tags="radio",
                )
            else:
                canvas.create_text(
                    w / 2,
                    22,
                    text="Son telsiz görünüm dışında — ‘Son telsize yaklaş’ düğmesini kullanın",
                    fill="#8e1939",
                )

    def poll(self):
        if time.monotonic() - self.last_poll < 1:
            return
        self.last_poll = time.monotonic()
        try:
            changed = self.reader.poll()
            self.refresh_labels()
            if changed:
                self.render()
        except OSError as exc:
            self.detail.set(f"Konum günlüğü okunamadı: {exc}")
