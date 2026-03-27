from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Asset, OutputFile, Project, User, VideoJob
from app.models.enums import OutputFileType
from app.repositories import JobRepository

router = APIRouter()


@router.get("/assets/{asset_id}")
def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    statement = (
        select(Asset)
        .join(Project, Asset.project_id == Project.id)
        .where(Asset.id == asset_id, Project.user_id == current_user.id)
    )
    asset = db.scalar(statement)
    if asset is None or not asset.local_path or not Path(asset.local_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    return FileResponse(asset.local_path)


@router.get("/exports/{job_id}")
def get_export(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    job = JobRepository(db).get_owned(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    final_output = next(
        (output for output in job.output_files if output.file_type == OutputFileType.FINAL_VIDEO),
        None,
    )
    if final_output is None or not Path(final_output.storage_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Final export not found.")
    return FileResponse(final_output.storage_path, media_type="video/mp4", filename=f"{job_id}.mp4")
