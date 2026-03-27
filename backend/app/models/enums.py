from enum import Enum


class AuthProvider(str, Enum):
    GOOGLE = "google"


class SourceType(str, Enum):
    PROMPT = "prompt"
    DOCUMENT = "document"
    LESSON_REQUEST = "lesson_request"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class VisualStyle(str, Enum):
    CLEAN_ACADEMIC = "clean_academic"
    MODERN_INFOGRAPHIC = "modern_infographic"
    CINEMATIC_TECHNICAL = "cinematic_technical"
    PLAYFUL_EDUCATIONAL = "playful_educational"
    STARTUP_EXPLAINER = "startup_explainer"


class JobType(str, Enum):
    FULL_RENDER = "full_render"
    PREVIEW = "preview"


class JobStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    QUEUED = "queued"
    RUNNING = "running"
    COMPOSING = "composing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class SceneStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AssetStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class AssetType(str, Enum):
    IMAGE = "image"
    ICON = "icon"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    PLOT = "plot"
    DOCUMENT = "document"
    VIDEO = "video"


class OutputFileType(str, Enum):
    SCENE_VIDEO = "scene_video"
    FINAL_VIDEO = "final_video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    DIAGNOSTICS = "diagnostics"
