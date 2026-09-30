import json
import math
import tkinter as tk

from PIL import Image

from biem_radia.map_detail import scale_distance
from biem_radia.map_panel import MapPanel, project
from biem_radia.satellite import SatelliteTiles, bounds, latitude, tile_y
from biem_radia.storage import Archive


def test_xyz_bounds_and_mercator_inverse():
    west, south, east, north = bounds(4, 9, 6)
    assert west == 22.5 and east == 45
    assert abs(north - 40.979898) < 0.00001
    assert abs(south - 21.943046) < 0.00001
    assert west < 29.242599 < east and south < 40.881391 < north
    for z in range(1, 5):
        for lat in (0, 21.9, 40.88, 70):
            assert math.isclose(latitude(tile_y(lat, z), z), lat, abs_tol=1e-8)


def test_local_tiles_render_and_marker_alignment(tmp_path):
    directory = tmp_path / "map-import/googlemaps/googlemaps/satellite/4/9"
    directory.mkdir(parents=True)
    Image.new("RGB", (256, 256), (80, 100, 150)).save(directory / "6.jpg")
    x = int((29.242599 + 180) / 360 * 2**14)
    y = int(tile_y(40.881391, 14))
    detail = directory.parents[1] / "14" / str(x) / f"{y}.jpg"
    detail.parent.mkdir(parents=True)
    Image.new("RGB", (256, 256), "beige").save(detail)
    assert len(SatelliteTiles(directory.parents[1]).tiles) == 2
    root = tk.Tk()
    root.withdraw()
    try:
        panel = MapPanel(root, Archive(tmp_path))
        panel.pack(fill="both", expand=True)
        root.geometry("1100x700")
        root.deiconify()
        root.update()
        assert panel.base_map.get() == "Uydu (yerel paket)"
        assert panel.canvas.find_withtag("satellite")
        assert panel.satellite.images
        before = panel.screen(29.242599, 40.881391)
        panel.base_map.set("Standart")
        panel.render()
        assert not panel.canvas.find_withtag("satellite")
        assert panel.screen(29.242599, 40.881391) == before
        # Actual touch controls retain location when switching layer.
        panel.satellite_button.invoke()
        assert panel.canvas.find_withtag("satellite")
        assert panel.satellite_button.cget("style") == "Primary.TButton"
        assert panel.screen(29.242599, 40.881391) == before
        panel.street_button.invoke()
        assert not panel.canvas.find_withtag("satellite")
        assert panel.street_button.cget("style") == "Primary.TButton"
        assert panel.screen(29.242599, 40.881391) == before
        # Prevent endless enlargement, while preserving a deliberately close street view.
        panel.satellite_button.invoke()
        panel.center = project(29.242599, 40.881391)
        panel.focus_native()
        native_zoom = panel.zoom
        panel.change_zoom(100)
        assert math.isclose(panel.zoom, native_zoom * 2)
        panel.change_zoom(2)
        assert math.isclose(panel.zoom, native_zoom * 2)
        assert "Ayrıntı sınırı" in panel.satellite_hint.get()
        panel.native_button.invoke()
        assert math.isclose(panel.zoom, native_zoom)
        assert "Ayrıntı sınırı" not in panel.satellite_hint.get()
    finally:
        root.destroy()


def test_indexed_pack_shares_images_and_culls_viewport(tmp_path):
    relative = "content/" + "a" * 64 + ".png"
    path = tmp_path / "tiles" / relative
    path.parent.mkdir(parents=True)
    Image.new("RGB", (256, 256), "beige").save(path)
    entries = [[17, 77000, y, relative] for y in range(50000, 51000)]
    (tmp_path / "tile-index.json").write_text(json.dumps(entries), "utf-8")
    tiles = SatelliteTiles(tmp_path / "tiles")
    assert len(tiles.tiles) == 1000
    assert tiles.level_bounds[17] == (77000, 50000, 77000, 50999)

    class Canvas:
        def winfo_width(self):
            return 1000

        def winfo_height(self):
            return 600

    class Panel:
        canvas = Canvas()
        west, south, east, north = bounds(17, 77000, 50500)
        center = project((west + east) / 2, (north + south) / 2)

        def scale(self):
            return 100000

    visible = list(tiles.visible_tiles(Panel(), 17))
    assert 1 <= len(visible) < 10
    assert (17, 77000, 50500, path) in visible
    assert list(tiles.visible_tiles(Panel(), 16)) == []
    assert tiles.load(path).size == (256, 256)


def test_index_cannot_reference_outside_pack(tmp_path):
    (tmp_path / "tile-index.json").write_text(json.dumps([[1, 0, 0, "../../outside.png"]]), "utf-8")
    assert SatelliteTiles(tmp_path / "tiles").tiles == []


def test_local_detail_and_corrupt_tile_fallback(tmp_path):
    lon, lat = 29.242599, 40.881391
    paths = []
    for level in (12, 14):
        x = int((lon + 180) / 360 * 2**level)
        y = int(tile_y(lat, level))
        path = tmp_path / str(level) / str(x) / f"{y}.jpg"
        path.parent.mkdir(parents=True)
        Image.new("RGB", (256, 256), "blue").save(path)
        paths.append(path)
    tiles = SatelliteTiles(tmp_path)
    assert tiles.detail_at(lon, lat) == 14
    assert tiles.detail_at(43, 38) is None
    assert tiles.native_scale_at(43, 38) is None
    paths[1].write_bytes(b"interrupted image download")
    assert SatelliteTiles(tmp_path).detail_at(lon, lat) == 12


def test_scale_bar_fits_from_country_to_street_zoom():
    for pixels_per_km in (0.1, 1, 10, 500, 1500, 10000):
        distance, length = scale_distance(pixels_per_km)
        assert 50 <= length <= 130
        assert math.isclose(distance * pixels_per_km, length)
    assert scale_distance(1500)[0] < 1  # Metres, not an overflowing one-kilometre bar.
