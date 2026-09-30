import io
import zipfile

import pytest
from PIL import Image

from biem_radia.map_pack import install
from biem_radia.satellite import SatelliteTiles


def test_map_pack_install_idempotent_and_lazy_cache(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (256, 256), (30, 60, 90)).save(buffer, format="PNG")
    path = tmp_path / "addon.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("addon/4/9/6.png", buffer.getvalue())
        z.writestr("../do-not-extract.txt", "not a tile")
    root = tmp_path / "packs"
    result = install(path, root)
    assert result.is_relative_to(root)
    assert (result / "manifest.json").is_file()
    assert not (tmp_path / "do-not-extract.txt").exists()
    assert install(path, root) == result
    tiles = SatelliteTiles(result / "tiles")
    assert len(tiles.tiles) == 1 and not tiles.cache
    assert tiles.load(tiles.tiles[0][3]).size == (256, 256)
    assert len(tiles.cache) == 1


def test_invalid_pack_never_activated(tmp_path):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("bad/4/9/6.png", b"not an image")
    root = tmp_path / "packs"
    with pytest.raises(OSError):
        install(path, root)
    assert not list(root.glob("*/manifest.json"))
