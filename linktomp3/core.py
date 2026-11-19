"""YouTube-linkin muuntaminen mp3-tiedostoksi yt-dlp:n ja ffmpegin avulla."""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import yt_dlp

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}

ALLOWED_BITRATES = ("128", "192", "256", "320")
DEFAULT_BITRATE = "192"


class ConversionError(Exception):
    """Muunnos epäonnistui (virheellinen linkki, latausvirhe tms.)."""


@dataclass
class Mp3Result:
    path: Path
    title: str
    duration: Optional[int]


def is_youtube_url(url: str) -> bool:
    """Palauttaa True, jos merkkijono näyttää YouTube-linkiltä."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    return (parsed.hostname or "").lower() in YOUTUBE_HOSTS


def safe_filename(name: str, max_len: int = 150) -> str:
    """Siivoaa tiedostonimestä merkit, jotka eivät kelpaa käyttöjärjestelmille."""
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name[:max_len].rstrip(" .") or "audio")


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise ConversionError(
            "ffmpeg puuttuu. Asenna se (esim. 'sudo apt install ffmpeg', "
            "'brew install ffmpeg' tai 'winget install ffmpeg')."
        )


def download_mp3(
    url: str,
    out_dir: str | Path,
    bitrate: str = DEFAULT_BITRATE,
    max_duration: Optional[int] = None,
    progress: Optional[Callable[[dict], None]] = None,
) -> Mp3Result:
    """Lataa YouTube-videon äänen ja tallentaa sen mp3-tiedostoksi hakemistoon out_dir.

    max_duration: hylkää videot, jotka ovat tätä pidempiä (sekunteina).
    progress: valinnainen yt-dlp:n progress hook -funktio.
    """
    url = url.strip()
    if not is_youtube_url(url):
        raise ConversionError("Linkki ei ole kelvollinen YouTube-linkki.")
    if bitrate not in ALLOWED_BITRATES:
        raise ConversionError(
            f"Bittinopeuden pitää olla jokin näistä: {', '.join(ALLOWED_BITRATES)}."
        )
    check_ffmpeg()

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_opts = {
        "quiet": True,
        "no_warnings": True,
        "logger": _SilentLogger(),  # virheet näytetään ConversionErrorin kautta
        "noplaylist": True,  # vain yksittäinen video, vaikka linkissä olisi &list=
        "noprogress": True,
    }

    # 1) Haetaan tiedot ensin, jotta pituus voidaan tarkistaa ennen latausta.
    try:
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise ConversionError(_clean_error(exc)) from exc

    if info is None:
        raise ConversionError("Videon tietoja ei saatu haettua.")
    if info.get("_type") == "playlist":
        raise ConversionError("Soittolistoja ei tueta – anna yksittäisen videon linkki.")
    if info.get("is_live"):
        raise ConversionError("Suoria lähetyksiä ei voi muuntaa.")

    duration = info.get("duration")
    if max_duration and duration and duration > max_duration:
        raise ConversionError(
            f"Video on liian pitkä ({_fmt_time(duration)}). "
            f"Enimmäispituus on {_fmt_time(max_duration)}."
        )

    title = info.get("title") or "audio"

    # 2) Ladataan paras ääniraita väliaikaiskansioon ja muunnetaan mp3:ksi.
    with tempfile.TemporaryDirectory(prefix=".linktomp3-", dir=out_dir) as tmp:
        produced = _download_audio(info, Path(tmp), bitrate, base_opts, progress)
        final = _unique_path(out_dir / f"{safe_filename(title)}.mp3")
        shutil.move(str(produced), final)
    return Mp3Result(path=final, title=title, duration=duration)


def _download_audio(info: dict, tmp: Path, bitrate: str, base_opts: dict,
                    progress: Optional[Callable[[dict], None]]) -> Path:
    opts = {
        **base_opts,
        "format": "bestaudio/best",
        "outtmpl": str(tmp / "audio.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            },
            {"key": "FFmpegMetadata", "add_metadata": True},
        ],
    }
    if progress:
        opts["progress_hooks"] = [progress]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.process_ie_result(info, download=True)
    except yt_dlp.utils.DownloadError as exc:
        raise ConversionError(_clean_error(exc)) from exc

    produced = tmp / "audio.mp3"
    if not produced.exists():
        raise ConversionError("Muunnos epäonnistui: mp3-tiedostoa ei syntynyt.")
    return produced


class _SilentLogger:
    def debug(self, msg: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    i = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def _fmt_time(seconds: int) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _clean_error(exc: Exception) -> str:
    msg = str(exc)
    msg = re.sub(r"\x1b\[[0-9;]*m", "", msg)  # ANSI-värikoodit pois
    msg = msg.replace("ERROR: ", "").strip()
    return f"Lataus epäonnistui: {msg}" if msg else "Lataus epäonnistui."
