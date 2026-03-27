from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "MindWise"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    timezone: str = "UTC"
    log_level: str = "INFO"
    auto_create_tables: bool = True

    database_url: str = Field(
        default="sqlite+pysqlite:///./mindwise.dev.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str | None = Field(default=None, alias="GOOGLE_REDIRECT_URI")
    jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=14, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    nvidia_api_key: str | None = Field(default=None, alias="NVIDIA_API_KEY")
    stablehorde_api_key: str | None = Field(default=None, alias="STABLEHORDE_API_KEY")
    opencode_api_key: str | None = Field(default=None, alias="OPENCODE_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    cerebras_api_key: str | None = Field(default=None, alias="CEREBRAS_API_KEY")

    llm_primary_provider: str = Field(default="heuristic", alias="LLM_PRIMARY_PROVIDER")
    image_generation_enabled: bool = Field(default=True, alias="IMAGE_GENERATION_ENABLED")
    stable_horde_base_url: str = "https://stablehorde.net/api/v2"
    iconify_base_url: str = "https://api.iconify.design"
    google_auth_base_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_url: str = "https://oauth2.googleapis.com/token"
    google_token_info_url: str = "https://oauth2.googleapis.com/tokeninfo"

    default_resolution: str = "1920x1080"
    piper_binary: str = "piper"
    piper_default_voice: str = Field(default="en_US-lessac-medium", alias="PIPER_DEFAULT_VOICE")
    piper_model_path: str | None = Field(default=None, alias="PIPER_MODEL_PATH")
    ffmpeg_binary: str = "ffmpeg"
    manim_binary: str = "manim"

    storage_root: Path = BACKEND_DIR / "storage"
    outputs_root: Path = BACKEND_DIR / "storage/outputs"
    assets_root: Path = BACKEND_DIR / "storage/assets"
    temp_root: Path = BACKEND_DIR / "storage/tmp"
    subtitle_root: Path = BACKEND_DIR / "storage/subtitles"
    logs_root: Path = BACKEND_DIR / "storage/logs"

    diagnostics_bbox_color: str = "#ff4d4f"
    preview_quality: str = "low_quality"
    final_quality: str = "production_quality"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False
        return bool(value)

    @computed_field  # type: ignore[misc]
    @property
    def oauth_enabled(self) -> bool:
        return bool(
            self.google_client_id and self.google_client_secret and self.google_redirect_uri
        )

    @computed_field  # type: ignore[misc]
    @property
    def auth_ready(self) -> bool:
        return self.oauth_enabled and bool(self.jwt_secret_key)

    @computed_field  # type: ignore[misc]
    @property
    def storage_directories(self) -> list[Path]:
        return [
            self.storage_root,
            self.outputs_root,
            self.assets_root,
            self.temp_root,
            self.subtitle_root,
            self.logs_root,
        ]

    @property
    def missing_env_vars(self) -> list[str]:
        missing: list[str] = []
        if not self.jwt_secret_key:
            missing.append("JWT_SECRET_KEY")
        if not self.google_client_id:
            missing.append("GOOGLE_CLIENT_ID")
        if not self.google_client_secret:
            missing.append("GOOGLE_CLIENT_SECRET")
        if not self.google_redirect_uri:
            missing.append("GOOGLE_REDIRECT_URI")
        if self.image_generation_enabled and not self.stablehorde_api_key:
            missing.append("STABLEHORDE_API_KEY")
        return missing

    def ensure_directories(self) -> None:
        for path in self.storage_directories:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
