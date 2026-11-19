"""Linktomp3 – muuntaa YouTube-linkit ladattaviksi mp3-tiedostoiksi."""

from .core import ConversionError, Mp3Result, download_mp3, is_youtube_url

__all__ = ["ConversionError", "Mp3Result", "download_mp3", "is_youtube_url"]
__version__ = "1.0.0"
