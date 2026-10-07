from types import SimpleNamespace
from uuid import uuid4

from app.canonical_problem_adapter import materialize_problem
from app.canonical_problem_families import generate
from app.services.visualization import visualization_for


VISUAL_FAMILIES = [
    "MATH.GEO.AREA.TRI",
    "MATH.GEO.AREA.PARALLELOGRAM",
    "MATH.GEO.AREA.TRAPEZOID",
    "MATH.GEO.VOLUME.PRISM",
    "MATH.GEO.ANGLE.CLASSIFY",
    "MATH.GEO.ANGLE.COMPLEMENT",
    "MATH.GEO.ANGLE.SUPPLEMENT",
    "MATH.GEO.TRIANGLE.MISSING_ANGLE",
    "MATH.GEO.PYTHAGOREAN.HYPOTENUSE",
    "MATH.GEO.TRANSFORM.TRANSLATE_POINT",
    "MATH.DATA.MEAN",
    "MATH.DATA.MEDIAN",
    "MATH.DATA.RANGE",
    "MATH.DATA.OUTLIER.CENTER",
    "MATH.DATA.FREQ.JOINT",
    "MATH.DATA.FREQ.CONDITIONAL",
    "MATH.PROB.SIMPLE",
    "MATH.PROB.COMPLEMENT",
]


def test_canonical_visual_specs_are_deterministic() -> None:
    for family_code in VISUAL_FAMILIES:
        first = generate(family_code, seed=41, difficulty=3)
        second = generate(family_code, seed=41, difficulty=3)
        assert first.visual_spec == second.visual_spec, family_code
        assert first.visual_spec is not None, family_code
        assert isinstance(first.visual_spec["type"], str), family_code
        assert first.visual_spec.get("aria_label"), family_code


def test_existing_nonvisual_family_remains_backward_compatible() -> None:
    problem = generate("MATH.EQ.ONE.ADD_DIRECT", seed=7, difficulty=2)
    assert problem.visual_spec is None


def test_visualization_service_prefers_canonical_spec() -> None:
    generated = generate("MATH.GEO.ANGLE.COMPLEMENT", seed=9, difficulty=3)
    problem = SimpleNamespace(
        solution={"visual_spec": generated.visual_spec},
        problem_type="ANGLE_REASONING",
        prompt=generated.prompt,
    )
    assert visualization_for(problem) == generated.visual_spec


def test_visualization_service_rejects_malformed_canonical_spec() -> None:
    problem = SimpleNamespace(
        solution={"visual_spec": {"angle": 45}},
        problem_type="UNSUPPORTED",
        prompt="No renderer should be selected.",
    )
    assert visualization_for(problem) is None


class _FakeDb:
    def __init__(self) -> None:
        self.added = None

    def scalar(self, _query):
        return None

    def add(self, problem) -> None:
        self.added = problem

    def flush(self) -> None:
        return None


def test_materialization_preserves_visual_spec_without_evidence_transfer() -> None:
    generated = generate("MATH.PROB.SIMPLE", seed=17, difficulty=2)
    db = _FakeDb()
    skill = SimpleNamespace(id=uuid4())

    problem = materialize_problem(db, generated=generated, curriculum_skill=skill)

    assert db.added is problem
    assert problem.solution["visual_spec"] == generated.visual_spec
    assert problem.solution["canonical_skill_code"] == generated.canonical_skill_code
    assert "mastery" not in problem.solution
    assert "learner" not in problem.solution


def test_pythagorean_visual_does_not_reveal_unknown_hypotenuse() -> None:
    generated = generate("MATH.GEO.PYTHAGOREAN.HYPOTENUSE", seed=23, difficulty=3)
    assert generated.visual_spec is not None
    assert generated.visual_spec["type"] == "right_triangle"
    assert generated.visual_spec["hyp"] == "?"
    assert generated.canonical_answer not in {
        str(generated.visual_spec.get("leg_a")),
        str(generated.visual_spec.get("leg_b")),
    }
