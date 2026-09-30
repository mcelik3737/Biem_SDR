"""BIEM console tokens; the orange accent is inspired by Hytera field equipment."""

LIGHT = {
    "bg": "#eef1f5",
    "surface": "#ffffff",
    "raised": "#f5f7fa",
    "ink": "#213044",
    "muted": "#617188",
    "line": "#d7dfe9",
    "nav": "#192738",
    "nav_ink": "#f2f5fa",
    "accent": "#ad2947",
    "orange": "#d95b08",
    "green": "#11794d",
    "red": "#bc263d",
    "gray": "#697383",
    "off": "#e2e5e9",
    "selected": "#f7e9ee",
    "blue": "#195f9d",
}
DARK = {
    "bg": "#101822",
    "surface": "#192635",
    "raised": "#223345",
    "ink": "#edf3fa",
    "muted": "#a7b8cb",
    "line": "#34465b",
    "nav": "#0b121b",
    "nav_ink": "#edf3fa",
    "accent": "#b52b4d",
    "orange": "#ff9b48",
    "green": "#59d9a1",
    "red": "#ff7d8d",
    "gray": "#a1a9b5",
    "off": "#303a46",
    "selected": "#422d40",
    "blue": "#89c4ff",
}


def channel_status(*, connected, running, enabled, state, threshold):
    if connected is False:
        return "disconnected", "SDR bağlantısı yok", "gray"
    if not enabled:
        return "disabled", "Kanal devre dışı", "gray"
    if not running:
        return "stopped", "Alım durduruldu", "gray"
    if not state:
        return "waiting", "Kanal sırası bekleniyor", "green"
    if state.get("level", -120) < threshold:
        return "ready", "Hazır · yayın bekleniyor", "green"
    if state.get("audio_present", False):
        return "audio", "Ses alınıyor", "green"
    return "no_audio", "Sinyal var · ses yok", "red"


def grid_shape(count, width):
    if count <= 1:
        return 1, 1
    columns = 3 if count >= 5 and width >= 640 else 2 if width >= 440 else 1
    return columns, (count + columns - 1) // columns
