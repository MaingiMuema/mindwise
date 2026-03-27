from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project, User
from app.models.enums import ProjectStatus, VisualStyle
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User, payload: ProjectCreate) -> Project:
        project = Project(
            user_id=user.id,
            title=payload.title,
            prompt=payload.prompt,
            source_type=payload.source_type,
            requested_duration_minutes=payload.requested_duration_minutes,
            visual_style=payload.visual_style or VisualStyle.CLEAN_ACADEMIC,
            topic_domain=payload.topic_domain,
            metadata_json=payload.metadata_json,
            status=ProjectStatus.DRAFT,
        )
        self.db.add(project)
        self.db.flush()
        return project

    def list_for_user(self, user_id: str) -> list[Project]:
        statement = select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
        return list(self.db.scalars(statement))

    def get_owned(self, project_id: str, user_id: str) -> Project | None:
        statement = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        return self.db.scalar(statement)

    def update(self, project: Project, payload: ProjectUpdate) -> Project:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(project, field, value)
        self.db.flush()
        return project
