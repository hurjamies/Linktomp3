"""Linktomp3 Windows-käynnistin.

Käynnistää selainkäyttöliittymän taustalle vapaaseen porttiin ja avaa sen omaan
sovellusikkunaansa (Microsoft Edge / Chrome --app -tila). Kun ikkuna suljetaan,
palvelin sammuu. Ajetaan pythonw:llä, joten konsoli-ikkunaa ei näy.
"""

from __future__ import annotations

import glob
import logging
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Linktomp3"
DATA.mkdir(parents=True, exist_ok=True)

logging.basicConfig(filename=DATA / "linktomp3.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
sys.stdout = sys.stderr = open(DATA / "linktomp3.log", "a", encoding="utf-8", buffering=1)
sys.path.insert(0, str(ROOT))


def ensure_ffmpeg() -> None:
    """Lisää wingetillä asennetun ffmpegin PATHiin, jos sitä ei jo löydy."""
    if shutil.which("ffmpeg"):
        return
    local = os.environ.get("LOCALAPPDATA", "")
    patterns = [
        os.path.join(local, "Microsoft", "WinGet", "Links"),
        os.path.join(local, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "*", "bin"),
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
    ]
    for pattern in patterns:
        for d in glob.glob(pattern):
            if os.path.isfile(os.path.join(d, "ffmpeg.exe")):
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                return


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def find_browser() -> str | None:
    candidates = [
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        path = os.path.expandvars(c)
        if os.path.isfile(path):
            return path
    return None


def wait_until_up(url: str, timeout: float = 20) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.2)


def main() -> None:
    ensure_ffmpeg()
    from linktomp3.web import create_app

    port = free_port()
    url = f"http://127.0.0.1:{port}/"
    app = create_app()
    threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False),
        daemon=True,
    ).start()
    wait_until_up(url)
    logging.info("Palvelin käynnissä: %s", url)

    browser = find_browser()
    if browser is None:
        # Ei Edgeä/Chromea: avataan oletusselaimeen ja pidetään palvelin päällä.
        webbrowser.open(url)
        threading.Event().wait()
        return

    # Oma profiili => oma prosessi, jonka sulkeutumista voidaan odottaa.
    profile = DATA / "browser-profile"
    downloads = Path.home() / "Downloads"
    proc = subprocess.Popen([
        browser,
        f"--app={url}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-mode",
        "--disable-features=msEdgeStartupBoost",
        "--window-size=560,760",
    ])
    proc.wait()
    logging.info("Ikkuna suljettu, sammutetaan. (Lataukset: %s)", downloads)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Käynnistin kaatui")
        raise
    os._exit(0)
