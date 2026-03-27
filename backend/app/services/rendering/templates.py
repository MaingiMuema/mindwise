from pathlib import Path

from manim import (
    Arrow,
    Axes,
    BLUE_E,
    Create,
    DOWN,
    FadeIn,
    GREEN_E,
    Group,
    ImageMobject,
    LEFT,
    MathTex,
    ORANGE,
    PURPLE_E,
    RED_E,
    RIGHT,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    WHITE,
    Write,
    YELLOW_E,
)

from app.schemas.planning import SceneSpecModel, VisualElement


def _fit(mobject, max_width: float = 11.6, max_height: float = 6.0):
    if mobject.width > max_width:
        mobject.scale_to_fit_width(max_width)
    if mobject.height > max_height:
        mobject.scale_to_fit_height(max_height)
    return mobject


def _text(content: str, font_size: int = 34, color=WHITE):
    return Text(content, font_size=font_size, color=color)


def _math(content: str):
    sanitized = content.replace("\\\\", "\\")
    return MathTex(sanitized, font_size=40)


def _visual_label(visual: VisualElement) -> str:
    return visual.content or visual.kind.replace("_", " ").title()


class TemplateRenderer:
    def render(self, scene: Scene, spec: SceneSpecModel) -> None:
        dispatch = {
            "title": self.render_title,
            "concept": self.render_concept,
            "derivation": self.render_derivation,
            "graph": self.render_graph,
            "comparison": self.render_comparison,
            "flow": self.render_flow,
            "icon": self.render_icon,
            "image": self.render_image,
            "summary": self.render_summary,
        }
        handler = dispatch.get(spec.renderer_key, self.render_concept)
        handler(scene, spec)
        if spec.diagnostics.get("layout_debug"):
            for mobject in list(scene.mobjects):
                scene.add(SurroundingRectangle(mobject, buff=0.08, color=YELLOW_E))

    def render_title(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _fit(_text(spec.title, font_size=48))
        subtitle = _fit(_text(spec.learning_objective, font_size=26, color=BLUE_E), max_height=1.8)
        stack = VGroup(title, subtitle).arrange(DOWN, buff=0.4).move_to(UP * 0.6)
        scene.play(Write(title))
        scene.play(FadeIn(subtitle))
        scene.wait(0.3)

    def render_concept(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=40).to_edge(UP)
        cards = []
        for visual in spec.visuals[:4]:
            card = RoundedRectangle(corner_radius=0.2, width=4.4, height=2.1, color=BLUE_E)
            label = _fit(_text(_visual_label(visual), font_size=26), max_width=3.8, max_height=1.4)
            cards.append(VGroup(card, label.move_to(card.get_center())))
        grid = VGroup(*cards).arrange_in_grid(cols=2, buff=0.4)
        scene.play(Write(title))
        scene.play(FadeIn(grid))

    def render_derivation(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=38).to_edge(UP)
        equation = _fit(_math(spec.equations[0] if spec.equations else "y=mx+b"), max_height=2.2)
        explanation = _fit(_text(spec.learning_objective, font_size=28), max_height=2.0)
        group = VGroup(equation, explanation).arrange(DOWN, buff=0.8).move_to(DOWN * 0.2)
        scene.play(Write(title))
        scene.play(Write(equation))
        scene.play(FadeIn(explanation))

    def render_graph(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=38).to_edge(UP)
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-1, 9, 1],
            x_length=5.2,
            y_length=4.0,
            axis_config={"include_numbers": False},
        ).shift(LEFT * 2.5 + DOWN * 0.4)
        graph = axes.plot(lambda x: x**2 / 2 + 1, color=GREEN_E)
        formula = _fit(_math(spec.equations[0] if spec.equations else "y=x^2"), max_width=4.6, max_height=1.8)
        formula.next_to(axes, RIGHT, buff=0.7)
        scene.play(Write(title))
        scene.play(Create(axes), Create(graph))
        scene.play(FadeIn(formula))

    def render_comparison(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=38).to_edge(UP)
        left_box = RoundedRectangle(corner_radius=0.2, width=4.8, height=3.8, color=ORANGE).shift(LEFT * 3)
        right_box = RoundedRectangle(corner_radius=0.2, width=4.8, height=3.8, color=PURPLE_E).shift(RIGHT * 3)
        left_label = _fit(_text("Baseline", font_size=30), max_width=3.6).move_to(left_box.get_center())
        right_label = _fit(_text("Improved", font_size=30), max_width=3.6).move_to(right_box.get_center())
        scene.play(Write(title))
        scene.play(FadeIn(VGroup(left_box, right_box, left_label, right_label)))

    def render_flow(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=38).to_edge(UP)
        labels = ["Input", "Transform", "Output"]
        boxes = []
        for index, label in enumerate(labels):
            box = RoundedRectangle(corner_radius=0.18, width=2.6, height=1.3, color=BLUE_E)
            box.shift(LEFT * 4 + RIGHT * (index * 4))
            text = _text(label, font_size=28).move_to(box.get_center())
            boxes.append(VGroup(box, text))
        arrows = VGroup(
            Arrow(boxes[0].get_right(), boxes[1].get_left(), buff=0.1, color=WHITE),
            Arrow(boxes[1].get_right(), boxes[2].get_left(), buff=0.1, color=WHITE),
        )
        flow = VGroup(*boxes, arrows).shift(DOWN * 0.3)
        scene.play(Write(title))
        scene.play(FadeIn(flow))

    def render_icon(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=38).to_edge(UP)
        big_label = _fit(_text("Icon-driven explanation", font_size=34, color=GREEN_E), max_height=1.5)
        caption = _fit(_text(spec.learning_objective, font_size=28), max_height=2.0)
        stack = VGroup(big_label, caption).arrange(DOWN, buff=0.5).move_to(DOWN * 0.2)
        scene.play(Write(title))
        scene.play(FadeIn(stack))

    def render_image(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=38).to_edge(UP)
        image_path = None
        for visual in spec.visuals:
            candidate = visual.metadata.get("asset_path")
            if candidate and Path(candidate).exists():
                image_path = candidate
                break
        if image_path:
            image = _fit(ImageMobject(image_path), max_width=6.2, max_height=4.4).shift(LEFT * 2.5 + DOWN * 0.2)
        else:
            frame = RoundedRectangle(corner_radius=0.2, width=6.0, height=4.2, color=RED_E).shift(LEFT * 2.5 + DOWN * 0.2)
            frame_label = _text("Image Placeholder", font_size=28).move_to(frame.get_center())
            image = Group(frame, frame_label)
        caption = _fit(_text(spec.learning_objective, font_size=28), max_width=4.8, max_height=3.4)
        caption.next_to(image, RIGHT, buff=0.8)
        scene.play(Write(title))
        scene.play(FadeIn(image), FadeIn(caption))

    def render_summary(self, scene: Scene, spec: SceneSpecModel) -> None:
        title = _text(spec.title, font_size=38).to_edge(UP)
        bullets = VGroup(
            *[
                _fit(_text(line, font_size=28), max_height=1.0)
                for line in [
                    "Build the intuition first.",
                    "Keep the core transformation visible.",
                    "End with a durable mental checklist.",
                ]
            ]
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        bullets.move_to(DOWN * 0.2)
        scene.play(Write(title))
        scene.play(FadeIn(bullets))


renderer = TemplateRenderer()
