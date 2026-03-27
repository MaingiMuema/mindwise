from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Project, SceneSpec, User
from app.models.enums import JobStatus, ProjectStatus, SceneStatus
from app.repositories import JobRepository
from app.schemas.job import JobCreateRequest, RetryJobRequest, SceneRerenderRequest
from app.services.monitoring import DiagnosticsService
from app.services.planning import ScenePlanningEngine


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRepository(db)
        self.diag = DiagnosticsService(db)
        self.planner = ScenePlanningEngine()

    def create_job(self, *, user: User, project: Project, payload: JobCreateRequest):
        job_id = str(uuid4())
        plan = self.planner.plan(
            job_id=job_id,
            project_id=project.id,
            title=project.title,
            prompt=project.prompt,
            duration_minutes=payload.requested_duration_minutes or project.requested_duration_minutes,
            style=project.visual_style,
            requested_provider=payload.llm_provider,
            image_generation_enabled=payload.image_generation_enabled,
            diagnostics_mode=payload.diagnostics_mode,
        )
        job = self.jobs.create(project, payload, plan)
        project.status = ProjectStatus.ACTIVE
        self.diag.log(
            level="info",
            event="job.created",
            message="Render job created.",
            job_id=job.id,
            payload={"project_id": project.id, "user_id": user.id},
        )
        self.db.commit()
        self.enqueue(job.id)
        return job

    def enqueue(self, job_id: str) -> None:
        from app.workers.tasks import run_video_job

        run_video_job.delay(job_id)

    def retry_job(self, *, job_id: str, payload: RetryJobRequest) -> None:
        job = self.jobs.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} was not found.")
        if payload.reset_failed_scenes:
            for scene in job.scenes:
                if scene.status == SceneStatus.FAILED:
                    scene.status = SceneStatus.READY
                    scene.last_error = None
        job.status = JobStatus.QUEUED
        job.error_message = None
        job.retry_count += 1
        self.db.commit()
        self.enqueue(job.id)

    def rerender_scene(self, *, job_id: str, scene_id: str, payload: SceneRerenderRequest) -> None:
        scene = self.jobs.get_scene(scene_id, job_id=job_id)
        if scene is None:
            raise ValueError(f"Scene {scene_id} was not found.")
        scene.status = SceneStatus.READY
        scene.last_error = None
        self.db.commit()
        from app.workers.tasks import rerender_scene

        rerender_scene.delay(job_id, scene_id, payload.diagnostics_mode)

    def list_logs(self, job_id: str):
        return self.jobs.list_logs(job_id)

    def get_scene(self, job_id: str, scene_id: str) -> SceneSpec | None:
        return self.jobs.get_scene(scene_id, job_id=job_id)
