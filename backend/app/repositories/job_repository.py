from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import LogEntry, Project, RenderAttempt, SceneSpec, VideoJob
from app.models.enums import JobStatus, SceneStatus
from app.schemas.job import JobCreateRequest
from app.schemas.planning import RenderJobPlan


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, project: Project, payload: JobCreateRequest, plan: RenderJobPlan) -> VideoJob:
        job = VideoJob(
            id=plan.job_id,
            project_id=project.id,
            job_type=payload.job_type,
            status=JobStatus.PENDING,
            target_resolution=plan.output_resolution,
            requested_duration_seconds=plan.video_spec.target_duration_seconds,
            llm_provider=plan.video_spec.llm_provider,
            tts_provider=payload.tts_provider or "auto",
            image_generation_enabled=payload.image_generation_enabled,
            render_plan_json=plan.model_dump(mode="json"),
            current_step="queued",
        )
        self.db.add(job)
        self.db.flush()

        for scene in plan.video_spec.scenes:
            self.db.add(
                SceneSpec(
                    id=scene.scene_id,
                    project_id=project.id,
                    job_id=job.id,
                    order_index=scene.order_index,
                    title=scene.title,
                    scene_type=scene.scene_type,
                    learning_objective=scene.learning_objective,
                    narration_text=scene.narration.text,
                    estimated_duration_seconds=scene.estimated_duration_seconds,
                    renderer_key=scene.renderer_key,
                    spec_json=scene.model_dump(mode="json"),
                    status=SceneStatus.READY,
                )
            )

        self.db.flush()
        return job

    def get_owned(self, job_id: str, user_id: str) -> VideoJob | None:
        statement = (
            select(VideoJob)
            .join(Project)
            .where(VideoJob.id == job_id, Project.user_id == user_id)
            .options(selectinload(VideoJob.scenes), selectinload(VideoJob.output_files))
        )
        return self.db.scalar(statement)

    def get(self, job_id: str) -> VideoJob | None:
        statement = (
            select(VideoJob)
            .where(VideoJob.id == job_id)
            .options(selectinload(VideoJob.scenes), selectinload(VideoJob.output_files))
        )
        return self.db.scalar(statement)

    def get_scene(self, scene_id: str, job_id: str | None = None) -> SceneSpec | None:
        conditions = [SceneSpec.id == scene_id]
        if job_id:
            conditions.append(SceneSpec.job_id == job_id)
        return self.db.scalar(select(SceneSpec).where(*conditions))

    def list_logs(self, job_id: str) -> Sequence[LogEntry]:
        statement = select(LogEntry).where(LogEntry.job_id == job_id).order_by(LogEntry.created_at.asc())
        return list(self.db.scalars(statement))

    def create_attempt(self, job_id: str, scene_id: str | None, worker_name: str | None) -> RenderAttempt:
        attempt = RenderAttempt(job_id=job_id, scene_id=scene_id, worker_name=worker_name)
        self.db.add(attempt)
        self.db.flush()
        return attempt
