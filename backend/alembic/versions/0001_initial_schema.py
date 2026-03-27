"""Initial MindWise schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-27 19:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


source_type_enum = sa.Enum("prompt", "document", "lesson_request", name="sourcetype")
project_status_enum = sa.Enum("draft", "active", "completed", "failed", name="projectstatus")
visual_style_enum = sa.Enum(
    "clean_academic",
    "modern_infographic",
    "cinematic_technical",
    "playful_educational",
    "startup_explainer",
    name="visualstyle",
)
job_type_enum = sa.Enum("full_render", "preview", name="jobtype")
job_status_enum = sa.Enum(
    "pending",
    "planning",
    "queued",
    "running",
    "composing",
    "completed",
    "failed",
    "canceled",
    name="jobstatus",
)
scene_status_enum = sa.Enum(
    "pending",
    "ready",
    "rendering",
    "completed",
    "failed",
    "skipped",
    name="scenestatus",
)
asset_status_enum = sa.Enum("pending", "ready", "failed", name="assetstatus")
asset_type_enum = sa.Enum(
    "image",
    "icon",
    "audio",
    "subtitle",
    "plot",
    "document",
    "video",
    name="assettype",
)
output_file_type_enum = sa.Enum(
    "scene_video",
    "final_video",
    "audio",
    "subtitle",
    "diagnostics",
    name="outputfiletype",
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("picture_url", sa.String(length=500), nullable=True),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("provider_subject"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_provider_subject", "users", ["provider_subject"], unique=False)

    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("source_document_path", sa.String(length=500), nullable=True),
        sa.Column("requested_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("visual_style", visual_style_enum, nullable=False),
        sa.Column("topic_domain", sa.String(length=128), nullable=True),
        sa.Column("status", project_status_enum, nullable=False),
        sa.Column("scene_plan_version", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_projects_title", "projects", ["title"], unique=False)
    op.create_index("ix_projects_user_id", "projects", ["user_id"], unique=False)

    op.create_table(
        "video_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", job_type_enum, nullable=False),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column("target_resolution", sa.String(length=32), nullable=False),
        sa.Column("requested_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("llm_provider", sa.String(length=64), nullable=False),
        sa.Column("tts_provider", sa.String(length=64), nullable=False),
        sa.Column("image_generation_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("progress_pct", sa.Float(), nullable=False),
        sa.Column("render_plan_json", sa.JSON(), nullable=False),
        sa.Column("current_step", sa.String(length=128), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_video_jobs_project_id", "video_jobs", ["project_id"], unique=False)
    op.create_index("ix_video_jobs_status", "video_jobs", ["status"], unique=False)

    op.create_table(
        "output_files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("video_jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scene_id", sa.String(length=36), nullable=True),
        sa.Column("file_type", output_file_type_enum, nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_output_files_project_id", "output_files", ["project_id"], unique=False)

    op.create_table(
        "scene_specs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("video_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("scene_type", sa.String(length=64), nullable=False),
        sa.Column("learning_objective", sa.Text(), nullable=False),
        sa.Column("narration_text", sa.Text(), nullable=False),
        sa.Column("estimated_duration_seconds", sa.Float(), nullable=False),
        sa.Column("renderer_key", sa.String(length=64), nullable=False),
        sa.Column("spec_json", sa.JSON(), nullable=False),
        sa.Column("status", scene_status_enum, nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("output_file_id", sa.String(length=36), sa.ForeignKey("output_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scene_specs_job_id", "scene_specs", ["job_id"], unique=False)
    op.create_index("ix_scene_specs_order_index", "scene_specs", ["order_index"], unique=False)
    op.create_index("ix_scene_specs_project_id", "scene_specs", ["project_id"], unique=False)
    op.create_foreign_key(
        "fk_output_files_scene_id",
        "output_files",
        "scene_specs",
        ["scene_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=False),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("state_nonce", sa.String(length=255), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_sessions_refresh_token_hash", "auth_sessions", ["refresh_token_hash"], unique=False)
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)

    op.create_table(
        "render_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("video_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scene_id", sa.String(length=36), sa.ForeignKey("scene_specs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("attempt_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("worker_name", sa.String(length=128), nullable=True),
        sa.Column("log_excerpt", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_render_attempts_job_id", "render_attempts", ["job_id"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("video_jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scene_id", sa.String(length=36), sa.ForeignKey("scene_specs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("asset_type", asset_type_enum, nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("local_path", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("status", asset_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "log_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("video_jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scene_id", sa.String(length=36), sa.ForeignKey("scene_specs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("event", sa.String(length=128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "usage_stats",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("video_jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("metric_name", sa.String(length=64), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("usage_stats")
    op.drop_table("log_entries")
    op.drop_table("assets")
    op.drop_index("ix_render_attempts_job_id", table_name="render_attempts")
    op.drop_table("render_attempts")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_refresh_token_hash", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_scene_specs_project_id", table_name="scene_specs")
    op.drop_index("ix_scene_specs_order_index", table_name="scene_specs")
    op.drop_index("ix_scene_specs_job_id", table_name="scene_specs")
    op.drop_constraint("fk_output_files_scene_id", "output_files", type_="foreignkey")
    op.drop_table("scene_specs")
    op.drop_index("ix_output_files_project_id", table_name="output_files")
    op.drop_table("output_files")
    op.drop_index("ix_video_jobs_status", table_name="video_jobs")
    op.drop_index("ix_video_jobs_project_id", table_name="video_jobs")
    op.drop_table("video_jobs")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_index("ix_projects_title", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_users_provider_subject", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
