"""Hytera profile and explicit receive-only IP Dispatch connection controls."""

from __future__ import annotations

import ipaddress
import json
import queue
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from .hytera_dashboard import HyteraDashboard
from .hytera_metrics import ALARM_METRICS, METRICS, measurement_cell
from .hytera_receiver import HyteraReceiver
from .hytera_snmp import ALARM_BASE, ALARMS, SnmpMonitor, repeater_badge
from .storage import Archive


class RepeaterSettingsPanel(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, data_root: Path, archive: Archive | None = None):
        super().__init__(parent, padding=20)
        self.path = data_root / "hytera.json"
        self.receiver = HyteraReceiver(archive or Archive(data_root, protected=True))
        self.archive_changed = False
        self.connection_error = ""
        self.snmp = SnmpMonitor(data_root)
        self.snmp_enabled = tk.BooleanVar(value=False)
        self.snmp_target: tuple[str, str] | None = None
        self.snmp_pending = False
        self.shutting_down = False
        self.linked = 0
        self.linked_at = 0.0
        self.health_window: tk.Toplevel | None = None
        self.health_text = tk.StringVar(value="Röle durum izlemesi kapalı")
        self.measurement_text = tk.StringVar(value="Besleme: —   •   Güç katı: —")
        self.fields = {
            key: tk.StringVar(value=value)
            for key, value in {
                "model": "HR659 UHF",
                "firmware": "2.5",
                "repeater_ip": "",
                "local_ip": "",
                "rcp_ts1": "30009",
                "rcp_ts2": "30010",
                "rtp_ts1": "30012",
                "rtp_ts2": "30014",
            }.items()
        }
        self.status = tk.StringVar(value="Bağlı değil • Ethernet üzerinden iki slot alımı")
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text("utf-8"))
                if not isinstance(saved, dict):
                    raise ValueError("Ayar dosyası nesne olmalı.")
                for key, variable in self.fields.items():
                    if key in saved:
                        variable.set(str(saved[key]))
                self.snmp_enabled.set(saved.get("snmp_enabled") is True)
                self.snmp_pending = self.snmp_enabled.get()
            except (ValueError, OSError) as exc:
                self.status.set(f"Ayarlar okunamadı: {exc}")
        ttk.Label(self, text="Hytera • Röle izleme", font=("Segoe UI", 16, "bold")).pack(
            anchor="w", pady=(0, 12)
        )
        ttk.Label(self, textvariable=self.status, foreground="#246293").pack(anchor="w")
        # Keep all controls reachable on small touch displays.
        viewport = ttk.Frame(self)
        viewport.pack(fill="both", expand=True, pady=(8, 0))
        self.page_canvas = tk.Canvas(viewport, highlightthickness=0)
        scroll = ttk.Scrollbar(viewport, command=self.page_canvas.yview)
        self.page_canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.page_canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(self.page_canvas)
        window = self.page_canvas.create_window(0, 0, anchor="nw", window=content)
        content.bind(
            "<Configure>",
            lambda event: self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all")),
        )
        self.page_canvas.bind(
            "<Configure>", lambda event: self.page_canvas.itemconfigure(window, width=event.width)
        )
        health = ttk.Frame(content)
        health.pack(fill="x", pady=(10, 0))
        ttk.Checkbutton(
            health,
            text="Röle durumunu izle (SNMP)",
            variable=self.snmp_enabled,
            command=self.toggle_snmp,
        ).pack(side="left")
        ttk.Button(health, text="Durum ve olay günlüğü", command=self.show_health).pack(
            side="left", padx=12
        )
        ttk.Label(content, textvariable=self.health_text, wraplength=850).pack(
            anchor="w", pady=(6, 0)
        )
        self.dashboard = HyteraDashboard(content, self.read_rssi)
        self.dashboard.pack(fill="x")
        ttk.Label(content, textvariable=self.measurement_text, wraplength=850).pack(
            anchor="w", pady=(6, 0)
        )
        settings_toggle = ttk.Button(
            content, text="⚙ Bağlantı ayarları", command=self.toggle_settings
        )
        settings_toggle.pack(anchor="w", pady=(12, 0))
        self.settings_container = ttk.Frame(content)
        self.settings_container.pack(fill="x")
        form = self.settings_form = ttk.Frame(self.settings_container)
        labels = {
            "model": "Röle modeli",
            "firmware": "Firmware sürümü (cihazda doğrulanacak)",
            "repeater_ip": "Röle IP adresi",
            "local_ip": "PC yerel IP adresi / Third Party Server",
            "rcp_ts1": "Slot 1 / Kontrol UDP portu",
            "rcp_ts2": "Slot 2 / Kontrol UDP portu",
            "rtp_ts1": "Slot 1 / Ses UDP portu",
            "rtp_ts2": "Slot 2 / Ses UDP portu",
        }
        for index, (key, label) in enumerate(labels.items()):
            row, column = (index // 2) * 2, index % 2
            ttk.Label(form, text=label).grid(
                row=row, column=column, sticky="w", padx=(0, 24), pady=(6, 2)
            )
            ttk.Entry(form, textvariable=self.fields[key], width=28).grid(
                row=row + 1, column=column, sticky="w", padx=(0, 32), pady=(0, 6)
            )
        ttk.Button(form, text="Ayarları kaydet", command=self.save).grid(
            row=8, column=0, sticky="w", pady=8
        )
        if not self.fields["repeater_ip"].get():
            form.pack(anchor="w", pady=12)
        buttons = ttk.Frame(content)
        buttons.pack(anchor="w")
        self.connect_button = ttk.Button(buttons, text="▶ Röleye bağlan", command=self.connect)
        self.connect_button.pack(side="left", padx=8)
        ttk.Button(buttons, text="■ Bağlantıyı kes", command=self.stop).pack(side="left")
        ttk.Button(buttons, text="Sesi kapat", command=self.receiver.monitor.stop).pack(
            side="left", padx=8
        )
        cards = ttk.Frame(content)
        cards.pack(fill="x", pady=14)
        self.slot_labels, self.meters, self.packet_labels = {}, {}, {}
        for slot in (1, 2):
            card = ttk.LabelFrame(cards, text=f"SLOT {slot}", padding=12)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self.slot_labels[slot] = tk.StringVar(value="Çağrı bekleniyor • CC: iletilmiyor")
            ttk.Label(card, textvariable=self.slot_labels[slot], wraplength=480).pack(anchor="w")
            self.packet_labels[slot] = tk.StringVar(value="Henüz ses paketi yok")
            ttk.Label(card, textvariable=self.packet_labels[slot]).pack(anchor="w", pady=6)
            self.meters[slot] = ttk.Progressbar(card, maximum=60)
            self.meters[slot].pack(fill="x", pady=6)
            ttk.Button(
                card, text=f"♫ Slot {slot} canlı dinle", command=lambda n=slot: self.listen(n)
            ).pack(anchor="w")
        ttk.Label(
            content,
            text="Rölede Forward to PC açık olmalı; Third Party Server IP bu bilgisayarın adresi olmalı. "
            "Bağlanınca iki slotun konuşmaları ayrı ve korumalı kaydedilir. 90 sn kayıt / 2 sn ara.\n"
            "Bu bağlantı RF gönderimi yapmaz. CC, RF frekansı ve anten gücü bu paketlerde bulunmadığından "
            "boş gösterilir. Ses göstergesi ses etkinliğidir. SMS/GPS hizmetleri henüz bu bağlantıya eklenmedi.",
            wraplength=850,
            foreground="#526174",
        ).pack(anchor="w", pady=20)

    def toggle_settings(self):
        if self.settings_form.winfo_manager():
            self.settings_form.pack_forget()
        else:
            self.settings_form.pack(anchor="w", pady=12)

    def read_rssi(self):
        self.snmp.request_rssi()
        self.poll_health()

    def save(self) -> bool:
        if self.receiver.running:
            messagebox.showerror("Hytera", "Ayarları değiştirmeden önce bağlantıyı kesin.")
            return False
        values = {key: variable.get().strip() for key, variable in self.fields.items()}
        try:
            for key in ("repeater_ip", "local_ip"):
                if values[key]:
                    address = ipaddress.IPv4Address(values[key])
                    if address.is_unspecified or address.is_multicast or int(address) == 0xFFFFFFFF:
                        raise ValueError("Tek bir cihazın IPv4 adresini girin.")
            ports = [int(values[key]) for key in ("rcp_ts1", "rcp_ts2", "rtp_ts1", "rtp_ts2")]
            if any(port < 1 or port > 65535 for port in ports) or len(set(ports)) != 4:
                raise ValueError("UDP portları 1–65535 arasında ve birbirinden farklı olmalı.")
            saved = dict(values, snmp_enabled=self.snmp_enabled.get())
            pending = self.path.with_suffix(".json.tmp")
            pending.write_text(json.dumps(saved, ensure_ascii=False, indent=2), "utf-8")
            pending.replace(self.path)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Hytera bağlantı ayarları", str(exc))
            return False
        self.status.set("Ayarlar kaydedildi • Bağlı değil • Canlı test bekleniyor")
        target = (values["local_ip"], values["repeater_ip"])
        if target != self.snmp_target:
            self.snmp.stop()
            self.snmp_pending = self.snmp_enabled.get()
        return True

    def toggle_snmp(self):
        # Only this preference changes while a voice session is active.
        try:
            saved = json.loads(self.path.read_text("utf-8")) if self.path.exists() else {}
            saved["snmp_enabled"] = self.snmp_enabled.get()
            pending = self.path.with_suffix(".json.tmp")
            pending.write_text(json.dumps(saved, ensure_ascii=False, indent=2), "utf-8")
            pending.replace(self.path)
        except (ValueError, OSError, TypeError) as exc:
            self.snmp_enabled.set(not self.snmp_enabled.get())
            messagebox.showerror("SNMP ayarları", str(exc))
            return
        self.snmp_pending = self.snmp_enabled.get()
        if not self.snmp_enabled.get():
            self.snmp.stop()

    def badge(self) -> tuple[str, str]:
        linked = self.linked if time.monotonic() - self.linked_at < 3 else 0
        return repeater_badge(
            voice_running=self.running,
            linked=linked,
            snmp=self.snmp.snapshot(),
            configured=bool(self.fields["repeater_ip"].get()),
        )

    def shutdown(self):
        self.shutting_down = True
        self.snmp_pending = False
        self.stop()
        self.snmp.stop()

    def show_health(self):
        if self.health_window is not None and self.health_window.winfo_exists():
            self.health_window.lift()
            return
        self.health_window = tk.Toplevel(self)
        self.health_window.title("Hytera • Röle durumu ve olay günlüğü")
        self.health_window.geometry("900x620")
        ttk.Label(self.health_window, textvariable=self.health_text, wraplength=860).pack(
            fill="x", padx=16, pady=12
        )
        table = ttk.Frame(self.health_window)
        table.pack(fill="x", padx=16)
        self.health_fields = ttk.Treeview(table, columns=("reading", "value", "age"), height=9)
        self.health_fields.heading("#0", text="İzlenen alan")
        self.health_fields.heading("reading", text="Ölçülen değer")
        self.health_fields.heading("value", text="Alarm durumu")
        self.health_fields.heading("age", text="Güncellik")
        for column, width in (("#0", 180), ("reading", 210), ("value", 180), ("age", 245)):
            self.health_fields.column(column, width=width, minwidth=80)
        table_scroll = ttk.Scrollbar(table, command=self.health_fields.yview)
        self.health_fields.configure(yscrollcommand=table_scroll.set)
        table_scroll.pack(side="right", fill="y")
        self.health_fields.pack(fill="x")
        for n, (label, _) in ALARMS.items():
            self.health_fields.insert("", "end", iid=str(n), text=label)
        for n in (11, 12, 9, 10):
            self.health_fields.insert("", "end", iid=f"metric{n}", text=METRICS[n])
        ttk.Label(
            self.health_window,
            text="Son olaylar (yerel saat) • Tüm günlük: Veri günlüğü / data/hytera-status",
        ).pack(anchor="w", padx=16, pady=8)
        box = ttk.Frame(self.health_window)
        box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.health_events = tk.Text(box, state="disabled", wrap="word", font=("Segoe UI", 10))
        scroll = ttk.Scrollbar(box, command=self.health_events.yview)
        self.health_events.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.health_events.pack(fill="both", expand=True)
        self.health_last_history = ""
        self.poll_health()

    def poll_health(self):
        if self.snmp_pending and not self.snmp.running and not self.shutting_down:
            self.snmp_pending = False
            self.snmp_target = (
                self.fields["local_ip"].get().strip(),
                self.fields["repeater_ip"].get().strip(),
            )
            try:
                self.snmp.start(*self.snmp_target)
            except ValueError as exc:
                self.snmp.error = str(exc)
        state = self.snmp.snapshot()
        self.page_canvas.configure(background=ttk.Style(self).lookup("TFrame", "background"))
        self.dashboard.update_state(state)
        label, _ = self.badge()
        age = "Henüz yanıt yok" if state["age"] is None else f"Son yanıt {state['age']:.0f} sn önce"
        normal = state["normal"] if state["fresh"] else 0
        detail = (
            " • ".join(state["active"]) or f"Normal alan: {normal}/9 • Diğer alanlar doğrulanmadı"
        )
        self.health_text.set(
            f"{state['identity'].get('alias', 'Röle')} • {label} • {age}\n{detail}"
            + (f" • {state['error']}" if state["error"] else "")
        )
        now = time.monotonic()
        measures = state["measurements"]
        summary = []
        for n, title in ((1, "Besleme"), (2, "Güç katı"), (11, "Kaynak"), (12, "Batarya")):
            value, freshness = measurement_cell(measures.get(n), now, state["running"])
            summary.append(f"{title}: {value}" + (" (eski)" if "eski" in freshness else ""))
        self.measurement_text.set("   •   ".join(summary))
        if self.health_window is None or not self.health_window.winfo_exists():
            return
        for n in ALARMS:
            record = state["fields"].get(f"{ALARM_BASE}{n}.0")
            value = record[2].split(": ", 1)[1] if record else "Henüz bildirilmedi"
            freshness = f"{max(0, now - record[1]):.0f} sn önce" if record else "—"
            if record and (now - record[1] > 35 or not state["fresh"]):
                freshness += " • eski veri"
            measurement_id = ALARM_METRICS.get(n)
            reading, measured_at = measurement_cell(
                measures.get(measurement_id), now, state["running"]
            )
            if measurement_id is None:
                reading = "— / sayısal değer doğrulanmadı"
            else:
                freshness = f"Ölçüm: {measured_at} / Alarm: {freshness}"
            self.health_fields.item(str(n), values=(reading, value, freshness))
        for n in (11, 12, 9, 10):
            reading, freshness = measurement_cell(measures.get(n), now, state["running"])
            self.health_fields.item(f"metric{n}", values=(reading, "—", freshness))
        history = "\n".join(
            f"{datetime.fromisoformat(item['observed_utc']).astimezone():%d.%m.%Y %H:%M:%S}  {item['raw']}"
            for item in state["history"]
        )
        if history != self.health_last_history:
            self.health_last_history = history
            self.health_events.configure(state="normal")
            self.health_events.delete("1.0", "end")
            self.health_events.insert("1.0", history)
            self.health_events.see("end")
            self.health_events.configure(state="disabled")

    def connect(self):
        if not self.save():
            return
        values = {key: variable.get().strip() for key, variable in self.fields.items()}
        if not values["local_ip"] or not values["repeater_ip"]:
            messagebox.showerror("Hytera", "Röle ve PC yerel IPv4 adreslerini girin.")
            return
        self.connection_error = ""
        try:
            self.receiver.start(values)
        except ValueError as exc:
            messagebox.showerror("Hytera", str(exc))
            return
        self.status.set("Bağlantı açılıyor…")

    @property
    def running(self) -> bool:
        return self.receiver.running

    def stop(self):
        self.receiver.stop()

    def listen(self, slot: int):
        try:
            self.receiver.monitor.select(f"Hytera • Slot {slot}", str(slot))
        except RuntimeError as exc:
            messagebox.showerror("Canlı dinleme", str(exc))

    def poll(self):
        self.poll_health()
        self.connect_button.configure(state="disabled" if self.running else "normal")
        try:
            while True:
                item = self.receiver.messages.get_nowait()
                if item["kind"] == "snapshot":
                    self.linked, self.linked_at = item["linked"], time.monotonic()
                    self.status.set(
                        f"Röle yanıtı: {item['linked']}/4 port • Hatalı/desteklenmeyen paket: {item['errors']}"
                    )
                    for slot, data in item["slots"].items():
                        self.packet_labels[slot].set(
                            f"{'● Kaydediliyor' if data['recording'] else 'Çağrı bekleniyor'} • Ses paketi {data['received']} • Kayıp {data['lost']}\n"
                            f"Kontrolsüz / tekrar / geç gelen: {data.get('discarded', 0)}"
                        )
                elif item["kind"] == "call":
                    self.slot_labels[item["slot"]].set(item["text"])
                elif item["kind"] == "archive_changed":
                    self.archive_changed = True
                    self.slot_labels[item["slot"]].set(item["text"])
                elif item["kind"] == "error":
                    self.connection_error = item["text"]
                    self.status.set(item["text"])
                else:
                    self.status.set(self.connection_error or item["text"])
        except queue.Empty:
            pass
        for slot, meter in self.meters.items():
            state = self.receiver.monitor.state(f"Hytera • Slot {slot}")
            meter["value"] = (
                max(0, min(60, 60 + state["audio_dbfs"])) if state["audio_present"] else 0
            )
