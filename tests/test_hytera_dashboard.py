import threading
import tkinter as tk
from tkinter import ttk

from biem_radia.console_theme import DARK, LIGHT
from biem_radia.hytera_dashboard import HyteraDashboard, alarm_display
from biem_radia.hytera_snmp import SnmpMonitor


def test_alarm_colors_respect_actual_alarm_freshness():
    assert alarm_display(None, 100, True) == ("Bilgi yok", "gray")
    assert alarm_display((0, 99, "Alıcı PLL: Normal"), 100, True) == ("Normal", "green")
    assert alarm_display((1, 99, "Verici PLL: Kilit hatası"), 100, True) == ("Kilit hatası", "red")
    assert alarm_display((0, 50, "Alıcı PLL: Normal"), 100, True) == ("Normal • eski", "gray")
    assert alarm_display((0, 99, "Alıcı PLL: Normal"), 100, False) == ("Normal • eski", "gray")


def test_dashboard_manual_rssi_and_responsive_dark_light(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("GUI tests must not use a real network")

    monkeypatch.setattr("socket.socket", no_network)
    monitor = SnmpMonitor(tmp_path)
    monitor.thread = threading.current_thread()
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        dashboard = HyteraDashboard(root, monitor.request_rssi)
        dashboard.pack(fill="both", expand=True)
        for width, palette in ((1000, LIGHT), (560, DARK)):
            root.geometry(f"{width}x700")
            style.configure("TFrame", background=palette["bg"])
            root.update()
            dashboard.update_state(monitor.snapshot())
            root.update()
            assert dashboard.canvas.cget("background") == palette["bg"]
            assert dashboard.canvas.find_all()
        dashboard.rssi_button.invoke()
        dashboard.update_state(monitor.snapshot())
        assert monitor.snapshot()["rssi_read"][1]["status"] == "pending"
        assert dashboard.rssi_button.instate(["disabled"])
        texts = [
            dashboard.canvas.itemcget(i, "text")
            for i in dashboard.canvas.find_all()
            if dashboard.canvas.type(i) == "text"
        ]
        assert "Okunuyor…" in texts
        assert "Alıcı PLL" in texts and "Verici PLL" in texts
    finally:
        root.destroy()
