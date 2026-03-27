from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Asset, OutputFile, SceneSpec, VideoJob
from app.models.enums import AssetStatus, AssetType, JobStatus, JobType, OutputFileType, SceneStatus
from app.repositories import JobRepository
from app.schemas.planning import SceneSpecModel
from app.services.assets import IconService
from app.services.composition import FFmpegComposer
from app.services.images import StableHordeImageAdapter
from app.services.monitoring import DiagnosticsService
from app.services.rendering import SceneRenderEngine
from app.services.subtitles import SubtitleService
from app.services.tts import TTSService


class VideoJobPipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRepository(db)
        self.diag = DiagnosticsService(db)
        self.icon_service = IconService()
        self.image_service = StableHordeImageAdapter()
        self.tts = TTSService()
        self.subtitles = SubtitleService()
        self.renderer = SceneRenderEngine()
        self.composer = FFmpegComposer()

    def run(self, job_id: str) -> str:
        job = self.jobs.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} was not found.")

        job.status = JobStatus.RUNNING
        job.started_at = job.started_at or datetime.now(UTC)
        job.failed_at = None
        job.error_message = None
        self.diag.log(level="info", event="job.started", message="Video job started.", job_id=job.id)
        self.db.commit()

        scene_clip_paths: list[str] = []
        ordered_scenes = sorted(job.scenes, key=lambda row: row.order_index)
        for scene in ordered_scenes:
            if scene.status == SceneStatus.COMPLETED and scene.output_file_id and scene.output_file:
                scene_clip_paths.append(scene.output_file.storage_path)
                continue
            clip_path = self._process_scene(job, scene)
            scene_clip_paths.append(clip_path)
            self._update_progress(job)

        job.status = JobStatus.COMPOSING
        job.current_step = "final-compose"
        self.db.commit()

        final_path = self.composer.concat(job_id=job.id, scene_clip_paths=scene_clip_paths)
        final_file = OutputFile(
            project_id=job.project_id,
            job_id=job.id,
            file_type=OutputFileType.FINAL_VIDEO,
            storage_path=final_path,
            mime_type="video/mp4",
            size_bytes=Path(final_path).stat().st_size if Path(final_path).exists() else None,
        )
        self.db.add(final_file)
        job.status = JobStatus.COMPLETED
        job.progress_pct = 100.0
        job.completed_at = datetime.now(UTC)
        job.current_step = "completed"
        self.diag.log(level="info", event="job.completed", message="Video job completed.", job_id=job.id)
        self.db.commit()
        return final_path

    def rerender_scene(self, job_id: str, scene_id: str) -> str:
        job = self.jobs.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} was not found.")
        scene = self.jobs.get_scene(scene_id, job_id=job_id)
        if scene is None:
            raise ValueError(f"Scene {scene_id} was not found.")
        return self._process_scene(job, scene, force=True)

    def _process_scene(self, job: VideoJob, scene: SceneSpec, force: bool = False) -> str:
        if not force and scene.status == SceneStatus.COMPLETED and scene.output_file:
            return scene.output_file.storage_path

        attempt = self.jobs.create_attempt(job.id, scene.id, worker_name="celery")
        attempt.started_at = datetime.now(UTC)
        scene.status = SceneStatus.RENDERING
        job.current_step = f"scene:{scene.order_index}"
        self.db.commit()

        try:
            spec = SceneSpecModel.model_validate(scene.spec_json)
            spec = self._hydrate_assets(job, scene, spec)
            synthesis = self.tts.synthesize(
                scene_id=scene.id,
                text=spec.narration.text,
                requested_provider=job.tts_provider,
                voice=spec.narration.voice,
            )
            subtitle_path = self.subtitles.generate(
                scene_id=scene.id,
                text=spec.narration.text,
                duration_seconds=synthesis.duration_seconds,
            )
            render_result = self.renderer.render(spec, preview=job.job_type == JobType.PREVIEW)
            clip_path = self.composer.compose_scene_clip(
                scene_id=scene.id,
                video_path=render_result.output_path or "",
                audio_path=synthesis.path,
                subtitle_path=subtitle_path,
            )
            output = OutputFile(
                project_id=job.project_id,
                job_id=job.id,
                scene_id=scene.id,
                file_type=OutputFileType.SCENE_VIDEO,
                storage_path=clip_path,
                mime_type="video/mp4",
                duration_seconds=synthesis.duration_seconds,
                size_bytes=Path(clip_path).stat().st_size if Path(clip_path).exists() else None,
            )
            self.db.add(output)
            self.db.flush()

            scene.output_file_id = output.id
            scene.status = SceneStatus.COMPLETED
            scene.last_error = None
            scene.spec_json = spec.model_dump(mode="json")
            attempt.status = "completed"
            attempt.completed_at = datetime.now(UTC)
            self.diag.log(
                level="info",
                event="scene.completed",
                message=f"Scene {scene.order_index} rendered successfully.",
                job_id=job.id,
                scene_id=scene.id,
            )
            self.db.commit()
            return clip_path
        except Exception as exc:
            attempt.status = "failed"
            attempt.completed_at = datetime.now(UTC)
            attempt.error_message = str(exc)
            scene.status = SceneStatus.FAILED
            scene.last_error = str(exc)
            job.status = JobStatus.FAILED
            job.failed_at = datetime.now(UTC)
            job.error_message = str(exc)
            self.diag.log(
                level="error",
                event="scene.failed",
                message="Scene rendering failed.",
                job_id=job.id,
                scene_id=scene.id,
                payload={"error": str(exc)},
            )
            self.db.commit()
            raise

    def _hydrate_assets(self, job: VideoJob, scene: SceneSpec, spec: SceneSpecModel) -> SceneSpecModel:
        visuals = list(spec.visuals)
        for asset in spec.assets:
            path: str | None = None
            if asset.asset_type == "icon":
                icon_name = asset.icon_name or self.icon_service.pick_icon(list(asset.metadata.values()))
                path = self.icon_service.fetch_svg(icon_name)
                self._bind_asset(visuals, "icon", path)
                self._record_asset(job, scene, AssetType.ICON, "iconify", path, {"icon_name": icon_name})
            elif asset.asset_type == "image" and asset.prompt:
                path = self.image_service.generate(prompt=asset.prompt)
                if path:
                    self._bind_asset(visuals, "image", path)
                    self._record_asset(job, scene, AssetType.IMAGE, "stable_horde", path, {"prompt": asset.prompt})
        return spec.model_copy(update={"visuals": visuals})

    def _bind_asset(self, visuals, kind: str, path: str) -> None:
        for visual in visuals:
            if visual.kind == kind:
                visual.metadata["asset_path"] = path
                return

    def _record_asset(
        self,
        job: VideoJob,
        scene: SceneSpec,
        asset_type: AssetType,
        provider: str,
        path: str,
        metadata: dict,
    ) -> None:
        asset = Asset(
            project_id=job.project_id,
            job_id=job.id,
            scene_id=scene.id,
            asset_type=asset_type,
            provider=provider,
            local_path=path,
            metadata_json=metadata,
            status=AssetStatus.READY,
        )
        self.db.add(asset)

    def _update_progress(self, job: VideoJob) -> None:
        total = max(1, len(job.scenes))
        completed = sum(1 for scene in job.scenes if scene.status == SceneStatus.COMPLETED)
        job.progress_pct = round((completed / total) * 100, 1)
        self.db.commit()
