from pathlib import Path

from app.services.composition import FFmpegComposer


def test_ffmpeg_concat_writes_concat_manifest(monkeypatch):
    composer = FFmpegComposer()
    monkeypatch.setattr(composer, "available", lambda: True)
    monkeypatch.setattr("app.services.composition.ffmpeg.subprocess.run", lambda *args, **kwargs: None)

    output = composer.concat(job_id="job-123", scene_clip_paths=["C:/clips/one.mp4", "C:/clips/two.mp4"])

    manifest = composer.storage.resolve("concat/job-123.txt")
    assert manifest.exists()
    assert "one.mp4" in manifest.read_text(encoding="utf-8")
    assert output.endswith("final/job-123.mp4")
