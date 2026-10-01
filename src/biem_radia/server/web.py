"""Same-origin browser API. Every data route enforces page and channel grants."""

from __future__ import annotations

import hmac
import ipaddress
import json
import logging
import sqlite3
import threading
import time
from contextlib import asynccontextmanager, closing
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from ..hytera_metrics import METRICS, measurement_cell
from ..locations import coordinates
from ..protection import read_audio
from .auth import DEPENDENCIES, PERMISSIONS, Accounts, AuthError, Principal
from .runtime import RadioRuntime, finite_json, read_object

COOKIE = "biem_session"
ASSETS = Path(__file__).parent / "static"


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class UserForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(default="", max_length=128)
    admin: bool = False
    enabled: bool = True
    permissions: list[str] = Field(default_factory=list, max_length=30)
    all_channels: bool = False
    channels: list[str] = Field(default_factory=list, max_length=200)


class Control(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    target: Literal["receiver", "hytera", "spectrum"]
    action: Literal["start", "stop"]
    low: float = Field(default=420, ge=24, le=1700)
    high: float = Field(default=421, ge=24, le=1700)


class Startup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    receiver: bool = False
    hytera: bool = False
    snmp: bool = False


def channel_clause(user: Principal) -> tuple[str, list[str]]:
    if user.admin or user.all_channels:
        return "1=1", []
    if not user.channels:
        return "0=1", []
    return "channel IN (" + ",".join("?" for _ in user.channels) + ")", sorted(user.channels)


def create_app(
    runtime: RadioRuntime,
    accounts: Accounts,
    *,
    origin: str,
    bootstrap_secret: str = "",
    background: bool = True,
) -> FastAPI:
    parsed = urlsplit(origin)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.path:
        raise ValueError("Sunucu origin adresi http(s)://adres:port biçiminde olmalı.")
    secure = parsed.scheme == "https"
    audio_gate = threading.BoundedSemaphore(2)
    map_gate = threading.BoundedSemaphore(1)
    settings_path = accounts.path.parent / "startup.json"

    @asynccontextmanager
    async def lifespan(_app):
        try:
            if background:
                runtime.start()
                if accounts.initialized:
                    prefs = Startup(**read_object(settings_path))
                    for target in ("receiver", "hytera"):
                        if getattr(prefs, target):
                            try:
                                runtime.control(target, "start")
                            except (ValueError, OSError, KeyError):
                                logging.exception("Automatic %s startup failed", target)
                                runtime.status = f"{target}: otomatik başlangıç başarısız"
                    if prefs.snmp:
                        try:
                            profile = read_object(runtime.archive.root / "hytera.json")
                            runtime.snmp.start(profile["local_ip"], profile["repeater_ip"])
                        except (ValueError, OSError, KeyError):
                            logging.exception("Automatic SNMP startup failed")
            yield
        finally:
            if background:
                runtime.close()

    app = FastAPI(
        title="BIEM-ICC-SERVER", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )

    @app.exception_handler(AuthError)
    async def auth_error(_request: Request, exc: AuthError):
        return JSONResponse({"detail": str(exc)}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _exc: RequestValidationError):
        # FastAPI's default validation output includes submitted passwords.
        return JSONResponse({"detail": "Alanları kontrol edin; gönderilen değerler geçersiz."}, 422)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        def reject(detail, status=403):
            return JSONResponse({"detail": detail}, status_code=status)

        if request.headers.get("host", "").lower() != parsed.netloc.lower():
            response = reject("Sunucu adresi doğrulanamadı.")
        elif request.headers.get("sec-fetch-site") == "cross-site":
            response = reject("Başka bir siteden erişim engellendi.")
        elif request.method not in ("GET", "HEAD", "POST", "PUT"):
            response = reject("Bu işlem desteklenmiyor.", 405)
        elif request.method in ("POST", "PUT") and (
            request.headers.get("origin") != origin
            or request.headers.get("content-type", "").split(";")[0] != "application/json"
        ):
            response = reject("İşlemi bu sunucunun ekranından gönderin.")
        else:
            total = 0
            chunks = []
            async for chunk in request.stream():
                total += len(chunk)
                if total > 65536:
                    break
                chunks.append(chunk)
            if total > 65536:
                response = reject("İstek boyutu sınırı aşıldı.", 413)
            else:
                request._body = b"".join(chunks)
                response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' blob:; media-src 'self' blob:; connect-src 'self'; "
                "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            }
        )
        if secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    def user_for(request: Request, permission: str | None = None, *, admin=False) -> Principal:
        user = accounts.authenticate(request.cookies.get(COOKIE, ""))
        if admin and not user.admin or permission and not user.allows(permission):
            raise AuthError("Bu ekran veya işlem için yetkiniz yok.", 403)
        if request.method in ("POST", "PUT") and not hmac.compare_digest(
            request.headers.get("x-csrf-token", ""), user.csrf
        ):
            raise AuthError("Oturum doğrulanamadı; sayfayı yenileyin.", 403)
        return user

    @app.get("/")
    def index():
        return FileResponse(ASSETS / "index.html")

    @app.get("/assets/{name}")
    def static(name: str):
        if name not in ("app.js", "style.css", "logo.png"):
            raise HTTPException(404)
        return FileResponse(ASSETS / name)

    @app.get("/api/setup")
    def setup_status():
        return {"required": not accounts.initialized}

    @app.post("/api/setup")
    def setup(form: Login, request: Request):
        try:
            local = bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
        except ValueError:
            local = False
        supplied = request.headers.get("x-setup-token", "")
        if not local or not bootstrap_secret or not hmac.compare_digest(supplied, bootstrap_secret):
            raise AuthError(
                "İlk kurulum sunucu bilgisayarında açılan kurulum ekranından yapılmalı.", 403
            )
        accounts.bootstrap(form.username, form.password)
        return {"ok": True}

    @app.post("/api/login")
    def login(form: Login, request: Request, response: Response):
        token, user = accounts.login(
            form.username, form.password, request.client.host if request.client else "unknown"
        )
        response.set_cookie(
            COOKIE, token, max_age=28800, httponly=True, secure=secure, samesite="strict", path="/"
        )
        return {"user": user.public(), "csrf": user.csrf}

    @app.get("/api/me")
    def me(request: Request):
        user = user_for(request)
        return {"user": user.public(), "csrf": user.csrf}

    @app.post("/api/logout")
    def logout(request: Request, response: Response):
        user = user_for(request)
        accounts.logout(request.cookies.get(COOKIE, ""), user.username)
        response.delete_cookie(COOKIE, path="/", secure=secure, httponly=True, samesite="strict")
        return {"ok": True}

    @app.get("/api/live")
    def live(request: Request):
        user = user_for(request, "live.view")
        data = runtime.snapshot()
        data["channels"] = [c for c in data["channels"] if user.sees(c["name"])]
        if user.allows("receiver.control"):
            data["status"] = runtime.status
        return finite_json(data)

    @app.get("/api/live/audio")
    def audio(
        request: Request,
        channel: str = Query(max_length=100),
        stream: str = Query(max_length=100),
        after: int = Query(default=0, ge=0),
    ):
        user = user_for(request, "live.listen")
        if not user.sees(channel):
            raise AuthError("Kanal bulunamadı.", 404)
        return runtime.audio.packets(channel, stream, after)

    @app.post("/api/control")
    def control(form: Control, request: Request):
        permission = "spectrum.control" if form.target == "spectrum" else "receiver.control"
        user = user_for(request, permission)
        try:
            runtime.control(form.target, form.action, form.low, form.high)
        except (ValueError, OSError, KeyError) as exc:
            raise AuthError(str(exc), 409) from exc
        accounts.audit(user.username, f"{form.target}: {form.action}")
        return {"ok": True}

    @app.get("/api/calls")
    def calls(
        request: Request,
        q: str = Query(default="", max_length=100),
        offset: int = Query(default=0, ge=0, le=1000000),
    ):
        user = user_for(request, "archive.view")
        clause, params = channel_clause(user)
        with runtime.archive.connect() as db:
            rows = db.execute(
                "SELECT * FROM calls WHERE "
                + clause
                + " AND (?='' OR instr(lower(channel||' '||coalesce(radio_id,'')||' '||coalesce(group_id,'')),lower(?))>0) "
                "ORDER BY started_utc DESC,id LIMIT 101 OFFSET ?",
                (*params, q, q, offset),
            ).fetchall()
        return {
            "rows": [
                {k: r[k] for k in r.keys() if k not in ("path", "rf_power_info")}
                for r in rows[:100]
            ],
            "more": len(rows) > 100,
        }

    @app.get("/api/calls/{call_id}/audio")
    def call_audio(call_id: str, request: Request):
        user = user_for(request, "archive.play")
        with runtime.archive.connect() as db:
            row = db.execute("SELECT channel FROM calls WHERE id=?", (call_id,)).fetchone()
        if not row or not user.sees(row["channel"]):
            raise AuthError("Kayıt bulunamadı.", 404)
        if not audio_gate.acquire(blocking=False):
            raise AuthError("Ses hazırlanıyor; kısa süre sonra tekrar deneyin.", 429)
        try:
            path = runtime.archive.audio_path(call_id)
            if path.stat().st_size > 8_000_000:
                raise ValueError("Kayıt boyutu sınırı aşıldı.")
            content = read_audio(path)
        except (ValueError, OSError) as exc:
            logging.warning("Archive audio unavailable: %s", exc)
            raise AuthError(
                "Kayıt açılamadı. Sunucunun Windows hesabını ve dosyayı kontrol edin.", 409
            ) from exc
        finally:
            audio_gate.release()
        accounts.audit(user.username, "Kayıt dinleme", call_id)
        return Response(content, media_type="audio/wav")

    @app.get("/api/messages")
    def messages(
        request: Request,
        q: str = Query(default="", max_length=100),
        offset: int = Query(default=0, ge=0, le=1000000),
    ):
        user = user_for(request, "messages.view")
        clause, params = channel_clause(user)
        with closing(sqlite3.connect(runtime.inbox.database)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT id,at_local,channel,protocol,source_id,group_id,target_id,kind,text "
                "FROM messages WHERE " + clause + " AND (?='' OR instr(lower(text),lower(?))>0) "
                "ORDER BY at_local DESC,id LIMIT 101 OFFSET ?",
                (*params, q, q, offset),
            ).fetchall()
        return {"rows": [dict(r) for r in rows[:100]], "more": len(rows) > 100}

    @app.get("/api/map/location")
    def location(request: Request):
        user = user_for(request, "map.view")
        clause, params = channel_clause(user)
        candidates: list[dict] = []
        # Search persisted decoded messages within the user's scope, before considering
        # the global legacy cache. A newer private channel must not hide an allowed fix.
        with closing(sqlite3.connect(runtime.inbox.database)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT channel,text,source_id,at_local FROM messages WHERE "
                + clause
                + " AND kind NOT LIKE 'Ham veri%' AND instr(text,'Enlem:')>0 "
                "AND instr(text,'Boylam:')>0 ORDER BY at_local DESC LIMIT 1000",
                params,
            )
            for row in rows:
                point = coordinates(row["text"])
                if point is not None and row["source_id"]:
                    try:
                        observed = datetime.fromisoformat(row["at_local"]).astimezone()
                    except (ValueError, TypeError):
                        continue
                    candidates.append(
                        {
                            "latitude": point[0],
                            "longitude": point[1],
                            "source_id": row["source_id"],
                            "channel": row["channel"],
                            "observed_utc": observed.isoformat(),
                        }
                    )
                    break
        with runtime.lock:
            last = runtime.locations.latest
            if last and user.sees(last.get("channel", "")):
                candidates.append(
                    {
                        k: last[k]
                        for k in ("latitude", "longitude", "source_id", "channel", "observed_utc")
                    }
                )
        return {
            "location": max(
                candidates,
                key=lambda point: datetime.fromisoformat(point["observed_utc"]).astimezone(),
                default=None,
            )
        }

    @app.get("/api/map/image")
    def map_image(
        request: Request,
        lon: float = Query(default=35, ge=24, le=46),
        lat: float = Query(default=39, ge=34, le=43),
        zoom: int = Query(default=6, ge=5, le=18),
    ):
        user_for(request, "map.view")
        if not map_gate.acquire(blocking=False):
            raise AuthError("Harita hazırlanıyor; tekrar deneyin.", 429)
        try:
            return Response(runtime.map_image(lon, lat, zoom), media_type="image/png")
        except ValueError as exc:
            raise AuthError(str(exc), 409) from exc
        finally:
            map_gate.release()

    @app.get("/api/repeater")
    def repeater(request: Request):
        user_for(request, "repeater.view")
        data = runtime.snmp.snapshot()
        for number, reading in data["measurements"].items():
            reading["label"] = METRICS.get(number, "Ölçüm")
            reading["freshness"] = measurement_cell(reading, time.monotonic(), data["running"])[1]
        return finite_json({**data, "receiver_status": runtime.repeater_status})

    @app.post("/api/repeater/rssi")
    def rssi(request: Request):
        user = user_for(request, "repeater.view")
        if not runtime.snmp.request_rssi():
            raise AuthError("SNMP kapalı veya RSSI sorgusu hâlâ sürüyor.", 409)
        accounts.audit(user.username, "RSSI okuma")
        return {"ok": True}

    @app.get("/api/spectrum")
    def spectrum(request: Request):
        user_for(request, "spectrum.view")
        with runtime.lock:
            return {"running": runtime.spectrum.running, **runtime.sweep}

    @app.get("/api/admin")
    def admin_data(request: Request):
        user_for(request, admin=True)
        return {
            "users": accounts.users(),
            "permissions": PERMISSIONS,
            "dependencies": DEPENDENCIES,
            "channels": runtime.inventory(),
            "startup": Startup(**read_object(settings_path)).model_dump(),
            "history": accounts.history(),
        }

    def save_user(form: UserForm, request: Request, user_id: int | None = None):
        actor = user_for(request, admin=True)
        if not set(form.channels) <= set(runtime.inventory()):
            raise AuthError("Kanal listesini yenileyin; bilinmeyen kanal seçildi.")
        identity = accounts.save(actor=actor, user_id=user_id, **form.model_dump())
        return {"id": identity}

    @app.post("/api/admin/users")
    def add_user(form: UserForm, request: Request):
        return save_user(form, request)

    @app.put("/api/admin/users/{user_id}")
    def update_user(user_id: int, form: UserForm, request: Request):
        return save_user(form, request, user_id)

    @app.put("/api/admin/startup")
    def startup(form: Startup, request: Request):
        actor = user_for(request, admin=True)
        with runtime.lock:
            temporary = settings_path.with_suffix(".part")
            temporary.write_text(json.dumps(form.model_dump(), indent=2), "utf-8")
            temporary.replace(settings_path)
        accounts.audit(actor.username, "Otomatik başlangıç ayarlandı")
        return {"ok": True}

    return app
