from hashlib import sha256

import httpx

from app.core.config import get_settings
from app.services.storage import LocalStorage


ICON_FALLBACKS = {
    "mathematics": "tabler:function",
    "physics": "tabler:atom-2",
    "finance": "tabler:chart-histogram",
    "computer_science": "tabler:brackets-angle",
    "ai_ml": "tabler:brain",
    "chemistry": "tabler:flask",
    "general_explainer": "tabler:bulb",
}


class IconService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = LocalStorage(self.settings.assets_root)

    def pick_icon(self, tags: list[str]) -> str:
        for tag in tags:
            if tag in ICON_FALLBACKS:
                return ICON_FALLBACKS[tag]
        return ICON_FALLBACKS["general_explainer"]

    def fetch_svg(self, icon_name: str, color: str = "#0f172a") -> str:
        cache_key = sha256(f"{icon_name}:{color}".encode("utf-8")).hexdigest()
        relative_path = f"icons/{cache_key}.svg"
        path = self.storage.resolve(relative_path)
        if path.exists():
            return path.as_posix()

        encoded_color = color.replace("#", "%23")
        response = httpx.get(
            f"{self.settings.iconify_base_url}/{icon_name}.svg?color={encoded_color}&width=256&height=256",
            timeout=30.0,
        )
        response.raise_for_status()
        self.storage.write_bytes(relative_path, response.content)
        return path.as_posix()
