from base64 import b64encode
from pathlib import Path

from app.services.images import StableHordeImageAdapter


class DummyResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.content = b""

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def test_stable_horde_adapter_persists_generated_image(monkeypatch):
    monkeypatch.setenv("IMAGE_GENERATION_ENABLED", "true")
    monkeypatch.setenv("STABLEHORDE_API_KEY", "fake-key")
    adapter = StableHordeImageAdapter()

    png_bytes = b"fake-png-bytes"
    status_calls = {"count": 0}

    def fake_post(*args, **kwargs):
        return DummyResponse({"id": "request-1"})

    def fake_get(url, *args, **kwargs):
        if url.endswith("/generate/status/request-1"):
            status_calls["count"] += 1
            return DummyResponse({"done": True, "generations": [{"img": b64encode(png_bytes).decode("utf-8")}]})
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("app.services.images.stable_horde.httpx.post", fake_post)
    monkeypatch.setattr("app.services.images.stable_horde.httpx.get", fake_get)
    monkeypatch.setattr("app.services.images.stable_horde.time.sleep", lambda _: None)

    path = adapter.generate(prompt="Educational diagram")

    assert path is not None
    assert Path(path).exists()
    assert Path(path).read_bytes() == png_bytes
