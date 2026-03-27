from datetime import UTC, datetime

from app.models import Project, SceneSpec, User, VideoJob
from app.models.enums import JobStatus, JobType, ProjectStatus, SceneStatus, SourceType, VisualStyle
from app.schemas.job import RetryJobRequest
from app.services.jobs import JobService


def test_retry_job_resets_failed_scenes(db_session, monkeypatch):
    user = User(
        email="retry@example.com",
        full_name="Retry User",
        picture_url=None,
        provider_subject="retry-user",
        provider="google",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    project = Project(
        user_id=user.id,
        title="Retry Project",
        prompt="Explain retry flows.",
        source_type=SourceType.PROMPT,
        requested_duration_minutes=5,
        visual_style=VisualStyle.CLEAN_ACADEMIC,
        status=ProjectStatus.ACTIVE,
        scene_plan_version=1,
        metadata_json={},
    )
    db_session.add(project)
    db_session.flush()
    job = VideoJob(
        project_id=project.id,
        job_type=JobType.FULL_RENDER,
        status=JobStatus.FAILED,
        target_resolution="1920x1080",
        requested_duration_seconds=300,
        llm_provider="heuristic",
        tts_provider="dummy",
        image_generation_enabled=False,
        progress_pct=50,
        render_plan_json={},
        current_step="failed",
        retry_count=0,
        failed_at=datetime.now(UTC),
        error_message="boom",
    )
    db_session.add(job)
    db_session.flush()
    failed_scene = SceneSpec(
        project_id=project.id,
        job_id=job.id,
        order_index=1,
        title="Broken",
        scene_type="concept_overview",
        learning_objective="Fix the failure.",
        narration_text="Broken scene narration",
        estimated_duration_seconds=30,
        renderer_key="concept",
        spec_json={},
        status=SceneStatus.FAILED,
        last_error="boom",
    )
    db_session.add(failed_scene)
    db_session.commit()

    service = JobService(db_session)
    monkeypatch.setattr(service, "enqueue", lambda *_args, **_kwargs: None)
    service.retry_job(job_id=job.id, payload=RetryJobRequest(reset_failed_scenes=True))

    db_session.refresh(job)
    db_session.refresh(failed_scene)
    assert job.status == JobStatus.QUEUED
    assert failed_scene.status == SceneStatus.READY
    assert failed_scene.last_error is None
