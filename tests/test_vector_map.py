import gzip
import json
import sqlite3
import time
import tkinter as tk
from contextlib import closing
from threading import Event

import mapbox_vector_tile
import pytest
from PIL import Image, ImageDraw

from biem_radia.map_panel import MapPanel, project
from biem_radia.satellite import latitude
from biem_radia.storage import Archive
from biem_radia.vector_map import (
    COS39,
    VECTOR_NAME,
    VectorMap,
    Viewport,
    find_package,
    paint_polygon,
    visible_tiles,
)
from biem_radia.vector_worker import MapWorker


@pytest.fixture
def package(tmp_path):
    folder = tmp_path / "map-packs/turkey-test"
    folder.mkdir(parents=True)
    path = folder / "turkey.mbtiles"
    meta = {
        "format": "pbf",
        "maxzoom": "14",
        "bounds": "25,35,45,43",
        "json": json.dumps(
            {"vector_layers": [{"id": name} for name in ("streets", "place_labels", "buildings")]}
        ),
    }
    data = mapbox_vector_tile.encode(
        {
            "name": "streets",
            "features": [
                {
                    "geometry": {"type": "LineString", "coordinates": [[100, 100], [3900, 3900]]},
                    "properties": {"kind": "primary"},
                }
            ],
        },
        default_options={"y_coord_down": True},
    )
    with closing(sqlite3.connect(path)) as db:
        db.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
        db.executemany("INSERT INTO metadata VALUES (?,?)", meta.items())
        db.execute(
            "CREATE TABLE tiles (zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB)"
        )
        # XYZ 4/9/6 becomes TMS row 9, deliberately asymmetric.
        db.execute("INSERT INTO tiles VALUES (4,9,9,?)", (gzip.compress(data),))
        db.commit()
    (folder / "manifest.json").write_text(
        json.dumps({"format": "biem-shortbread-mbtiles-v1", "filename": path.name}), "utf-8"
    )
    return path


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.01)
    raise AssertionError("Map result timed out")


def test_package_tms_gzip_and_projection(package):
    assert find_package(package.parents[2]) == package
    renderer = VectorMap(package)
    with renderer.connection() as db:
        assert renderer.tile(db, 4, 9, 6)["streets"]["features"][0]["geometry"]["coordinates"][
            0
        ] == [100, 100]
        assert renderer.tile(db, 4, 9, 9) == {}
    lon, lat = 33.75, latitude(6.5, 4)
    view = Viewport(300, 200, project(lon, lat), 256 * 2**4 / (360 * COS39))
    assert view.screen(lon, lat) == (150, 100)
    assert view.coordinates(*view.screen(28.9, 41.1)) == pytest.approx((28.9, 41.1))
    result = renderer.render(view)
    assert result[1]["loaded"] == 1
    assert result[1]["features"]["streets"] == 1
    assert len(result[0].getcolors()) > 1
    assert renderer.render(view, lambda: True) is None
    overzoom = Viewport(800, 500, project(32, 39), 256 * 2**17 / (360 * COS39))
    assert all(z == 14 for z, x, y in visible_tiles(overzoom))


def test_package_rejects_filename_escape(package):
    manifest = package.parent / "manifest.json"
    manifest.write_text(
        json.dumps({"format": "biem-shortbread-mbtiles-v1", "filename": "../turkey.mbtiles"}),
        "utf-8",
    )
    assert find_package(package.parents[2]) is None


def test_polygon_hole_preserves_underlying_pixels():
    picture = Image.new("RGB", (30, 30), "green")
    paint_polygon(
        picture,
        ImageDraw.Draw(picture),
        [[(2, 2), (28, 2), (28, 28), (2, 28)], [(10, 10), (20, 10), (20, 20), (10, 20)]],
        "blue",
    )
    assert picture.getpixel((5, 5)) == (0, 0, 255)
    assert picture.getpixel((15, 15)) == (0, 128, 0)


def test_worker_discards_stale_requests_and_reports_errors():
    started, release = Event(), Event()

    class Renderer:
        def render(self, view, cancelled):
            if view == "first":
                started.set()
                assert release.wait(2)
                assert cancelled()
            if view == "bad":
                raise ValueError("broken tile")
            return view

    worker = MapWorker(Renderer())
    try:
        worker.submit("first")
        assert started.wait(2)
        worker.submit("superseded")
        worker.submit("latest")
        release.set()
        assert wait_for(worker.take_result) == ("latest", "latest", None)
        worker.submit("bad")
        assert wait_for(worker.take_result) == ("bad", None, "broken tile")
    finally:
        release.set()
        worker.close()
        worker.thread.join(2)
    assert not worker.thread.is_alive()


def test_panel_vector_default_city_jump_and_radio_anchor(package):
    root = tk.Tk()
    root.withdraw()
    try:
        panel = MapPanel(root, Archive(package.parents[2]))
        panel.pack(fill="both", expand=True)
        root.geometry("1200x750")
        root.deiconify()
        root.update()
        assert panel.base_map.get() == VECTOR_NAME

        def drawn():
            root.update()
            return panel.canvas.find_withtag("vector-map")

        wait_for(drawn)
        assert "OpenStreetMap" in panel.map_credit.get()
        panel.city_name.set("İstanbul")
        panel.focus_city()
        wait_for(drawn)
        place = panel.city_places["İstanbul"]
        assert panel.screen(place["lon"], place["lat"]) == pytest.approx(
            (panel.canvas.winfo_width() / 2, panel.canvas.winfo_height() / 2)
        )
        panel.reader.latest = {
            "longitude": place["lon"],
            "latitude": place["lat"],
            "source_id": 3737,
        }
        panel.render()
        assert panel.canvas.find_withtag("radio-photo")
        before = panel.screen(place["lon"], place["lat"])
        panel.base_map.set("Standart")
        panel.render()
        assert not panel.canvas.find_withtag("vector-map")
        assert panel.screen(place["lon"], place["lat"]) == before
        worker = panel.vector_worker
    finally:
        root.destroy()
    worker.thread.join(2)
    assert not worker.thread.is_alive()
