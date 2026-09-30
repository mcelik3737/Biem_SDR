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
        # Polling uses the real monitor state schema without starting audio or sockets.
        panel.receiver.notify(
            {
                "kind": "snapshot",
                "linked": 4,
                "errors": 0,
                "slots": {
                    1: {"recording": True, "received": 9, "lost": 1},
                    2: {"recording": False, "received": 0, "lost": 0},
                },
            }
        )
        panel.poll()
        assert "4/4" in panel.status.get()
        assert "Kaydediliyor" in panel.packet_labels[1].get()
        panel.receiver.notify({"kind": "archive_changed", "slot": 1, "text": "ID 123 • kayıt"})
        panel.poll()
        assert panel.archive_changed and "123" in panel.slot_labels[1].get()
        panel.receiver.notify({"kind": "error", "text": "Port kullanımda"})
        panel.receiver.notify({"kind": "stopped", "text": "Kapalı"})
        panel.poll()
        assert "Port kullanımda" in panel.status.get()
        # Stopping audio must not stop independent health monitoring; closing must.
        calls = []
        monkeypatch.setattr(panel.snmp, "stop", lambda: calls.append("snmp-stop"))
        monkeypatch.setattr(panel.receiver, "stop", lambda: calls.append("voice-stop"))
        panel.stop()
        assert calls == ["voice-stop"]
        panel.shutdown()
        assert calls[-2:] == ["voice-stop", "snmp-stop"]
    finally:
        root.destroy()
