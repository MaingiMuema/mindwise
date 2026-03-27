from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import JobStatus, JobType, SceneStatus
from app.schemas.common import APIModel, TimestampedRead
from app.schemas.planning import VideoSpec


class JobCreateRequest(BaseModel):
    job_type: JobType = JobType.FULL_RENDER
    requested_duration_minutes: int | None = Field(default=None, ge=1, le=30)
    diagnostics_mode: bool = False
    image_generation_enabled: bool = True
    llm_provider: str | None = None
    tts_provider: str | None = None
    preview_only: bool = False


class SceneRead(TimestampedRead):
    project_id: str
    job_id: str
    order_index: int
    title: str
    scene_type: str
    learning_objective: str
    narration_text: str
    estimated_duration_seconds: float
    renderer_key: str
    spec_json: dict[str, Any]
    status: SceneStatus
    output_file_id: str | None = None
    last_error: str | None = None


class JobRead(TimestampedRead):
    project_id: str
    job_type: JobType
    status: JobStatus
    target_resolution: str
    requested_duration_seconds: int
    llm_provider: str
    tts_provider: str
    image_generation_enabled: bool
    progress_pct: float
    render_plan_json: dict[str, Any]
    current_step: str | None = None
    retry_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    error_message: str | None = None


class JobStatusRead(BaseModel):
    job: JobRead
    scenes: list[SceneRead]
    video_spec: VideoSpec | None = None


class SceneRerenderRequest(BaseModel):
    diagnostics_mode: bool = False


class RetryJobRequest(BaseModel):
    reset_failed_scenes: bool = True


class JobLogRead(APIModel):
    id: str
    level: str
    event: str
    message: str
    payload_json: dict[str, Any]
    created_at: datetime
