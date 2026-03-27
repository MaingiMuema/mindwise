from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ProjectStatus, SourceType, VisualStyle


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.PROMPT)
    source_document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_duration_minutes: Mapped[int] = mapped_column(Integer, default=5)
    visual_style: Mapped[VisualStyle] = mapped_column(
        Enum(VisualStyle),
        default=VisualStyle.CLEAN_ACADEMIC,
    )
    topic_domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    scene_plan_version: Mapped[int] = mapped_column(Integer, default=1)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    user = relationship("User", back_populates="projects")
    jobs = relationship("VideoJob", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="project")
    output_files = relationship("OutputFile", back_populates="project")
    usage_stats = relationship("UsageStat", back_populates="project")
