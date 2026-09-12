"""Build the standalone, offline design reference. No RF/app dependency."""

from base64 import b64encode
from pathlib import Path

root = Path(__file__).resolve().parent
html = (root / "index.html").read_text(encoding="utf-8")
html = html.replace(
    '<link rel="stylesheet" href="radia.css">',
    "<style>" + (root / "radia.css").read_text(encoding="utf-8") + "</style>",
)
scripts = []
for filename in ("assets/icons.js", "assets/map-data.js", "radia.js"):
    html = html.replace(f'<script src="{filename}" defer></script>', "")
    scripts.append((root / filename).read_text(encoding="utf-8"))
html = html.replace("</body>", "<script>\n" + "\n".join(scripts) + "\n</script>\n</body>")
for filename, mime in (
    ("biem-logo.png", "image/png"),
    ("biem-amblem.png", "image/png"),
    ("telsiz-ikonu.webp", "image/webp"),
):
    encoded = b64encode((root / "assets" / filename).read_bytes()).decode("ascii")
    html = html.replace("assets/" + filename, f"data:{mime};base64,{encoded}")
html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
(root / "BIEM_Radia_Arayuz_Onizleme.html").write_text(html, encoding="utf-8")
print("Offline preview generated.")
