from dataclasses import dataclass
import math
import re

from app.models.enums import VisualStyle
from app.schemas.planning import (
    AnimationSpec,
    AssetSpec,
    NarrationSpec,
    RenderJobPlan,
    SceneSpecModel,
    VideoSpec,
    VisualElement,
)
from app.services.layout import LayoutEngine
from app.services.llm import LLMRegistry


DOMAIN_KEYWORDS = {
    "mathematics": {"equation", "calculus", "algebra", "matrix", "theorem", "proof", "integral"},
    "physics": {"force", "energy", "quantum", "motion", "field", "wave", "relativity"},
    "finance": {"market", "valuation", "risk", "portfolio", "cashflow", "stock", "bond"},
    "computer_science": {"algorithm", "runtime", "data structure", "network", "compiler", "graph"},
    "ai_ml": {"model", "training", "gradient", "neural", "embedding", "transformer"},
    "chemistry": {"reaction", "molecule", "equilibrium", "orbital", "stoichiometry"},
}

SCENE_ROTATION = [
    "title",
    "concept_overview",
    "derivation",
    "graph_plot",
    "comparison",
    "process_flow",
    "icon_explainer",
    "image_assisted",
    "summary",
]


@dataclass(slots=True)
class PlanContext:
    prompt: str
    duration_minutes: int
    style: VisualStyle
    llm_provider_name: str


