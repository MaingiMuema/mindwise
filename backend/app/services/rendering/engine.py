from pathlib import Path
import os
import shutil
import subprocess

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.schemas.planning import SceneRenderResult, SceneSpecModel
from app.services.storage import LocalStorage


class SceneRenderEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = LocalStorage(self.settings.outputs_root)
        self.spec_storage = LocalStorage(self.settings.temp_root)

    def render(self, scene: SceneSpecModel, *, preview: bool = False) -> SceneRenderResult:
        if not shutil.which(self.settings.manim_binary):
            raise ExternalServiceError("Manim is not installed or not available on PATH.")

        spec_path = self.spec_storage.write_text(
            f"scene-specs/{scene.scene_id}.json",
            scene.model_dump_json(indent=2),
        )
        media_dir = self.storage.resolve(f"manim/{scene.scene_id}")
        runtime_file = Path(__file__).with_name("runtime_scene.py")
        quality_flag = "-ql" if preview else "-qh"
        command = [
            self.settings.manim_binary,
            quality_flag,
            runtime_file.as_posix(),
            "MindWiseRuntimeScene",
            "--media_dir",
            media_dir.as_posix(),
        ]
        env = os.environ.copy()
        env["MINDWISE_SCENE_SPEC_PATH"] = spec_path.as_posix()
        env["PYTHONPATH"] = os.pathsep.join(
            [Path(__file__).resolve().parents[3].as_posix(), env.get("PYTHONPATH", "")]
        )
        subprocess.run(command, check=True, env=env, cwd=runtime_file.parent)
        output_path = self._find_rendered_video(media_dir)
        return SceneRenderResult(
            scene_id=scene.scene_id,
            status="completed",
            output_path=output_path,
            duration_seconds=scene.estimated_duration_seconds,
        )

    def _find_rendered_video(self, media_dir: Path) -> str:
        matches = list(media_dir.rglob("*.mp4"))
        if not matches:
            raise ExternalServiceError("Manim completed without producing an output clip.")
        return matches[-1].as_posix()
