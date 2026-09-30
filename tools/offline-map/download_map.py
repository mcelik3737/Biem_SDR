"""Download the officially published Turkey MBTiles package, never scrape map tiles."""

import hashlib
import json
from contextlib import closing
import shutil
import sqlite3
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
URL = "https://download.geofabrik.de/europe/turkey-shortbread-1.0.mbtiles"
NAME = "turkey-shortbread-1.0.mbtiles"
LIMIT = 2_000_000_000


def validate(path):
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("SQLite doğrulaması başarısız")
        meta = dict(db.execute("SELECT name,value FROM metadata"))
        if meta.get("format") != "pbf":
            raise ValueError("Vektör karo biçimi bekleniyordu")
        layers = json.loads(meta["json"])["vector_layers"]
        if not {"streets", "place_labels", "buildings"}.issubset({x["id"] for x in layers}):
            raise ValueError("Beklenen Shortbread katmanları eksik")
        levels = dict(db.execute("SELECT zoom_level,count(*) FROM tiles GROUP BY zoom_level"))
        if not levels or max(levels) < 14:
            raise ValueError("Paket yakınlık seviyeleri eksik")
        # Test that the z14 package covers points across Turkey, including both endpoints.
        import math
        for name, lon, lat in [("İstanbul",28.9784,41.0082),("Ankara",32.8597,39.9334),("İzmir",27.1428,38.4237),("Konya",32.4932,37.8746),("Van",43.372,38.5012),("Hakkari",43.739,37.574),("Edirne",26.5557,41.6771)]:
            x = int((lon+180)/360*2**14)
            y = int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**14)
            if not db.execute("SELECT 1 FROM tiles WHERE zoom_level=14 AND tile_column=? AND tile_row=?", (x,2**14-1-y)).fetchone():
                raise ValueError(f"Örnek şehir karosu bulunamadı: {name}")
    with path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    return {"format":"biem-shortbread-mbtiles-v1", "source":URL, "filename":NAME, "bytes":path.stat().st_size, "sha256":digest, "levels":levels, "tile_count":sum(levels.values()), "layers":[x["id"] for x in layers], "metadata":meta, "validated_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()), "license":"ODbL-1.0", "attribution":"© OpenStreetMap contributors / Geofabrik", "network_required_for_viewing":False}


def download(root=ROOT):
    root.mkdir(parents=True, exist_ok=True)
    dest=root/NAME
    if dest.exists():
        result=validate(dest)
        print("Mevcut paket doğrulandı; yeniden indirilmedi.")
    else:
        part=dest.with_suffix(dest.suffix+".part")
        state=root/"download-state.json"
        headers={"User-Agent":"BIEM-Offline-Map/0.1"}
        with urlopen(Request(URL,headers=headers,method="HEAD"),timeout=30) as response:
            size=int(response.headers["Content-Length"])
            etag=response.headers.get("ETag")
            modified=response.headers.get("Last-Modified")
        if not 1<size<=LIMIT:
            raise ValueError("Paket 2 GB indirme sınırını aşıyor")
        saved=json.loads(state.read_text("utf-8")) if state.exists() else {}
        position=part.stat().st_size if part.exists() and etag and saved.get("etag")==etag and saved.get("size")==size else 0
        if position>size:
            position=0
        if shutil.disk_usage(root).free<size-position+500_000_000:
            raise ValueError("İndirme için yeterli boş alan yok")
        state.write_text(json.dumps({"etag":etag,"size":size,"last_modified":modified,"url":URL},indent=2),"utf-8")
        if position<size:
            if position:
                headers.update({"Range":f"bytes={position}-","If-Range":etag})
            with urlopen(Request(URL,headers=headers),timeout=60) as response:
                if position and response.status==200:
                    position=0
                elif position and (response.status!=206 or not response.headers.get("Content-Range","").startswith(f"bytes {position}-")):
                    raise ValueError("Sunucu devam etme aralığını doğrulamadı")
                if response.headers.get("ETag") != etag:
                    raise ValueError("Paket sunucuda değişti; tekrar deneyin")
                with part.open("ab" if position else "wb") as file:
                    last=0.0
                    while chunk:=response.read(1_048_576):
                        position+=len(chunk)
                        if position>size:
                            raise ValueError("Sunucu beklenen dosya boyutunu aştı")
                        file.write(chunk)
                        if time.monotonic()-last>1:
                            print(f"\rTürkiye: %{position/size*100:.1f} ({position/1e6:.0f}/{size/1e6:.0f} MB)",end="",flush=True)
                            last=time.monotonic()
        if part.stat().st_size!=size:
            raise ValueError("İndirme tamamlanmadı; tekrar çalıştırınca devam eder")
        print("\nPaket bütünlüğü ve Türkiye kapsamı doğrulanıyor…")
        result=validate(part)
        result.update({"source_etag":etag,"source_last_modified":modified})
        part.rename(dest)
    (root/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),"utf-8")
    print(f"Hazır: {dest}\n{result['tile_count']} karo, {len(result['layers'])} veri katmanı")
    return result


if __name__=="__main__":
    try:
        download()
    except KeyboardInterrupt:
        print("\nİndirme durduruldu. Kısmi dosya korundu.")
