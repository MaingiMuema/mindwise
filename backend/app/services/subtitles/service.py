from pathlib import Path

from app.core.config import get_settings
from app.services.storage import LocalStorage


def _format_srt_time(seconds: float) -> str:
    millis = int((seconds % 1) * 1000)
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class SubtitleService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = LocalStorage(self.settings.subtitle_root)

    def generate(self, *, scene_id: str, text: str, duration_seconds: float) -> str:
        words = text.split()
        chunk_size = 10
        chunks = [" ".join(words[index : index + chunk_size]) for index in range(0, len(words), chunk_size)]
        chunk_duration = duration_seconds / max(1, len(chunks))
        lines: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            start = (index - 1) * chunk_duration
            end = min(duration_seconds, index * chunk_duration)
            lines.extend(
                [
                    str(index),
                    f"{_format_srt_time(start)} --> {_format_srt_time(end)}",
                    chunk,
                    "",
                ]
            )
        path = self.storage.write_text(f"{scene_id}.srt", "\n".join(lines))
        return path.as_posix()
