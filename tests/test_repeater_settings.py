import json
import tkinter as tk
from tkinter import ttk

from biem_radia.repeater_settings import RepeaterSettingsPanel


def test_offline_profile_persistence_and_invalid_input_preserves_file(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Offline settings must not open a socket")

    monkeypatch.setattr("socket.socket", no_network)
    errors = []
    monkeypatch.setattr(
        "biem_radia.repeater_settings.messagebox.showerror",
        lambda title, text: errors.append(text),
    )
    root = tk.Tk()
    root.withdraw()
    try:
        tabs = ttk.Notebook(root)
        panel = RepeaterSettingsPanel(tabs, tmp_path)
        assert panel.save()  # A disconnected repeater may have no IP yet.
        panel.fields["repeater_ip"].set("192.168.4.32")
        panel.fields["local_ip"].set("192.168.4.10")
        assert panel.save()
        original = panel.path.read_bytes()
        assert json.loads(original)["model"] == "HR659 UHF"
        restored = RepeaterSettingsPanel(tabs, tmp_path)
        assert restored.fields["repeater_ip"].get() == "192.168.4.32"
        assert "Bağlı değil" in restored.status.get()
        panel.fields["repeater_ip"].set("999.1.1.1")
        assert not panel.save() and panel.path.read_bytes() == original
        panel.fields["repeater_ip"].set("192.168.4.32")
        panel.fields["rtp_ts2"].set("30012")
        assert not panel.save() and panel.path.read_bytes() == original
        assert len(errors) == 2
    finally:
        root.destroy()
