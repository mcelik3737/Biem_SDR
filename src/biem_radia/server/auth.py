"""Server-owned accounts, grants and revocable sessions; no radio dependencies."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

PERMISSIONS = {
    "live.view": "Canlı kanalları gör",
    "live.listen": "Canlı sesi dinle",
    "archive.view": "Kayıt arşivini gör",
    "archive.play": "Kayıtları dinle",
    "messages.view": "Gelen mesajları gör",
    "map.view": "Harita ve konumları gör",
    "repeater.view": "Röle durumunu gör (tüm röle)",
    "spectrum.view": "Spektrumu gör (tüm RF bandı)",
    "spectrum.control": "Spektrum ölçümünü yönet",
    "receiver.control": "Alımı başlat / durdur (tüm kanallar)",
}
DEPENDENCIES = {
    "live.listen": "live.view",
    "archive.play": "archive.view",
    "spectrum.control": "spectrum.view",
}


class AuthError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class Principal:
    id: int
    username: str
    admin: bool
    permissions: frozenset[str]
    all_channels: bool
    channels: frozenset[str]
    csrf: str = ""

    def allows(self, permission: str) -> bool:
        return self.admin or permission in self.permissions

    def sees(self, channel: str) -> bool:
        return self.admin or self.all_channels or channel in self.channels

    def public(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "admin": self.admin,
            "permissions": sorted(PERMISSIONS if self.admin else self.permissions),
            "all_channels": self.admin or self.all_channels,
            "channels": sorted(self.channels),
        }


class Accounts:
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "accounts.sqlite3"
        self.hasher = PasswordHasher()
        self.dummy_hash = self.hasher.hash(secrets.token_urlsafe(32))
        with self.database() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL, admin INTEGER NOT NULL,
                    enabled INTEGER NOT NULL, permissions TEXT NOT NULL,
                    all_channels INTEGER NOT NULL, channels TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
                    csrf TEXT NOT NULL, expires REAL NOT NULL, touched REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);
                CREATE TABLE IF NOT EXISTS attempts (at REAL, address TEXT, username TEXT);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, at REAL, actor TEXT, action TEXT, target TEXT);
            """)

    @contextmanager
    def database(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @property
    def initialized(self) -> bool:
        with self.database() as db:
            return bool(db.execute("SELECT 1 FROM users LIMIT 1").fetchone())

    def _password(self, password: str) -> str:
        if not 12 <= len(password) <= 128:
            raise AuthError("Şifre 12–128 karakter olmalı.")
        return self.hasher.hash(password)

    @staticmethod
    def _username(username: str) -> str:
        username = username.strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,39}", username):
            raise AuthError("Kullanıcı adı 3–40 karakter: a-z, 0-9, nokta, tire veya alt çizgi.")
        return username

    @staticmethod
    def _grants(permissions: list[str], channels: list[str]) -> tuple[str, str]:
        if not set(permissions) <= PERMISSIONS.keys():
            raise AuthError("Bilinmeyen yetki.")
        if any(
            p in permissions and parent not in permissions for p, parent in DEPENDENCIES.items()
        ):
            raise AuthError("Dinleme/yönetim için ilgili ekranı görme yetkisi de seçilmeli.")
        if len(channels) > 200 or any(not c or len(c) > 100 for c in channels):
            raise AuthError("Geçersiz kanal listesi.")
        return json.dumps(sorted(set(permissions))), json.dumps(sorted(set(channels)))

    @staticmethod
    def _audit(db, actor: str, action: str, target: str):
        db.execute(
            "INSERT INTO audit(at,actor,action,target) VALUES(?,?,?,?)",
            (time.time(), actor, action, target),
        )

    def bootstrap(self, username: str, password: str):
        username, encoded = self._username(username), self._password(password)
        with self.database() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
                raise AuthError("İlk yönetici zaten oluşturuldu.", 409)
            db.execute("INSERT INTO users VALUES(NULL,?,?,1,1,'[]',1,'[]')", (username, encoded))
            self._audit(db, username, "İlk yönetici oluşturuldu", username)

    def login(self, username: str, password: str, address: str) -> tuple[str, Principal]:
        username = username.strip().lower()[:128]
        now = time.time()
        with self.database() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM attempts WHERE at<?", (now - 300,))
            count = db.execute(
                "SELECT count(*) FROM attempts WHERE address=? OR username=?", (address, username)
            ).fetchone()[0]
            if count >= 10:
                raise AuthError("Çok sayıda giriş denemesi. 5 dakika sonra yeniden deneyin.", 429)
            db.execute("INSERT INTO attempts VALUES(?,?,?)", (now, address, username))
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        encoded = user["password"] if user else self.dummy_hash
        try:
            valid = self.hasher.verify(encoded, password)
        except VerificationError:
            valid = False
        if not valid or not user or not user["enabled"]:
            with self.database() as db:
                self._audit(db, "—", "Başarısız giriş", username)
            raise AuthError("Kullanıcı adı veya şifre hatalı.", 401)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self.database() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
            if not current or not current["enabled"] or current["password"] != encoded:
                raise AuthError("Hesap değişti; yeniden giriş yapın.", 401)
            db.execute("DELETE FROM sessions WHERE expires<? OR touched<?", (now, now - 1800))
            db.execute(
                "DELETE FROM sessions WHERE token IN (SELECT token FROM sessions "
                "WHERE user_id=? ORDER BY touched DESC LIMIT -1 OFFSET 7)",
                (user["id"],),
            )
            db.execute(
                "INSERT INTO sessions VALUES(?,?,?,?,?)",
                (digest(token), user["id"], csrf, now + 28800, now),
            )
            db.execute("DELETE FROM attempts WHERE address=? AND username=?", (address, username))
            if self.hasher.check_needs_rehash(encoded):
                db.execute(
                    "UPDATE users SET password=? WHERE id=?",
                    (self.hasher.hash(password), user["id"]),
                )
            self._audit(db, username, "Giriş", username)
            return token, self._principal(current, csrf)

    @staticmethod
    def _principal(row, csrf: str = "") -> Principal:
        return Principal(
            row["id"],
            row["username"],
            bool(row["admin"]),
            frozenset(json.loads(row["permissions"])),
            bool(row["all_channels"]),
            frozenset(json.loads(row["channels"])),
            csrf,
        )

    def authenticate(self, token: str) -> Principal:
        now = time.time()
        with self.database() as db:
            row = db.execute(
                "SELECT u.*,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id "
                "WHERE s.token=? AND s.expires>? AND s.touched>? AND u.enabled=1",
                (digest(token), now, now - 1800),
            ).fetchone()
            if not row:
                raise AuthError("Oturum açın.", 401)
            db.execute("UPDATE sessions SET touched=? WHERE token=?", (now, digest(token)))
            return self._principal(row, row["csrf"])

    def logout(self, token: str, actor: str):
        with self.database() as db:
            db.execute("DELETE FROM sessions WHERE token=?", (digest(token),))
            self._audit(db, actor, "Çıkış", actor)

    def users(self) -> list[dict]:
        with self.database() as db:
            return [
                {**self._principal(r).public(), "enabled": bool(r["enabled"])}
                for r in db.execute("SELECT * FROM users ORDER BY username")
            ]

    def save(
        self,
        *,
        actor: Principal,
        username: str,
        password: str,
        admin: bool,
        enabled: bool,
        permissions: list[str],
        all_channels: bool,
        channels: list[str],
        user_id: int | None = None,
    ) -> int:
        if not actor.admin:
            raise AuthError("Yönetici yetkisi gerekli.", 403)
        username = self._username(username)
        grants, channel_json = self._grants(permissions, channels)
        encoded = self._password(password) if password else None
        if user_id is None and encoded is None:
            raise AuthError("Yeni kullanıcı için şifre gerekli.")
        with self.database() as db:
            db.execute("BEGIN IMMEDIATE")
            # Recheck administrator inside the write transaction (revocation race).
            current_actor = db.execute("SELECT * FROM users WHERE id=?", (actor.id,)).fetchone()
            if not current_actor or not current_actor["admin"] or not current_actor["enabled"]:
                raise AuthError("Yönetici yetkisi gerekli.", 403)
            if user_id is not None:
                old = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
                if not old:
                    raise AuthError("Kullanıcı bulunamadı.", 404)
                if old["admin"] and old["enabled"] and not (admin and enabled):
                    others = db.execute(
                        "SELECT count(*) FROM users WHERE admin=1 AND enabled=1 AND id<>?",
                        (user_id,),
                    ).fetchone()[0]
                    if not others:
                        raise AuthError("Son etkin yönetici kapatılamaz veya yetkisi kaldırılamaz.")
                encoded = encoded or old["password"]
            try:
                values = (username, encoded, admin, enabled, grants, all_channels, channel_json)
                if user_id is None:
                    result = db.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?,?,?)", values)
                    user_id = int(result.lastrowid or 0)
                else:
                    db.execute(
                        "UPDATE users SET username=?,password=?,admin=?,enabled=?,permissions=?,all_channels=?,channels=? WHERE id=?",
                        (*values, user_id),
                    )
                    db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            except sqlite3.IntegrityError as exc:
                raise AuthError("Bu kullanıcı adı zaten kullanılıyor.", 409) from exc
            self._audit(db, actor.username, "Kullanıcı / yetki kaydedildi", username)
            return user_id

    def audit(self, actor: str, action: str, target: str = ""):
        with self.database() as db:
            self._audit(db, actor, action, target)

    def history(self) -> list[dict]:
        with self.database() as db:
            return [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200")]
