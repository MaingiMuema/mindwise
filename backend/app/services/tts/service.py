from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import wave

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.services.storage import LocalStorage


@dataclass(slots=True)
class SynthesisResult:
    path: str
    duration_seconds: float
    provider: str


class BaseTTSProvider:
    name = "base"

    def synthesize(self, *, text: str, output_path: Path, voice: str | None = None) -> SynthesisResult:
        raise NotImplementedError


class DummyTTSProvider(BaseTTSProvider):
    name = "dummy"

    def synthesize(self, *, text: str, output_path: Path, voice: str | None = None) -> SynthesisResult:
        words = max(1, len(text.split()))
        duration_seconds = max(2.0, round(words / 2.5, 2))
        sample_rate = 22050
        n_frames = int(duration_seconds * sample_rate)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(output_path.as_posix(), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00\x00" * n_frames)
        return SynthesisResult(path=output_path.as_posix(), duration_seconds=duration_seconds, provider=self.name)


class PiperTTSProvider(BaseTTSProvider):
    name = "piper"

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def available(self) -> bool:
        return bool(self.settings.piper_model_path and shutil.which(self.settings.piper_binary))

    def synthesize(self, *, text: str, output_path: Path, voice: str | None = None) -> SynthesisResult:
        if not self.available:
            raise ExternalServiceError("Piper is not available. Configure PIPER_MODEL_PATH and install piper.")

        command = [
            self.settings.piper_binary,
            "--model",
            voice or self.settings.piper_model_path or "",
            "--output_file",
            output_path.as_posix(),
        ]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, input=text.encode("utf-8"), check=True)
        duration_seconds = max(2.0, round(len(text.split()) / 2.5, 2))
        return SynthesisResult(path=output_path.as_posix(), duration_seconds=duration_seconds, provider=self.name)


class TTSService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = LocalStorage(self.settings.assets_root)
        self.piper = PiperTTSProvider()
        self.dummy = DummyTTSProvider()

    def select_provider(self, requested: str | None = None) -> BaseTTSProvider:
        if requested == "dummy":
            return self.dummy
        if requested == "piper" and self.piper.available:
            return self.piper
        if self.piper.available:
            return self.piper
        return self.dummy

    def synthesize(
        self,
        *,
        scene_id: str,
        text: str,
        requested_provider: str | None = None,
        voice: str | None = None,
    ) -> SynthesisResult:
        provider = self.select_provider(requested_provider)
        output_path = self.storage.resolve(f"audio/{scene_id}.wav")
        return provider.synthesize(text=text, output_path=output_path, voice=voice)
