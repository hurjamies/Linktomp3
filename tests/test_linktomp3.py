import time

import pytest

import linktomp3.web as web
from linktomp3.core import ConversionError, Mp3Result, download_mp3, is_youtube_url, safe_filename


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://m.youtube.com/watch?v=dQw4w9WgXcQ&list=abc",
    "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
    "http://youtube.com/shorts/dQw4w9WgXcQ",
    "  https://www.youtube.com/watch?v=dQw4w9WgXcQ  ",
])
def test_valid_youtube_urls(url):
    assert is_youtube_url(url)


@pytest.mark.parametrize("url", [
    "", "youtube.com/watch?v=x", "ftp://youtube.com/x", "https://example.com/watch?v=x",
    "https://youtube.com.evil.com/watch?v=x", "javascript:alert(1)",
])
def test_invalid_urls(url):
    assert not is_youtube_url(url)


def test_safe_filename():
    assert safe_filename('AC/DC: "Back in Black"?') == "AC_DC_ _Back in Black__"
    assert safe_filename("   ...  ") == "audio"
    assert len(safe_filename("a" * 500)) == 150


def test_download_rejects_bad_input(tmp_path):
    with pytest.raises(ConversionError, match="YouTube"):
        download_mp3("https://example.com/x", tmp_path)
    with pytest.raises(ConversionError, match="Bittinopeu"):
        download_mp3("https://youtu.be/abc", tmp_path, bitrate="999")


@pytest.fixture
def client(monkeypatch, tmp_path):
    def fake_download(url, out_dir, bitrate, max_duration=None, progress=None):
        if "fail" in url:
            raise ConversionError("Video ei ole saatavilla.")
        progress({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100})
        progress({"status": "finished"})
        path = out_dir / "Kappale.mp3"
        path.write_bytes(b"ID3fake")
        return Mp3Result(path=path, title="Kappale", duration=10)

    monkeypatch.setattr(web, "download_mp3", fake_download)
    return web.create_app().test_client()


def _wait(client, job_id):
    for _ in range(100):
        data = client.get(f"/api/jobs/{job_id}").get_json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_web_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Linktomp3" in res.get_data(as_text=True)


def test_web_full_flow(client):
    res = client.post("/api/jobs", json={"url": "https://youtu.be/abc", "bitrate": "320"})
    assert res.status_code == 202
    data = _wait(client, res.get_json()["id"])
    assert data["status"] == "done" and data["filename"] == "Kappale.mp3"

    dl = client.get(f"/download/{data['id']}")
    assert dl.status_code == 200
    assert dl.mimetype == "audio/mpeg"
    assert "attachment" in dl.headers["Content-Disposition"]
    assert dl.data == b"ID3fake"


def test_web_error_flow(client):
    res = client.post("/api/jobs", json={"url": "https://youtu.be/fail"})
    data = _wait(client, res.get_json()["id"])
    assert data["status"] == "error" and "saatavilla" in data["error"]
    assert client.get(f"/download/{data['id']}").status_code == 404


def test_web_validation(client):
    assert client.post("/api/jobs", json={"url": "https://example.com"}).status_code == 400
    assert client.post("/api/jobs", json={"url": "https://youtu.be/a", "bitrate": "1"}).status_code == 400
    assert client.get("/api/jobs/nope").status_code == 404
    assert client.get("/download/nope").status_code == 404
