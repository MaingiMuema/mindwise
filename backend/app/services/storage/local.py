from pathlib import Path

from app.core.config import get_settings


class LocalStorage:
    def __init__(self, root: Path | None = None) -> None:
        settings = get_settings()
        self.root = root or settings.storage_root
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self.resolve(relative_path)
        path.write_text(content, encoding="utf-8")
        return path

    def write_bytes(self, relative_path: str, content: bytes) -> Path:
        path = self.resolve(relative_path)
        path.write_bytes(content)
        return path

    def exists(self, relative_path: str) -> bool:
        return self.resolve(relative_path).exists()

    def as_uri(self, relative_path: str) -> str:
        return self.resolve(relative_path).as_posix()
