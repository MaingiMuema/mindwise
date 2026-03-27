from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.repositories import JobRepository
from app.schemas.job import (
    JobLogRead,
    JobRead,
    JobStatusRead,
    RetryJobRequest,
    SceneRead,
    SceneRerenderRequest,
)
from app.schemas.planning import VideoSpec
from app.services.jobs import JobService

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusRead)
def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobStatusRead:
    job = JobRepository(db).get_owned(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    video_spec = None
    render_plan = job.render_plan_json or {}
    if render_plan.get("video_spec"):
        video_spec = VideoSpec.model_validate(render_plan["video_spec"])
    return JobStatusRead(
        job=JobRead.model_validate(job),
        scenes=[SceneRead.model_validate(scene) for scene in sorted(job.scenes, key=lambda row: row.order_index)],
        video_spec=video_spec,
    )


@router.get("/{job_id}/scenes", response_model=list[SceneRead])
def list_job_scenes(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SceneRead]:
    job = JobRepository(db).get_owned(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return [SceneRead.model_validate(scene) for scene in sorted(job.scenes, key=lambda row: row.order_index)]


@router.get("/{job_id}/logs", response_model=list[JobLogRead])
def list_job_logs(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobLogRead]:
    job = JobRepository(db).get_owned(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    logs = JobService(db).list_logs(job_id)
    return [JobLogRead.model_validate(log) for log in logs]


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(
    job_id: str,
    payload: RetryJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobRead:
    repo = JobRepository(db)
    job = repo.get_owned(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    JobService(db).retry_job(job_id=job_id, payload=payload)
    refreshed = repo.get_owned(job_id, current_user.id)
    return JobRead.model_validate(refreshed)


@router.post("/{job_id}/scenes/{scene_id}/rerender", response_model=JobRead)
def rerender_job_scene(
    job_id: str,
    scene_id: str,
    payload: SceneRerenderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobRead:
    repo = JobRepository(db)
    job = repo.get_owned(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    JobService(db).rerender_scene(job_id=job_id, scene_id=scene_id, payload=payload)
    refreshed = repo.get_owned(job_id, current_user.id)
    return JobRead.model_validate(refreshed)
