"""Browser security contracts. No SDR, sockets, sound device or network is opened."""

from __future__ import annotations

import json
import time
import wave
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from biem_radia.models import Channel
from biem_radia.server.__main__ import project_lease, server_arguments
from biem_radia.server.auth import Accounts, AuthError, digest
from biem_radia.server.runtime import BrowserAudio, RadioRuntime
from biem_radia.server.web import COOKIE, create_app

ORIGIN = "http://testserver"
PASSWORD = "test-only-long-password"


@pytest.fixture
def site(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "channels.json").write_text(
        json.dumps([asdict(Channel("A", 424000000)), asdict(Channel("B", 424012500))]), "utf-8"
    )
    runtime = RadioRuntime(tmp_path)
    accounts = Accounts(data / "server")
    app = create_app(
        runtime, accounts, origin=ORIGIN, bootstrap_secret="local-setup-token", background=False
    )
    with TestClient(app, base_url=ORIGIN, client=("127.0.0.1", 51000)) as client:
        yield client, accounts, runtime, app


def write(client, path, body, csrf="", method="POST", **headers):
    return client.request(
        method, path, json=body, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf, **headers}
    )


def login(client, name="admin"):
    response = write(client, "/api/login", {"username": name, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()["csrf"]


def bootstrap(client):
    r = write(
        client,
        "/api/setup",
        {"username": "admin", "password": PASSWORD},
        **{"X-Setup-Token": "local-setup-token"},
    )
    assert r.status_code == 200, r.text
    return login(client)


def add_user(client, csrf, **overrides):
    form = {
        "username": "operator",
        "password": PASSWORD,
        "permissions": ["live.view"],
        "channels": ["A"],
        **overrides,
    }
    r = write(client, "/api/admin/users", form, csrf)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def seed_calls(runtime):
    for name in ("A", "B"):
        path = runtime.archive.root / (name + ".wav")
        with wave.open(str(path), "wb") as w:
            w.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
            w.writeframes(bytes(1600))
        with runtime.archive.connect() as db:
            db.execute(
                "INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason) "
                "VALUES(?,?,424000000,'2026-10-01T08:00:00+00:00',0.1,?,'test','end')",
                (name, name, name + ".wav"),
            )
        runtime.inbox.add(
            {
                "channel": name,
                "text": name + " private message",
                "observed_utc": "2026-10-01T08:00:00+00:00",
            },
            "test",
            name,
        )


def test_setup_is_local_token_gated_one_time_and_no_default_credentials(site):
    client, accounts, _, app = site
    assert client.get("/api/setup").json() == {"required": True}
    assert (
        write(client, "/api/setup", {"username": "admin", "password": PASSWORD}).status_code == 403
    )
    with TestClient(app, base_url=ORIGIN, client=("192.168.1.25", 50001)) as remote:
        assert (
            write(
                remote,
                "/api/setup",
                {"username": "admin", "password": PASSWORD},
                **{"X-Setup-Token": "local-setup-token"},
            ).status_code
            == 403
        )
    bootstrap(client)
    assert accounts.initialized
    assert (
        write(
            client,
            "/api/setup",
            {"username": "second", "password": PASSWORD},
            **{"X-Setup-Token": "local-setup-token"},
        ).status_code
        == 409
    )
    with accounts.database() as db:
        assert db.execute("SELECT password FROM users").fetchone()[0].startswith("$argon2id$")
        session_token = db.execute("SELECT token FROM sessions").fetchone()[0]
        assert session_token == digest(client.cookies[COOKIE])


@pytest.mark.parametrize(
    "path",
    [
        "/api/live",
        "/api/calls",
        "/api/calls/A/audio",
        "/api/messages",
        "/api/admin",
        "/api/map/location",
        "/api/map/image",
        "/api/repeater",
        "/api/spectrum",
        "/api/live/audio?channel=A&stream=1",
    ],
)
def test_every_private_data_route_requires_session(site, path):
    client, _, _, _ = site
    assert client.get(path).status_code == 401


def test_page_denial_and_channel_filters_are_server_enforced(site):
    client, _, runtime, _ = site
    csrf = bootstrap(client)
    seed_calls(runtime)
    add_user(
        client,
        csrf,
        permissions=[
            "live.view",
            "live.listen",
            "archive.view",
            "archive.play",
            "messages.view",
            "map.view",
        ],
    )
    login(client, "operator")
    assert [c["name"] for c in client.get("/api/live").json()["channels"]] == ["A"]
    assert [r["id"] for r in client.get("/api/calls").json()["rows"]] == ["A"]
    assert "path" not in client.get("/api/calls").json()["rows"][0]
    assert [r["channel"] for r in client.get("/api/messages").json()["rows"]] == ["A"]
    assert client.get("/api/calls/B/audio").status_code == 404
    assert client.get("/api/calls/A/audio").content.startswith(b"RIFF")
    assert client.get("/api/live/audio?channel=B&stream=1").status_code == 404
    runtime.locations.latest = {
        "channel": "B",
        "latitude": 39,
        "longitude": 35,
        "source_id": 1001,
        "observed_utc": "2026-10-01T08:00:00+00:00",
    }
    assert client.get("/api/map/location").json() == {"location": None}
    runtime.locations.latest["channel"] = "A"
    assert client.get("/api/map/location").json()["location"]["source_id"] == 1001
    for path in ("/api/spectrum", "/api/repeater", "/api/admin"):
        assert client.get(path).status_code == 403


def test_no_grants_no_data_and_view_does_not_grant_audio(site):
    client, _, runtime, _ = site
    csrf = bootstrap(client)
    seed_calls(runtime)
    add_user(client, csrf, permissions=["live.view", "archive.view", "messages.view"], channels=[])
    login(client, "operator")
    assert client.get("/api/live").json()["channels"] == []
    assert client.get("/api/calls").json()["rows"] == []
    assert client.get("/api/messages").json()["rows"] == []
    assert client.get("/api/calls/A/audio").status_code == 403
    assert client.get("/api/live/audio?channel=A&stream=1").status_code == 403


def test_user_cannot_promote_self_or_control_receiver(site, monkeypatch):
    client, _, runtime, _ = site
    csrf = bootstrap(client)
    uid = add_user(client, csrf)
    csrf = login(client, "operator")
    calls = []
    monkeypatch.setattr(runtime, "control", lambda *args: calls.append(args))
    assert (
        write(
            client, f"/api/admin/users/{uid}", {"username": "operator", "admin": True}, csrf, "PUT"
        ).status_code
        == 403
    )
    assert (
        write(client, "/api/control", {"target": "receiver", "action": "start"}, csrf).status_code
        == 403
    )
    assert (
        write(client, "/api/control", {"target": "spectrum", "action": "start"}, csrf).status_code
        == 403
    )
    assert calls == []


def test_csrf_origin_host_body_limits_and_no_password_echo(site):
    client, _, _, _ = site
    csrf = bootstrap(client)
    assert write(client, "/api/logout", {}).status_code == 403
    assert write(client, "/api/logout", {}, csrf, Origin="https://attacker.test").status_code == 403
    assert client.get("/api/me", headers={"Host": "attacker.test"}).status_code == 403
    assert client.get("/api/me", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert (
        client.post(
            "/api/logout",
            content="x" * 70000,
            headers={"Origin": ORIGIN, "Content-Type": "application/json"},
        ).status_code
        == 413
    )
    r = write(client, "/api/login", {"username": "admin", "password": PASSWORD, "unexpected": True})
    assert r.status_code == 422 and PASSWORD not in r.text
    assert write(client, "/api/logout", {}, csrf).status_code == 200
    assert client.get("/api/me").status_code == 401


def test_account_change_revokes_other_client_immediately_and_last_admin_survives(site):
    client, accounts, _, app = site
    csrf = bootstrap(client)
    uid = add_user(client, csrf)
    with TestClient(app, base_url=ORIGIN) as operator:
        login(operator, "operator")
        assert operator.get("/api/live").status_code == 200
        r = write(
            client,
            f"/api/admin/users/{uid}",
            {"username": "operator", "enabled": False},
            csrf,
            "PUT",
        )
        assert r.status_code == 200
        assert operator.get("/api/live").status_code == 401
        assert (
            write(
                operator, "/api/login", {"username": "operator", "password": PASSWORD}
            ).status_code
            == 401
        )
    admin_id = next(u["id"] for u in accounts.users() if u["admin"])
    r = write(
        client, f"/api/admin/users/{admin_id}", {"username": "admin", "admin": False}, csrf, "PUT"
    )
    assert r.status_code == 400
    assert client.get("/api/admin").status_code == 200


def test_attempt_limit_expired_session_and_safe_static_roots(site):
    client, accounts, _, _ = site
    bootstrap(client)
    with accounts.database() as db:
        db.execute("UPDATE sessions SET expires=?", (time.time() - 1,))
    assert client.get("/api/me").status_code == 401
    for _ in range(10):
        assert (
            write(client, "/api/login", {"username": "unknown", "password": "bad"}).status_code
            == 401
        )
    assert (
        write(client, "/api/login", {"username": "unknown", "password": "bad"}).status_code == 429
    )
    for path in (
        "/data/server/accounts.sqlite3",
        "/assets/accounts.sqlite3",
        "/docs",
        "/openapi.json",
    ):
        assert client.get(path).status_code == 404
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_permission_dependencies_unknown_grants_and_channel_sql_injection(site):
    client, _, _, _ = site
    csrf = bootstrap(client)
    for form in (
        {"permissions": ["archive.play"]},
        {"permissions": ["root.access"]},
        {"channels": ["A') OR 1=1 --"]},
    ):
        r = write(
            client, "/api/admin/users", {"username": "operator", "password": PASSWORD, **form}, csrf
        )
        assert r.status_code == 400
    add_user(client, csrf)
    assert (
        write(
            client, "/api/admin/users", {"username": "operator", "password": PASSWORD}, csrf
        ).status_code
        == 409
    )


def test_authorized_control_preferences_and_archive_path_containment(site, monkeypatch):
    client, accounts, runtime, _ = site
    csrf = bootstrap(client)
    seen = []
    monkeypatch.setattr(runtime, "control", lambda *args: seen.append(args))
    assert (
        write(client, "/api/control", {"target": "receiver", "action": "start"}, csrf).status_code
        == 200
    )
    assert seen == [("receiver", "start", 420, 421)]
    assert write(client, "/api/admin/startup", {"receiver": True}, csrf, "PUT").status_code == 200
    assert client.get("/api/admin").json()["startup"]["receiver"] is True
    assert any(r["action"] == "receiver: start" for r in accounts.history())
    seed_calls(runtime)
    with runtime.archive.connect() as db:
        db.execute("UPDATE calls SET path='../secret.wav' WHERE id='A'")
    assert client.get("/api/calls/A/audio").status_code == 409


def test_audio_tap_keeps_streams_separate_is_bounded_and_does_not_open_speakers():
    audio = BrowserAudio()
    for _ in range(100):
        audio.feed("A", "slot1", np.ones(1000, dtype=np.float32) * 0.1, 8000, "Slot 1")
        audio.feed("A", "slot2", np.ones(1000, dtype=np.float32) * 0.2, 8000, "Slot 2")
    first = audio.packets("A", "slot1", 0)
    assert len(first["packets"]) == 64
    assert len(audio.streams("A")) == 2
    assert audio.output is None
    seq = first["packets"][-1]["sequence"]
    assert audio.packets("A", "slot1", seq)["packets"] == []
    assert audio.packets("B", "slot1", 0)["packets"] == []
    audio.clear()
    assert audio.packets("A", "slot1", 0)["packets"] == []


def test_runtime_telemetry_logout_independent_and_scan_stale_clear(site, monkeypatch):
    client, _, runtime, _ = site
    csrf = bootstrap(client)
    stopped = []
    monkeypatch.setattr(runtime.receiver, "stop", lambda: stopped.append(True))
    runtime.receiver.publish("connection", connected=True)
    runtime.receiver.publish("levels", channels=[{"name": "A", "level": -25}])
    runtime.poll_once()
    assert runtime.snapshot()["channels"][0]["level"] == -25
    assert write(client, "/api/logout", {}, csrf).status_code == 200
    assert not stopped
    runtime.receiver.publish("tuning", names=["B"])
    runtime.poll_once()
    assert "level" not in runtime.snapshot()["channels"][0]


def test_launcher_rejects_insecure_lan_and_multiple_instances(tmp_path):
    with pytest.raises(SystemExit):
        server_arguments(["--project", str(tmp_path), "--host", "0.0.0.0"])
    args = server_arguments(["--project", str(tmp_path)])
    assert args.origin == "http://127.0.0.1:8765"
    with project_lease(tmp_path):
        with pytest.raises((ValueError, OSError)):
            with project_lease(tmp_path):
                pytest.fail("Two server instances acquired same project")
    with project_lease(tmp_path):
        pass  # restart after releasing the process lock


def test_store_defends_non_admin_writer_and_empty_password(site):
    client, accounts, _, _ = site
    csrf = bootstrap(client)
    add_user(client, csrf)
    login(client, "operator")
    principal = accounts.authenticate(client.cookies[COOKIE])
    with pytest.raises(AuthError, match="Yönetici"):
        accounts.save(
            actor=principal,
            username="intruder",
            password=PASSWORD,
            admin=True,
            enabled=True,
            permissions=[],
            all_channels=True,
            channels=[],
        )


def test_allowed_older_location_survives_newer_private_channel(site):
    client, _, runtime, _ = site
    csrf = bootstrap(client)
    add_user(client, csrf, permissions=["map.view"])
    runtime.inbox.add(
        {
            "channel": "A",
            "source_id": 3737,
            "text": "Enlem: N 40.1° Boylam: E 29.2°",
            "observed_utc": "2026-10-01T07:00:00+00:00",
        },
        "test",
        "allowed",
    )
    runtime.locations.latest = {
        "channel": "B",
        "source_id": 4000,
        "latitude": 42,
        "longitude": 35,
        "observed_utc": "2026-10-01T08:00:00+00:00",
    }
    login(client, "operator")
    point = client.get("/api/map/location").json()["location"]
    assert point["channel"] == "A" and point["latitude"] == 40.1

    # The inbox index can lag behind a live decoded position on the same channel.
    runtime.locations.latest.update(
        channel="A", latitude=40.2, observed_utc="2026-10-01T09:00:00+00:00"
    )
    assert client.get("/api/map/location").json()["location"]["latitude"] == 40.2
    runtime.locations.latest["observed_utc"] = "2026-10-01T06:00:00+00:00"
    assert client.get("/api/map/location").json()["location"]["latitude"] == 40.1


def test_audio_does_not_drop_normal_thirteen_packet_poll_window():
    audio = BrowserAudio()
    for _ in range(13):
        audio.feed("A", "analog", np.ones(273, dtype=np.float32) * 0.1, 16000, "Analog")
    assert len(audio.packets("A", "analog", 0)["packets"]) == 13


def test_hytera_async_failure_reaches_client_and_clears_connection(site):
    client, _, runtime, _ = site
    bootstrap(client)
    runtime.hytera.notify({"kind": "snapshot", "linked": 4})
    runtime.hytera.notify({"kind": "error", "text": "UDP portu kullanımda"})
    runtime.hytera.notify({"kind": "stopped", "text": "Hytera alımı kapalı"})
    runtime.poll_once()
    assert not runtime.repeater
    assert "UDP portu" in client.get("/api/repeater").json()["receiver_status"]


def test_sdr_async_error_survives_stopped_event(site):
    client, _, runtime, _ = site
    bootstrap(client)
    runtime.receiver.publish("connection", connected=True)
    runtime.receiver.publish("error", text="USB alıcı açılamadı")
    runtime.receiver.publish("stopped")
    runtime.poll_once()
    snapshot = client.get("/api/live").json()
    assert "USB alıcı açılamadı" in snapshot["status"]
    assert all(not channel["connected"] for channel in snapshot["channels"])


def test_startup_failure_still_closes_runtime(site, monkeypatch):
    _, accounts, runtime, _ = site
    accounts.bootstrap("admin", PASSWORD)
    (accounts.path.parent / "startup.json").write_text("not json", "utf-8")
    events = []
    monkeypatch.setattr(runtime, "start", lambda: events.append("start"))
    monkeypatch.setattr(runtime, "close", lambda: events.append("closed"))
    app = create_app(runtime, accounts, origin=ORIGIN)
    with pytest.raises(ValueError):
        with TestClient(app, base_url=ORIGIN):
            pass
    assert events == ["start", "closed"]


def test_shutdown_waits_for_slow_recording_finalization(site):
    _, _, runtime, _ = site

    class FinalizingThread:
        def __init__(self):
            self.waits = 0

        def is_alive(self):
            return self.waits < 3

        def join(self, timeout=None):
            self.waits += 1

    worker = FinalizingThread()
    runtime.receiver.thread = worker
    runtime.close()
    assert not worker.is_alive()


def test_background_lifecycle_and_tls_cookie(site, monkeypatch):
    _, accounts, runtime, _ = site
    events = []
    monkeypatch.setattr(runtime, "start", lambda: events.append("start"))
    monkeypatch.setattr(runtime, "close", lambda: events.append("close"))
    accounts.bootstrap("admin", PASSWORD)
    app = create_app(runtime, accounts, origin="https://radio.test:8765")
    with TestClient(app, base_url="https://radio.test:8765") as client:
        r = client.post(
            "/api/login",
            json={"username": "admin", "password": PASSWORD},
            headers={"Origin": "https://radio.test:8765"},
        )
        assert r.status_code == 200
        cookie = r.headers["set-cookie"]
        assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=strict" in cookie
        assert client.get("/api/me").status_code == 200
    assert events == ["start", "close"]
