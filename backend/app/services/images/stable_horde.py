from base64 import b64decode
from hashlib import sha256
from pathlib import Path
import time

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.services.storage import LocalStorage


class StableHordeImageAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = LocalStorage(self.settings.assets_root)

    def enabled(self) -> bool:
        return self.settings.image_generation_enabled and bool(self.settings.stablehorde_api_key)

    def generate(
        self,
        *,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        timeout_seconds: int = 300,
    ) -> str | None:
        if not self.enabled():
            return None

        cache_key = sha256(f"{prompt}:{width}:{height}:{steps}".encode("utf-8")).hexdigest()
        relative_path = f"stable-horde/{cache_key}.png"
        cached_path = self.storage.resolve(relative_path)
        if cached_path.exists():
            return cached_path.as_posix()

        headers = {"apikey": self.settings.stablehorde_api_key or "", "Client-Agent": "MindWise/0.1"}
        submit = httpx.post(
            f"{self.settings.stable_horde_base_url}/generate/async",
            headers=headers,
            json={
                "prompt": prompt,
                "params": {"width": width, "height": height, "steps": steps},
                "nsfw": False,
                "trusted_workers": False,
                "models": [],
            },
            timeout=45.0,
        )
        submit.raise_for_status()
        request_id = submit.json()["id"]

        started_at = time.time()
        while time.time() - started_at < timeout_seconds:
            status_response = httpx.get(
                f"{self.settings.stable_horde_base_url}/generate/status/{request_id}",
                headers=headers,
                timeout=45.0,
            )
            status_response.raise_for_status()
            payload = status_response.json()
            if payload.get("done"):
                generations = payload.get("generations") or []
                if not generations:
                    raise ExternalServiceError("Stable Horde completed without returning an image.")
                image_path = self._persist_generation(generations[0], relative_path)
                return image_path.as_posix()
            time.sleep(5)

        raise ExternalServiceError("Stable Horde image generation timed out.")

    def _persist_generation(self, generation: dict, relative_path: str) -> Path:
        if generation.get("img"):
            image_data = generation["img"]
            if image_data.startswith("http"):
                response = httpx.get(image_data, timeout=45.0)
                response.raise_for_status()
                return self.storage.write_bytes(relative_path, response.content)
            return self.storage.write_bytes(relative_path, b64decode(image_data))
        raise ExternalServiceError("Stable Horde generation payload did not contain image data.")
