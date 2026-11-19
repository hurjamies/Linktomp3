"""Komentorivikäyttöliittymä.

Esimerkki:
    python -m linktomp3 https://www.youtube.com/watch?v=XXXXXXXXXXX -o musiikki -b 320
"""

from __future__ import annotations

import argparse
import sys

from .core import ALLOWED_BITRATES, DEFAULT_BITRATE, ConversionError, download_mp3


def _progress(d: dict) -> None:
    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        done = d.get("downloaded_bytes") or 0
        if total:
            print(f"\r  Ladataan... {done * 100 / total:5.1f} %", end="", flush=True)
    elif d.get("status") == "finished":
        print("\r  Ladattu, muunnetaan mp3:ksi...      ", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="linktomp3",
        description="Muuntaa YouTube-linkit mp3-tiedostoiksi.",
    )
    parser.add_argument("urls", nargs="*", help="Yksi tai useampi YouTube-linkki")
    parser.add_argument("-o", "--output", default="mp3", help="Kohdekansio (oletus: mp3)")
    parser.add_argument(
        "-b", "--bitrate", default=DEFAULT_BITRATE, choices=ALLOWED_BITRATES,
        help=f"mp3:n bittinopeus kbps (oletus: {DEFAULT_BITRATE})",
    )
    parser.add_argument("-f", "--file", help="Tekstitiedosto, jossa yksi linkki per rivi")
    args = parser.parse_args(argv)

    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            urls += [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    if not urls:
        try:
            entered = input("Liitä YouTube-linkki: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1
        if entered:
            urls.append(entered)
    if not urls:
        parser.error("anna vähintään yksi linkki")

    failures = 0
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        try:
            result = download_mp3(url, args.output, args.bitrate, progress=_progress)
        except ConversionError as exc:
            failures += 1
            print(f"  VIRHE: {exc}", file=sys.stderr)
            continue
        print(f"  Valmis: {result.path}")

    if len(urls) > 1:
        print(f"\nOnnistui {len(urls) - failures}/{len(urls)}.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
