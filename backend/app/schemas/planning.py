from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import VisualStyle

VisualElementKind = Literal[
    "title",
    "text",
    "equation",
    "plot",
    "diagram",
    "geometry",
    "comparison",
    "timeline",
    "process_flow",
    "icon",
    "image",
    "summary",
]


class VisualElement(BaseModel):
    element_id: str = Field(default_factory=lambda: str(uuid4()))
    kind: VisualElementKind
    content: str | None = None
    position_hint: str = "center"
    priority: int = 1
    max_width_ratio: float = 0.82
    max_height_ratio: float = 0.55
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnimationSpec(BaseModel):
    animation_type: str
    transition: str = "fade"
    pace: str = "steady"
    emphasis_targets: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NarrationSpec(BaseModel):
    text: str
    language: str = "en"
    voice: str | None = None
    subtitle_mode: str = "scene"
    estimated_words_per_minute: int = 145


class AssetSpec(BaseModel):
    asset_type: str
    provider: str = "local"
    prompt: str | None = None
    icon_name: str | None = None
    cache_key: str | None = None
    optional: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class SceneSpecModel(BaseModel):
    scene_id: str = Field(default_factory=lambda: str(uuid4()))
    order_index: int
    title: str
    scene_type: str
    learning_objective: str
    estimated_duration_seconds: float
    visual_style: VisualStyle
    renderer_key: str
    narration: NarrationSpec
    visuals: list[VisualElement] = Field(default_factory=list)
    animations: list[AnimationSpec] = Field(default_factory=list)
    assets: list[AssetSpec] = Field(default_factory=list)
    equations: list[str] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class VideoSpec(BaseModel):
    title: str
    objective: str
    topic_domain: str
    complexity_score: float
    target_duration_seconds: int
    estimated_total_duration_seconds: int
    scene_count: int
    style: VisualStyle
    llm_provider: str
    scenes: list[SceneSpecModel]


class RenderJobPlan(BaseModel):
    job_id: str
    project_id: str
    render_mode: str = "final"
    output_resolution: str = "1920x1080"
    image_generation_enabled: bool = True
    diagnostics_mode: bool = False
    video_spec: VideoSpec


class SceneRenderResult(BaseModel):
    scene_id: str
    status: str
    output_path: str | None = None
    audio_path: str | None = None
    subtitle_path: str | None = None
    duration_seconds: float | None = None
    warnings: list[str] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
