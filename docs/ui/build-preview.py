"""Produce the offline single-file design reference; no application dependencies."""

from base64 import b64encode
from pathlib import Path

root = Path(__file__).resolve().parent
html = (root / "index.html").read_text(encoding="utf-8")
html = html.replace(
    '<link rel="stylesheet" href="radia.css">',
    "<style>" + (root / "radia.css").read_text(encoding="utf-8") + "</style>",
)
html = html.replace('<script src="assets/icons.js" defer></script>', "")
html = html.replace('<script src="radia.js" defer></script>', "")
html = html.replace(
    'src="assets/biem-logo.png"',
    'src="data:image/png;base64,'
    + b64encode((root / "assets/biem-logo.png").read_bytes()).decode("ascii")
    + '"',
)
scripts = (
    "<script>"
    + (root / "assets/icons.js").read_text(encoding="utf-8")
    + "\n"
    + (root / "radia.js").read_text(encoding="utf-8")
    + "</script>"
)
html = html.replace("</body>", scripts + "\n</body>")
html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
(root / "BIEM_Radia_Arayuz_Onizleme.html").write_text(html, encoding="utf-8")
print("Offline preview generated.")
