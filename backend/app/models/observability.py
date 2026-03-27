from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class LogEntry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "log_entries"

    job_id: Mapped[str | None] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"))
    scene_id: Mapped[str | None] = mapped_column(ForeignKey("scene_specs.id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    event: Mapped[str] = mapped_column(String(128))
    message: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    job = relationship("VideoJob", back_populates="logs")
    scene = relationship("SceneSpec", back_populates="logs")


class UsageStat(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "usage_stats"

    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    job_id: Mapped[str | None] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(64))
    metric_name: Mapped[str] = mapped_column(String(64))
    metric_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), default="count")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="usage_stats")
    project = relationship("Project", back_populates="usage_stats")
    job = relationship("VideoJob", back_populates="usage_stats")
