from app.core.database import SessionLocal
from app.models import Project, User
from app.models.enums import ProjectStatus, SourceType, VisualStyle


def main() -> None:
    db = SessionLocal()
    try:
        user = User(
            email="demo@mindwise.local",
            full_name="MindWise Demo",
            provider_subject="demo-seed-user",
            provider="google",
            is_active=True,
        )
        db.add(user)
        db.flush()

        project = Project(
            user_id=user.id,
            title="Backpropagation Explained",
            prompt="Explain backpropagation from intuition to chain rule to gradient flow using diagrams, equations, and plots.",
            source_type=SourceType.PROMPT,
            requested_duration_minutes=8,
            visual_style=VisualStyle.CLEAN_ACADEMIC,
            topic_domain="ai_ml",
            status=ProjectStatus.DRAFT,
            scene_plan_version=1,
            metadata_json={"seed": True},
        )
        db.add(project)
        db.commit()
        print(f"Seeded demo user={user.id} project={project.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
