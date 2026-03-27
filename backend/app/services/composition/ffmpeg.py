from pathlib import Path
import shutil
import subprocess

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.services.storage import LocalStorage


class FFmpegComposer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = LocalStorage(self.settings.outputs_root)

    def available(self) -> bool:
        return bool(shutil.which(self.settings.ffmpeg_binary))

    def compose_scene_clip(
        self,
        *,
        scene_id: str,
        video_path: str,
        audio_path: str,
        subtitle_path: str | None = None,
    ) -> str:
        if not self.available():
            raise ExternalServiceError("FFmpeg is not installed or not available on PATH.")

        output = self.storage.resolve(f"scene-clips/{scene_id}.mp4")
        command = [
            self.settings.ffmpeg_binary,
            "-y",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
        ]
        if subtitle_path:
            command.extend(["-vf", f"subtitles={subtitle_path}"])
        command.append(output.as_posix())
        subprocess.run(command, check=True)
        return output.as_posix()

    def concat(self, *, job_id: str, scene_clip_paths: list[str]) -> str:
        if not self.available():
            raise ExternalServiceError("FFmpeg is not installed or not available on PATH.")

        concat_file = self.storage.write_text(
            f"concat/{job_id}.txt",
            "\n".join(f"file '{Path(path).as_posix()}'" for path in scene_clip_paths),
        )
        output = self.storage.resolve(f"final/{job_id}.mp4")
        command = [
            self.settings.ffmpeg_binary,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file.as_posix(),
            "-c",
            "copy",
            output.as_posix(),
        ]
        subprocess.run(command, check=True)
        return output.as_posix()