class ScenePlanningEngine:
    def __init__(self) -> None:
        self.registry = LLMRegistry()
        self.layout_engine = LayoutEngine()

    def plan(
        self,
        *,
        job_id: str,
        project_id: str,
        title: str,
        prompt: str,
        duration_minutes: int,
        style: VisualStyle | None = None,
        requested_provider: str | None = None,
        image_generation_enabled: bool = True,
        diagnostics_mode: bool = False,
    ) -> RenderJobPlan:
        provider = self.registry.choose(requested_provider)
        topic_domain = self._infer_domain(prompt)
        complexity = self._estimate_complexity(prompt, duration_minutes)
        target_duration = duration_minutes * 60
        scene_count = self._estimate_scene_count(target_duration, complexity)
        effective_style = style or self._infer_style(topic_domain)
        context = PlanContext(
            prompt=prompt,
            duration_minutes=duration_minutes,
            style=effective_style,
            llm_provider_name=provider.name,
        )
        scenes = self._build_scenes(
            title=title,
            topic_domain=topic_domain,
            scene_count=scene_count,
            complexity=complexity,
            context=context,
            image_generation_enabled=image_generation_enabled,
            diagnostics_mode=diagnostics_mode,
        )
        scenes = self._rebalance_durations(scenes, target_duration)

        return RenderJobPlan(
            job_id=job_id,
            project_id=project_id,
            output_resolution="1920x1080",
            image_generation_enabled=image_generation_enabled,
            diagnostics_mode=diagnostics_mode,
            video_spec=VideoSpec(
                title=title,
                objective=f"Explain {title} clearly with structured visuals and paced narration.",
                topic_domain=topic_domain,
                complexity_score=complexity,
                target_duration_seconds=target_duration,
                estimated_total_duration_seconds=int(sum(scene.estimated_duration_seconds for scene in scenes)),
                scene_count=len(scenes),
                style=effective_style,
                llm_provider=provider.name,
                scenes=scenes,
            ),
        )

    def _infer_domain(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        scores: dict[str, int] = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            scores[domain] = sum(1 for keyword in keywords if keyword in prompt_lower)
        return max(scores, key=scores.get) if any(scores.values()) else "general_explainer"

    def _estimate_complexity(self, prompt: str, duration_minutes: int) -> float:
        math_density = len(re.findall(r"[=^_{}\\]", prompt)) * 0.2
        prompt_words = len(prompt.split())
        keyword_bonus = sum(
            1
            for keywords in DOMAIN_KEYWORDS.values()
            for keyword in keywords
            if keyword in prompt.lower()
        ) * 0.18
        duration_bonus = duration_minutes / 20
        return round(min(1.0, 0.25 + (prompt_words / 140) + keyword_bonus + duration_bonus + math_density), 2)

    def _estimate_scene_count(self, target_duration: int, complexity: float) -> int:
        base = max(4, math.ceil(target_duration / 75))
        density = math.ceil(complexity * 5)
        return min(28, max(5, base + density))

    def _infer_style(self, topic_domain: str) -> VisualStyle:
        if topic_domain in {"mathematics", "physics", "computer_science"}:
            return VisualStyle.CLEAN_ACADEMIC
        if topic_domain in {"ai_ml", "finance"}:
            return VisualStyle.MODERN_INFOGRAPHIC
        return VisualStyle.PLAYFUL_EDUCATIONAL

    def _build_scenes(
        self,
        *,
        title: str,
        topic_domain: str,
        scene_count: int,
        complexity: float,
        context: PlanContext,
        image_generation_enabled: bool,
        diagnostics_mode: bool,
    ) -> list[SceneSpecModel]:
        scene_types = self._scene_sequence(scene_count, complexity)
        scenes: list[SceneSpecModel] = []
        for index, scene_type in enumerate(scene_types, start=1):
            scene = self._make_scene(
                order_index=index,
                title=title,
                scene_type=scene_type,
                topic_domain=topic_domain,
                context=context,
                image_generation_enabled=image_generation_enabled,
                diagnostics_mode=diagnostics_mode,
            )
            scenes.extend(self.layout_engine.split_scene(scene))
        for order, scene in enumerate(scenes, start=1):
            scene.order_index = order
        return scenes

    def _scene_sequence(self, scene_count: int, complexity: float) -> list[str]:
        sequence = ["title", "concept_overview"]
        while len(sequence) < scene_count - 1:
            for scene_type in SCENE_ROTATION[2:-1]:
                if len(sequence) >= scene_count - 1:
                    break
                if complexity < 0.5 and scene_type == "derivation":
                    continue
                sequence.append(scene_type)
        sequence.append("summary")
        return sequence[:scene_count]

    def _make_scene(
        self,
        *,
        order_index: int,
        title: str,
        scene_type: str,
        topic_domain: str,
        context: PlanContext,
        image_generation_enabled: bool,
        diagnostics_mode: bool,
    ) -> SceneSpecModel:
        scene_title = self._scene_title(title, scene_type, order_index)
        objective = self._scene_objective(scene_type, title)
        return SceneSpecModel(
            order_index=order_index,
            title=scene_title,
            scene_type=scene_type,
            learning_objective=objective,
            estimated_duration_seconds=50.0,
            visual_style=context.style,
            renderer_key=self._renderer_for(scene_type),
            narration=NarrationSpec(
                text=self._scene_narration(scene_type, title, objective, context.prompt)
            ),
            visuals=self._scene_visuals(scene_type, title, topic_domain),
            animations=self._scene_animations(scene_type),
            assets=self._scene_assets(scene_type, title, topic_domain, image_generation_enabled),
            equations=self._scene_equations(scene_type, topic_domain),
            diagnostics={"topic_domain": topic_domain, "layout_debug": diagnostics_mode},
        )

    def _scene_title(self, root_title: str, scene_type: str, order_index: int) -> str:
        labels = {
            "title": root_title,
            "concept_overview": "Key Idea Map",
            "derivation": f"Derivation Step {order_index - 1}",
            "graph_plot": "Visualizing the Behavior",
            "comparison": "Side-by-Side Comparison",
            "process_flow": "How the System Evolves",
            "icon_explainer": "Concepts in Context",
            "image_assisted": "Concrete Mental Model",
            "summary": "Takeaways and Next Steps",
        }
        return labels.get(scene_type, f"{root_title} Scene {order_index}")

    def _scene_objective(self, scene_type: str, title: str) -> str:
        objectives = {
            "title": f"Establish the central question behind {title}.",
            "concept_overview": f"Break {title} into the core mental model and vocabulary.",
            "derivation": f"Work through the logic or derivation that powers {title}.",
            "graph_plot": f"Show how {title} behaves across a dynamic range of inputs.",
            "comparison": f"Contrast competing perspectives or states within {title}.",
            "process_flow": f"Show the causal sequence underlying {title}.",
            "icon_explainer": f"Anchor {title} using familiar domain symbols.",
            "image_assisted": f"Build an intuitive analogy for {title}.",
            "summary": f"Reinforce the most durable takeaways from {title}.",
        }
        return objectives.get(scene_type, f"Explain {title}.")

    def _scene_visuals(self, scene_type: str, title: str, topic_domain: str) -> list[VisualElement]:
        if scene_type == "title":
            return [
                VisualElement(kind="title", content=title, position_hint="top"),
                VisualElement(kind="text", content=f"A structured explainer on {title}.", position_hint="center"),
            ]
        if scene_type == "derivation":
            return [
                VisualElement(kind="equation", content=self._domain_equation(topic_domain), position_hint="left"),
                VisualElement(kind="text", content="Each transformation is justified before the next reveal.", position_hint="right"),
            ]
        if scene_type == "graph_plot":
            return [
                VisualElement(kind="plot", content=f"{title} trend plot", position_hint="left"),
                VisualElement(kind="equation", content=self._domain_equation(topic_domain), position_hint="right"),
            ]
        if scene_type == "comparison":
            return [
                VisualElement(kind="comparison", content=f"Baseline vs improved view of {title}", position_hint="center"),
                VisualElement(kind="icon", content=topic_domain.replace("_", " "), position_hint="bottom", tags=[topic_domain]),
            ]
        if scene_type == "process_flow":
            return [
                VisualElement(kind="process_flow", content=f"Pipeline for {title}", position_hint="center"),
                VisualElement(kind="text", content="Inputs, transformations, and outputs are staged for clarity.", position_hint="bottom"),
            ]
        if scene_type == "image_assisted":
            return [
                VisualElement(kind="image", content=f"{title} conceptual illustration", position_hint="left"),
                VisualElement(kind="text", content="A visual metaphor links the abstraction to something concrete.", position_hint="right"),
            ]
        if scene_type == "summary":
            return [VisualElement(kind="summary", content=f"Three durable lessons from {title}.")]
        return [
            VisualElement(kind="diagram", content=f"Concept map for {title}", position_hint="center"),
            VisualElement(kind="icon", content=topic_domain.replace("_", " "), position_hint="bottom", tags=[topic_domain]),
        ]

    def _scene_narration(self, scene_type: str, title: str, objective: str, prompt: str) -> str:
        prompt_summary = " ".join(prompt.split()[:24])
        if scene_type == "title":
            return f"This explainer unpacks {title}. We start by framing the problem, then progressively build intuition, structure, and technical depth."
        if scene_type == "summary":
            return f"We can now compress {title} into a compact mental model. The key is to remember the structure, the driver of change, and the practical implication."
        return f"{objective} We connect it back to the original request: {prompt_summary}. The pacing stays deliberate so each visual change supports the narration instead of competing with it."

    def _scene_assets(
        self,
        scene_type: str,
        title: str,
        topic_domain: str,
        image_generation_enabled: bool,
    ) -> list[AssetSpec]:
        assets: list[AssetSpec] = []
        if scene_type in {"icon_explainer", "comparison", "concept_overview"}:
            assets.append(
                AssetSpec(
                    asset_type="icon",
                    provider="iconify",
                    icon_name=self._icon_for_topic(topic_domain),
                    cache_key=f"icon:{topic_domain}",
                    metadata={"topic_domain": topic_domain},
                )
            )
        if scene_type == "image_assisted" and image_generation_enabled:
            assets.append(
                AssetSpec(
                    asset_type="image",
                    provider="stable_horde",
                    prompt=f"Educational explainer illustration of {title}, {topic_domain}, clean composition, no text",
                    cache_key=f"image:{topic_domain}:{title.lower().replace(' ', '-')}",
                )
            )
        return assets

    def _scene_animations(self, scene_type: str) -> list[AnimationSpec]:
        animations = {
            "title": [AnimationSpec(animation_type="write"), AnimationSpec(animation_type="fade_in")],
            "derivation": [AnimationSpec(animation_type="transform"), AnimationSpec(animation_type="highlight")],
            "graph_plot": [AnimationSpec(animation_type="draw_graph"), AnimationSpec(animation_type="label_track")],
            "process_flow": [AnimationSpec(animation_type="flow_reveal"), AnimationSpec(animation_type="emphasis_box")],
        }
        return animations.get(scene_type, [AnimationSpec(animation_type="fade_in")])

    def _scene_equations(self, scene_type: str, topic_domain: str) -> list[str]:
        if scene_type not in {"derivation", "graph_plot"}:
            return []
        return [self._domain_equation(topic_domain)]

    def _domain_equation(self, topic_domain: str) -> str:
        equations = {
            "mathematics": "f(x)=x^2+2x+1",
            "physics": "F=ma",
            "finance": "NPV=\\sum_{t=0}^{n} \\frac{CF_t}{(1+r)^t}",
            "computer_science": "T(n)=2T(n/2)+n",
            "ai_ml": "L(\\theta)=\\frac{1}{n}\\sum_i (y_i-\\hat{y}_i)^2",
            "chemistry": "PV=nRT",
        }
        return equations.get(topic_domain, "y=mx+b")

    def _renderer_for(self, scene_type: str) -> str:
        mapping = {
            "title": "title",
            "concept_overview": "concept",
            "derivation": "derivation",
            "graph_plot": "graph",
            "comparison": "comparison",
            "process_flow": "flow",
            "icon_explainer": "icon",
            "image_assisted": "image",
            "summary": "summary",
        }
        return mapping.get(scene_type, "concept")

    def _icon_for_topic(self, topic_domain: str) -> str:
        mapping = {
            "mathematics": "tabler:function",
            "physics": "tabler:atom-2",
            "finance": "tabler:chart-histogram",
            "computer_science": "tabler:brackets-angle",
            "ai_ml": "tabler:brain",
            "chemistry": "tabler:flask",
        }
        return mapping.get(topic_domain, "tabler:bulb")

    def _rebalance_durations(self, scenes: list[SceneSpecModel], target_duration_seconds: int) -> list[SceneSpecModel]:
        if not scenes:
            return scenes
        base = target_duration_seconds / len(scenes)
        for scene in scenes:
            modifier = 1.2 if scene.scene_type in {"derivation", "graph_plot"} else 0.9 if scene.scene_type == "title" else 1.0
            scene.estimated_duration_seconds = round(base * modifier, 1)
        total = sum(scene.estimated_duration_seconds for scene in scenes)
        correction = target_duration_seconds / total
        for scene in scenes:
            scene.estimated_duration_seconds = round(scene.estimated_duration_seconds * correction, 1)
        return scenes
