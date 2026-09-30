"""Read-only, loopback-only viewer for the downloaded Turkey map. Standard library only."""

import argparse
import json
from contextlib import closing
import mimetypes
import re
import sqlite3
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
MAP = ROOT / "turkey-shortbread-1.0.mbtiles"


def connect(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)


def metadata(path):
    with closing(connect(path)) as db:
        result = dict(db.execute("SELECT name, value FROM metadata"))
    if "json" in result:
        result["layers"] = json.loads(result.pop("json")).get("vector_layers", [])
    result["bytes"] = path.stat().st_size
    result["filename"] = path.name
    return result


def read_tile(path, z, x, y):
    if not (0 <= z <= 14 and 0 <= x < 2**z and 0 <= y < 2**z):
        raise ValueError("Invalid XYZ coordinate")
    # MBTiles stores rows bottom-up (TMS); web clients request top-down XYZ.
    with closing(connect(path)) as db:
        row = db.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, 2**z - 1 - y),
        ).fetchone()
    return row[0] if row else None


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, root=ROOT, map_path=MAP, **kwargs):
        self.root, self.map_path = root, map_path
        super().__init__(*args, **kwargs)

    def log_message(self, *args):
        pass

    def reply(self, status, body=b"", mime="text/plain; charset=utf-8", compressed=False):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; worker-src 'self' blob:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'")
        if compressed:
            self.send_header("Content-Encoding", "gzip")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Reject foreign hostnames / DNS rebinding. No receiver, archive or arbitrary file API.
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            return self.reply(403, b"Loopback host required")
        route = urlsplit(self.path).path
        try:
            if route == "/api/package":
                return self.reply(200, json.dumps(metadata(self.map_path), ensure_ascii=False).encode(), "application/json")
            match = re.fullmatch(r"/tiles/(\d+)/(\d+)/(\d+)\.pbf", route)
            if match:
                tile = read_tile(self.map_path, *map(int, match.groups()))
                if tile is None:
                    return self.reply(204)
                return self.reply(200, tile, "application/vnd.mapbox-vector-tile", tile.startswith(b"\x1f\x8b"))
            allowed = {"/": "index.html", "/app.js": "app.js", "/app.css": "app.css"}
            if route in allowed:
                file = self.root / allowed[route]
            elif re.fullmatch(r"/assets/[a-zA-Z0-9_.-]+", route):
                file = self.root / route.lstrip("/")
            else:
                return self.reply(404, b"Not found")
            mime = "text/javascript" if file.suffix == ".mjs" else mimetypes.guess_type(file.name)[0]
            self.reply(200, file.read_bytes(), mime or "application/octet-stream")
        except (OSError, sqlite3.Error, ValueError):
            self.reply(503, "Harita paketi hazır değil veya istek geçersiz.".encode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    if not MAP.is_file():
        raise SystemExit("Önce Turkey harita paketini indirin: python download_map.py")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, root=ROOT, map_path=MAP))
    except OSError:
        raise SystemExit(f"{args.port} portu kullanımda. Açık harita penceresini kontrol edin.")
    if args.open:
        webbrowser.open(f"http://127.0.0.1:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
