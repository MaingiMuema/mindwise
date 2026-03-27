from sqlalchemy import Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AssetStatus, AssetType, OutputFileType


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    job_id: Mapped[str | None] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"))
    scene_id: Mapped[str | None] = mapped_column(ForeignKey("scene_specs.id", ondelete="CASCADE"))
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType))
    provider: Mapped[str] = mapped_column(String(64), default="local")
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.PENDING)

    project = relationship("Project", back_populates="assets")
    job = relationship("VideoJob", back_populates="assets")
    scene = relationship("SceneSpec", back_populates="assets")


class OutputFile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "output_files"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"))
    scene_id: Mapped[str | None] = mapped_column(ForeignKey("scene_specs.id", ondelete="SET NULL"))
    file_type: Mapped[OutputFileType] = mapped_column(Enum(OutputFileType))
    storage_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(128))
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    project = relationship("Project", back_populates="output_files")
    job = relationship("VideoJob", back_populates="output_files")
