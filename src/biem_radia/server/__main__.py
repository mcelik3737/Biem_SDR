"""Single-process BIEM-ICC-SERVER launcher; localhost setup or explicit HTTPS LAN."""

from __future__ import annotations

import argparse
import contextlib
import ipaddress
import logging
import os
import secrets
import threading
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit

import uvicorn

from .auth import Accounts
from .runtime import RadioRuntime
from .web import create_app


@contextlib.contextmanager
def project_lease(root: Path):
    """OS lock releases after a crash; cannot start two servers on one archive."""
    root.mkdir(parents=True, exist_ok=True)
    handle = (root / "server.lock").open("a+b")
    try:
        handle.seek(0)
        if not handle.read(1):
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        handle.close()
        raise ValueError("Bu veri klasörü için BIEM-ICC-SERVER zaten çalışıyor.") from exc
    try:
        yield
    finally:
        handle.close()


def server_arguments(argv=None):
    parser = argparse.ArgumentParser(description="BIEM-ICC-SERVER")
    parser.add_argument(
        "--project", type=Path, required=True, help="Mevcut data ve vendor klasörlerinin kökü"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--origin", help="Tarayıcının kullanacağı tam adres: https://sunucu:8765")
    parser.add_argument("--cert", type=Path, help="PEM TLS sertifikası")
    parser.add_argument("--key", type=Path, help="PEM TLS özel anahtarı")
    parser.add_argument("--open", action="store_true", help="Yerel kurulum / giriş ekranını aç")
    args = parser.parse_args(argv)
    try:
        local = ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        parser.error("--host bir IP adresi olmalı.")
    if not 1 <= args.port <= 65535:
        parser.error("Port 1–65535 arasında olmalı.")
    if bool(args.cert) != bool(args.key):
        parser.error("TLS için --cert ve --key birlikte gerekli.")
    if not local and (not args.cert or not args.origin):
        parser.error(
            "Ağ erişimi için --cert, --key ve --origin gerekli. İlk kurulumu yerelde yapın."
        )
    scheme = "https" if args.cert else "http"
    args.origin = args.origin or f"{scheme}://127.0.0.1:{args.port}"
    parsed = urlsplit(args.origin)
    if (
        parsed.scheme != scheme
        or not parsed.hostname
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        parser.error("Origin, TLS seçimine uygun http(s)://adres:port biçiminde olmalı.")
    args.local = local
    return args


def main():
    args = server_arguments()
    root = args.project.resolve() / "data/server"
    with project_lease(root):
        logging.basicConfig(
            filename=root / "server.log",
            encoding="utf-8",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
        accounts = Accounts(root)
        if not args.local and not accounts.initialized:
            raise SystemExit(
                "Önce sunucu bilgisayarında varsayılan yerel adresle yönetici oluşturun."
            )
        setup = secrets.token_urlsafe(32) if not accounts.initialized else ""
        runtime = RadioRuntime(args.project)
        app = create_app(runtime, accounts, origin=args.origin, bootstrap_secret=setup)
        print(f"BIEM-ICC-SERVER: {args.origin}")
        if setup:
            print("İlk yönetici kurulumu bu bilgisayarın tarayıcısında açılıyor.")
        if args.open or setup:
            url = args.origin + ("/#setup=" + setup if setup else "/")
            opener = threading.Timer(2, lambda: webbrowser.open(url))
            opener.daemon = True
            opener.start()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=1,
            proxy_headers=False,
            ssl_certfile=str(args.cert) if args.cert else None,
            ssl_keyfile=str(args.key) if args.key else None,
            access_log=False,
            limit_concurrency=32,
            timeout_keep_alive=5,
        )


if __name__ == "__main__":
    main()
