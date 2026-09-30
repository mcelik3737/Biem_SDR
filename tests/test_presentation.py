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
        card.telemetry({"level": -42.5, "active": True, "rf_dbfs": -42.5, "rf_dbm": -76.2})
        view.update()
        assert str(view.power.cget("textvariable")) == str(card.rf_power)
        assert "-76.2 dBm" in card.rf_power.get()
        card.telemetry({"level": -42.5, "active": True, "rf_dbfs": -42.5, "rf_dbm": None})
        assert "kalibrasyon gerekli" in card.rf_power.get()
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
        assert card.rf_power.get() == "Anten: — dBm\nRF: — dBFS"
        for tab in app.tabs.tabs():
            app.tabs.select(tab)
            root.update()
        app.toggle_radio()
        assert app.fm_panel.winfo_manager() == "pack"
        app.toggle_radio()
        assert not app.fm_panel.winfo_manager()
        assert config.read_text("utf-8") == original
        assert not app.receiver.running and not app.radio.running
        app.presentation.toggle_theme()
        assert json.loads((directory / "console-ui.json").read_text("utf-8"))["dark"]
        assert config.read_text("utf-8") == original
        app.presentation.toggle_theme()
        root.deiconify()
        root.state("normal")
        root.geometry("800x480")
        app.presentation.show_all.set(True)
        for c in app.cards:
            c.enabled.set(True)
        for _ in range(5):
            root.update()
        for v in app.presentation.cards:
            assert v.speaker.winfo_height() >= 38
            assert v.meter.winfo_height() >= 38
            assert v.button.winfo_ismapped()
            assert v.speaker.winfo_y() + v.speaker.winfo_height() <= v.actions.winfo_height()
            assert v.actions.winfo_y() + v.actions.winfo_height() <= v.summary.winfo_height()
            assert v.message.winfo_ismapped()
            assert (
                v.card.frame.winfo_x() + v.card.frame.winfo_width()
                <= app.card_grid.winfo_width() + 2
            )
        app.presentation.settings()
        root.update()
        assert app.presentation.settings_window.winfo_exists()
        app.presentation.settings_window.destroy()
    finally:
        for token in root.tk.splitlist(root.tk.call("after", "info")):
            root.after_cancel(token)
        root.destroy()
