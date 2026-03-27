from app.models.enums import VisualStyle
from app.schemas.planning import NarrationSpec, SceneSpecModel, VisualElement
from app.services.layout import LayoutEngine


def test_layout_engine_flags_overflow_and_paginates():
    engine = LayoutEngine(viewport_width=1280, viewport_height=720)
    scene = SceneSpecModel(
        order_index=1,
        title="Dense Scene",
        scene_type="concept_overview",
        learning_objective="Fit many blocks into a small viewport.",
        estimated_duration_seconds=45,
        visual_style=VisualStyle.CLEAN_ACADEMIC,
        renderer_key="concept",
        narration=NarrationSpec(text="dense scene"),
        visuals=[
            VisualElement(kind="text", content="A" * 300),
            VisualElement(kind="text", content="B" * 300),
            VisualElement(kind="text", content="C" * 300),
            VisualElement(kind="text", content="D" * 300),
            VisualElement(kind="text", content="E" * 300),
        ],
    )

    plan = engine.fit_scene(scene)
    split = engine.split_scene(scene)

    assert plan.overflow_detected is True
    assert len(split) >= 2
