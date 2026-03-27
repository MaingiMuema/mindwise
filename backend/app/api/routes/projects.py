from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.repositories import ProjectRepository
from app.schemas.job import JobCreateRequest, JobRead
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.jobs import JobService

router = APIRouter()


@router.get("", response_model=list[ProjectRead])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectRead]:
    projects = ProjectRepository(db).list_for_user(current_user.id)
    return [ProjectRead.model_validate(project) for project in projects]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    repo = ProjectRepository(db)
    project = repo.create(current_user, payload)
    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    project = ProjectRepository(db).get_owned(project_id, current_user.id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    repo = ProjectRepository(db)
    project = repo.get_owned(project_id, current_user.id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    repo.update(project, payload)
    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/jobs", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    project_id: str,
    payload: JobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobRead:
    project = ProjectRepository(db).get_owned(project_id, current_user.id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    job = JobService(db).create_job(user=current_user, project=project, payload=payload)
    return JobRead.model_validate(job)
