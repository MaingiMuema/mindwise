from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.jobs import VideoJobPipeline


@celery_app.task(name="mindwise.run_video_job", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def run_video_job(self, job_id: str) -> str:
    db = SessionLocal()
    try:
        pipeline = VideoJobPipeline(db)
        return pipeline.run(job_id)
    finally:
        db.close()


@celery_app.task(name="mindwise.rerender_scene", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def rerender_scene(self, job_id: str, scene_id: str, diagnostics_mode: bool = False) -> str:
    db = SessionLocal()
    try:
        pipeline = VideoJobPipeline(db)
        return pipeline.rerender_scene(job_id, scene_id)
    finally:
        db.close()
