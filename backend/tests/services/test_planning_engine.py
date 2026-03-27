from app.models.enums import VisualStyle
from app.services.planning import ScenePlanningEngine


def test_planning_engine_creates_long_form_math_plan():
    engine = ScenePlanningEngine()
    plan = engine.plan(
        job_id="job-1",
        project_id="project-1",
        title="Fourier Series Intuition",
        prompt="Explain Fourier series, show the derivation, connect coefficients to geometry, and visualize partial sums with equations and plots.",
        duration_minutes=12,
        style=VisualStyle.CLEAN_ACADEMIC,
        image_generation_enabled=True,
    )

    assert plan.video_spec.scene_count >= 8
    assert abs(plan.video_spec.estimated_total_duration_seconds - 720) <= 3
    assert any(scene.scene_type == "derivation" for scene in plan.video_spec.scenes)
    assert any(visual.kind == "plot" for scene in plan.video_spec.scenes for visual in scene.visuals)
