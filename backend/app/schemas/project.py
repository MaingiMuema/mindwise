from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus, SourceType, VisualStyle
from app.schemas.common import TimestampedRead


class ProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    prompt: str = Field(min_length=12)
    source_type: SourceType = SourceType.PROMPT
    requested_duration_minutes: int = Field(ge=1, le=30, default=5)
    visual_style: VisualStyle | None = None
    topic_domain: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    prompt: str | None = Field(default=None, min_length=12)
    requested_duration_minutes: int | None = Field(default=None, ge=1, le=30)
    visual_style: VisualStyle | None = None
    topic_domain: str | None = None
    status: ProjectStatus | None = None
    metadata_json: dict | None = None


class ProjectRead(TimestampedRead):
    user_id: str
    title: str
    prompt: str
    source_type: SourceType
    source_document_path: str | None = None
    requested_duration_minutes: int
    visual_style: VisualStyle
    topic_domain: str | None = None
    status: ProjectStatus
    scene_plan_version: int
    metadata_json: dict
