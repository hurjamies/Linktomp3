"""Selainkäyttöliittymä (Flask).

Käynnistys:
    python -m linktomp3.web          # avaa http://127.0.0.1:5000
"""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from flask import Flask, abort, jsonify, render_template, request, send_file

from .core import ALLOWED_BITRATES, DEFAULT_BITRATE, ConversionError, download_mp3, is_youtube_url

MAX_DURATION = int(os.environ.get("LINKTOMP3_MAX_DURATION", 3 * 60 * 60))  # sekuntia
JOB_TTL = int(os.environ.get("LINKTOMP3_JOB_TTL", 30 * 60))  # valmiit tiedostot poistetaan
WORKERS = int(os.environ.get("LINKTOMP3_WORKERS", 3))


@dataclass
class Job:
    id: str
    url: str
    bitrate: str
    workdir: Path
    status: str = "queued"  # queued | downloading | converting | done | error
    progress: float = 0.0
    title: Optional[str] = None
    error: Optional[str] = None
    file: Optional[Path] = None
    created: float = field(default_factory=time.time)

    def public(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "progress": round(self.progress, 1),
            "title": self.title,
            "error": self.error,
            "filename": self.file.name if self.file else None,
        }


def create_app() -> Flask:
    app = Flask(__name__)
    jobs: dict[str, Job] = {}
    lock = threading.Lock()
    executor = ThreadPoolExecutor(max_workers=WORKERS)
    root = Path(tempfile.mkdtemp(prefix="linktomp3-"))

    def cleanup() -> None:
        now = time.time()
        with lock:
            expired = [j for j in jobs.values()
                       if j.status in ("done", "error") and now - j.created > JOB_TTL]
            for j in expired:
                jobs.pop(j.id, None)
        for j in expired:
            shutil.rmtree(j.workdir, ignore_errors=True)

    def run(job: Job) -> None:
        def hook(d: dict) -> None:
            if d.get("status") == "downloading":
                job.status = "downloading"
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    job.progress = min(99.0, d.get("downloaded_bytes", 0) * 100 / total)
            elif d.get("status") == "finished":
                job.status = "converting"
                job.progress = 100.0

        try:
            job.status = "downloading"
            result = download_mp3(job.url, job.workdir, job.bitrate,
                                  max_duration=MAX_DURATION, progress=hook)
            job.title, job.file, job.status = result.title, result.path, "done"
        except ConversionError as exc:
            job.error, job.status = str(exc), "error"
        except Exception as exc:  # odottamaton virhe – ei kaadeta palvelinta
            app.logger.exception("Muunnos kaatui")
            job.error, job.status = f"Odottamaton virhe: {exc}", "error"

    @app.get("/")
    def index():
        return render_template("index.html", bitrates=ALLOWED_BITRATES, default=DEFAULT_BITRATE)

    @app.post("/api/jobs")
    def create_job():
        cleanup()
        data = request.get_json(silent=True) or request.form
        url = (data.get("url") or "").strip()
        bitrate = str(data.get("bitrate") or DEFAULT_BITRATE)
        if not is_youtube_url(url):
            return jsonify(error="Anna kelvollinen YouTube-linkki."), 400
        if bitrate not in ALLOWED_BITRATES:
            return jsonify(error="Virheellinen bittinopeus."), 400

        job_id = uuid.uuid4().hex
        workdir = root / job_id
        workdir.mkdir()
        job = Job(id=job_id, url=url, bitrate=bitrate, workdir=workdir)
        with lock:
            jobs[job_id] = job
        executor.submit(run, job)
        return jsonify(job.public()), 202

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id: str):
        job = jobs.get(job_id)
        if job is None:
            return jsonify(error="Tehtävää ei löydy (se on ehkä vanhentunut)."), 404
        return jsonify(job.public())

    @app.get("/download/<job_id>")
    def download(job_id: str):
        job = jobs.get(job_id)
        if job is None or job.status != "done" or not job.file or not job.file.exists():
            abort(404)
        return send_file(job.file, mimetype="audio/mpeg", as_attachment=True,
                         download_name=job.file.name)

    return app


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    print(f"Linktomp3 käynnissä: http://{host}:{port}")
    create_app().run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
