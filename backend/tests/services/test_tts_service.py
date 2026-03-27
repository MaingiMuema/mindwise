from pathlib import Path

from app.services.tts import TTSService


def test_tts_service_uses_dummy_provider_when_piper_unavailable(monkeypatch):
    monkeypatch.delenv("PIPER_MODEL_PATH", raising=False)
    service = TTSService()
    result = service.synthesize(scene_id="scene-1", text="MindWise narration for testing.")

    assert result.provider == "dummy"
    assert Path(result.path).exists()
    assert result.duration_seconds >= 2.0
