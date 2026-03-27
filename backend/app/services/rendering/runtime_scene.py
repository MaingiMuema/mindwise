import json
import os

from manim import BLACK, Scene

from app.schemas.planning import SceneSpecModel
from app.services.rendering.templates import renderer


class MindWiseRuntimeScene(Scene):
    def construct(self) -> None:
        self.camera.background_color = BLACK
        spec_path = os.environ["MINDWISE_SCENE_SPEC_PATH"]
        with open(spec_path, "r", encoding="utf-8") as file_handle:
            spec = SceneSpecModel.model_validate(json.load(file_handle))
        renderer.render(self, spec)
