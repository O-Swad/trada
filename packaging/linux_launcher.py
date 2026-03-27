"""Portable Linux launcher for the TRADA Studio Reflex app."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn
from reflex import environment


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _find_free_port(preferred: int = 3000) -> int:
    for port in range(preferred, preferred + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if candidate.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("Could not find a free local port to launch TRADA Studio.")


def main() -> None:
    root = _bundle_root()
    os.chdir(root)
    os.environ.setdefault("REFLEX_DIR", str(root / ".reflex-home"))
    (root / "storage").mkdir(parents=True, exist_ok=True)

    web_dir = root / ".web"
    if not web_dir.exists():
        raise RuntimeError(
            "Compiled frontend assets were not found. Rebuild the Linux bundle before running it."
        )

    environment.REFLEX_SKIP_COMPILE.set(True)
    environment.REFLEX_MOUNT_FRONTEND_COMPILED_APP.set(True)

    from tradeoff_app.tradeoff_app import app as reflex_app

    port = _find_free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            app=reflex_app(),
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    )

    url = f"http://127.0.0.1:{port}"

    def _open_browser() -> None:
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open_browser, daemon=True).start()
    print(f"TRADA Studio is starting at {url}")
    server.run()


if __name__ == "__main__":
    main()
