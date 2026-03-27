from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import JobStatus, JobType, SceneStatus


class VideoJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "video_jobs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), default=JobType.FULL_RENDER)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    target_resolution: Mapped[str] = mapped_column(String(32), default="1920x1080")
    requested_duration_seconds: Mapped[int] = mapped_column(Integer)
    llm_provider: Mapped[str] = mapped_column(String(64), default="heuristic")
    tts_provider: Mapped[str] = mapped_column(String(64), default="dummy")
    image_generation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    render_plan_json: Mapped[dict] = mapped_column(JSON, default=dict)
    current_step: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="jobs")
    scenes = relationship("SceneSpec", back_populates="job", cascade="all, delete-orphan")
    render_attempts = relationship("RenderAttempt", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("LogEntry", back_populates="job")
    assets = relationship("Asset", back_populates="job")
    output_files = relationship("OutputFile", back_populates="job")
    usage_stats = relationship("UsageStat", back_populates="job")


class SceneSpec(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scene_specs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"), index=True)
    order_index: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255))
    scene_type: Mapped[str] = mapped_column(String(64))
    learning_objective: Mapped[str] = mapped_column(Text)
    narration_text: Mapped[str] = mapped_column(Text)
    estimated_duration_seconds: Mapped[float] = mapped_column(Float)
    renderer_key: Mapped[str] = mapped_column(String(64))
    spec_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[SceneStatus] = mapped_column(Enum(SceneStatus), default=SceneStatus.PENDING)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    output_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("output_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    job = relationship("VideoJob", back_populates="scenes")
    render_attempts = relationship("RenderAttempt", back_populates="scene", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="scene")
    logs = relationship("LogEntry", back_populates="scene")
    output_file = relationship(
        "OutputFile",
        foreign_keys=[output_file_id],
        post_update=True,
    )


class RenderAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "render_attempts"

    job_id: Mapped[str] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"), index=True)
    scene_id: Mapped[str | None] = mapped_column(ForeignKey("scene_specs.id", ondelete="CASCADE"))
    attempt_type: Mapped[str] = mapped_column(String(64), default="scene_render")
    status: Mapped[str] = mapped_column(String(32), default="running")
    worker_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    log_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    job = relationship("VideoJob", back_populates="render_attempts")
    scene = relationship("SceneSpec", back_populates="render_attempts")
