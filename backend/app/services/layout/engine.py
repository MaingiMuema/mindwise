from dataclasses import dataclass, field
import math

from app.schemas.planning import SceneSpecModel, VisualElement


@dataclass(slots=True)
class LayoutItem:
    element_id: str
    x: float
    y: float
    width: float
    height: float
    scale: float
    page: int = 1


@dataclass(slots=True)
class LayoutPlan:
    items: list[LayoutItem]
    overflow_detected: bool
    required_pages: int
    warnings: list[str] = field(default_factory=list)


class LayoutEngine:
    def __init__(
        self,
        *,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        margin_x: int = 120,
        margin_y: int = 90,
        min_font_scale: float = 0.62,
    ) -> None:
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.min_font_scale = min_font_scale

    @property
    def safe_width(self) -> float:
        return self.viewport_width - (self.margin_x * 2)

    @property
    def safe_height(self) -> float:
        return self.viewport_height - (self.margin_y * 2)

    def fit_scene(self, scene: SceneSpecModel) -> LayoutPlan:
        items: list[LayoutItem] = []
        warnings: list[str] = []

        title_height = 120
        title_scale = max(self.min_font_scale, min(1.0, self.safe_width / max(600, len(scene.title) * 24)))
        items.append(
            LayoutItem(
                element_id="title",
                x=self.margin_x,
                y=self.margin_y,
                width=self.safe_width,
                height=title_height,
                scale=title_scale,
            )
        )

        content_elements = scene.visuals or [
            VisualElement(kind="text", content=scene.narration.text, position_hint="center")
        ]
        slot_count = max(1, len(content_elements))
        columns = 1 if slot_count <= 2 else 2
        rows = math.ceil(slot_count / columns)
        usable_height = self.safe_height - title_height - 36
        slot_width = (self.safe_width - (24 * (columns - 1))) / columns
        slot_height = (usable_height - (24 * (rows - 1))) / rows

        overflow_detected = False
        required_pages = 1
        for index, visual in enumerate(content_elements):
            column = index % columns
            row = index // columns
            width_estimate, height_estimate = self._estimate_element_size(visual, slot_width, slot_height)
            scale = min(slot_width / width_estimate, slot_height / height_estimate, 1.0)
            if scale < self.min_font_scale:
                overflow_detected = True
                required_pages = max(required_pages, math.ceil(slot_count / 2))
                warnings.append(
                    f"Element {visual.element_id} in scene '{scene.title}' exceeded layout bounds and requires pagination."
                )
                scale = self.min_font_scale

            items.append(
                LayoutItem(
                    element_id=visual.element_id,
                    x=self.margin_x + column * (slot_width + 24),
                    y=self.margin_y + title_height + 36 + row * (slot_height + 24),
                    width=min(width_estimate * scale, slot_width),
                    height=min(height_estimate * scale, slot_height),
                    scale=scale,
                )
            )

        return LayoutPlan(
            items=items,
            overflow_detected=overflow_detected,
            required_pages=required_pages,
            warnings=warnings,
        )

    def _estimate_element_size(
        self,
        visual: VisualElement,
        slot_width: float,
        slot_height: float,
    ) -> tuple[float, float]:
        content_length = len(visual.content or "") or 24
        if visual.kind == "equation":
            return min(slot_width * 1.1, 960), min(slot_height * 0.9, 220 + content_length * 1.2)
        if visual.kind in {"plot", "diagram", "geometry", "image"}:
            return min(slot_width * 0.95, 840), min(slot_height * 0.95, 520)
        if visual.kind in {"comparison", "timeline", "process_flow"}:
            return min(slot_width * 1.05, 900), min(slot_height * 0.95, 420)
        if visual.kind == "icon":
            return 220, 220
        line_estimate = math.ceil(content_length / 34)
        return min(slot_width, 700), min(slot_height * 1.2, 120 + line_estimate * 42)

    def split_scene(self, scene: SceneSpecModel) -> list[SceneSpecModel]:
        plan = self.fit_scene(scene)
        if not plan.overflow_detected:
            return [scene]

        midpoint = max(1, math.ceil(len(scene.visuals) / 2))
        parts: list[SceneSpecModel] = []
        for index, visuals in enumerate((scene.visuals[:midpoint], scene.visuals[midpoint:]), start=1):
            if not visuals:
                continue
            parts.append(
                scene.model_copy(
                    update={
                        "title": f"{scene.title} (Part {index})",
                        "visuals": visuals,
                        "diagnostics": {**scene.diagnostics, "paginated_from": scene.scene_id},
                    }
                )
            )
        return parts or [scene]
