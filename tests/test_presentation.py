import json
import tkinter as tk
from dataclasses import asdict

from biem_radia.app import RadiaApp
from biem_radia.models import Channel


def test_presentation_keeps_config_and_live_telemetry(tmp_path):
    directory = tmp_path / "data"
    directory.mkdir()
    configured = Channel("Sunum kanalı", 427_500_000, mode="DMR", color_code=11)
    config = directory / "channels.json"
    original = json.dumps([asdict(configured)])
    config.write_text(original, "utf-8")
    root = tk.Tk()
    root.withdraw()
    try:
        app = RadiaApp(root, tmp_path)
        root.update()
        card = app.cards[0]
        view = app.presentation.cards[0]
        assert card.value() == configured
        view.toggle()
        assert view.expanded and card.code_entry.winfo_manager()
        view.toggle()
        card.telemetry({"level": -42.5, "active": True, "data": "ID 3737 · Grup 21"})
        view.update()
        assert str(view.state.cget("textvariable")) == str(card.state)
        assert str(view.detail.cget("textvariable")) == str(card.details)
        assert "KAYIT" in card.state.get()
        card.telemetry(
            {"level": -42.5, "active": True, "peak_hz": 427502000, "peak_offset_hz": 2000}
        )
        assert str(view.peak.cget("textvariable")) == str(card.peak)
        assert "427.50200 MHz" in card.peak.get() and "+2.00 kHz" in card.peak.get()
        card.telemetry(
            {"level": -42.5, "active": False, "peak_hz": 427498000, "peak_offset_hz": -2000}
        )
        assert "-2.00 kHz" in card.peak.get()
        for offset, color in (
            (2000, "#18784a"),
            (-2000, "#18784a"),
            (2001, "#b42336"),
            (-5500, "#b42336"),
        ):
            card.telemetry(
                {
                    "level": -30,
                    "active": False,
                    "follow_state": "locked",
                    "locked_hz": configured.frequency_hz + offset,
                    "lock_offset_hz": offset,
                }
            )
            view.update()
            assert "KİLİT" in card.peak.get()
            assert str(view.peak.cget("foreground")) == color
        assert card.value() == configured
        card.telemetry(None)
        assert card.peak.get() == "Tepe: — MHz\nΔ — kHz"
        for tab in app.tabs.tabs():
            app.tabs.select(tab)
            root.update()
        app.toggle_radio()
        assert app.fm_panel.winfo_manager() == "pack"
        app.toggle_radio()
        assert not app.fm_panel.winfo_manager()
        assert config.read_text("utf-8") == original
        assert not app.receiver.running and not app.radio.running
    finally:
        for token in root.tk.splitlist(root.tk.call("after", "info")):
            root.after_cancel(token)
        root.destroy()
