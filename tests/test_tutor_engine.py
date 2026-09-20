from app.services.tutor_engine import TutorContext, TutorEngine


class GoodProvider:
    model_name = "test-model"
    provider_name = "test-provider"

    def generate(self, context: TutorContext) -> dict[str, object]:
        return {
            "message": f"Think about {context.skill_name} before answering.",
            "expects_student_response": True,
        }


class FailingProvider:
    model_name = "broken-model"
    provider_name = "broken-provider"

    def generate(self, context: TutorContext) -> dict[str, object]:
        raise RuntimeError("provider unavailable")


def context() -> TutorContext:
    return TutorContext(
        grade_level="8",
        curriculum_name="MCPS Grade 8 Mathematics",
        state="GUIDED_PRACTICE",
        skill_name="Distributive Property",
        action="GIVE_HINT",
        hint_level=2,
        problem_prompt="3(x+4)",
        student_answer="3x+4",
        misconception_description="Partial distribution",
    )


def test_tutor_engine_accepts_structured_provider_output() -> None:
    result = TutorEngine(GoodProvider()).generate(context())
    assert result.source == "llm"
    assert result.model == "test-model"
    assert result.provider == "test-provider"
    assert result.latency_ms is not None
    assert "Distributive Property" in result.message


def test_tutor_engine_falls_back_when_provider_fails() -> None:
    result = TutorEngine(FailingProvider()).generate(context())
    assert result.source == "fallback"
    assert result.model is None
    assert result.provider is None
    assert "every term" in result.message


def _hint(prompt: str, level: int = 2, action: str = "GIVE_HINT") -> str:
    ctx = TutorContext(
        grade_level="8",
        curriculum_name="MCPS Grade 8 Mathematics",
        state="GUIDED_PRACTICE",
        skill_name="Two-Step Equations",
        action=action,
        hint_level=level,
        problem_prompt=prompt,
    )
    return TutorEngine(FailingProvider()).generate(ctx).message


def test_equation_hint_never_mentions_parentheses() -> None:
    for level in (1, 2, 3, 4):
        message = _hint("3x - 5 = 16", level)
        assert "parentheses" not in message
    assert "side" in _hint("3x - 5 = 16", 2)


def test_like_terms_hint_mentions_combining() -> None:
    assert "Combine the x terms" in _hint("4x + 3 + 2x - 5", 2)


def test_fraction_hint_mentions_denominator() -> None:
    assert "denominator" in _hint("3/4 + 1/2", 1)


def test_linear_function_hint_mentions_slope() -> None:
    message = _hint("For y = 4x - 1, what is y when x = 3?", 1)
    assert "slope" in message or "y =" in message


def test_generic_hint_is_neutral() -> None:
    message = _hint("What is 20% of 60?", 2)
    assert "parentheses" not in message
    assert "operation" in message


def test_explain_concept_matches_problem_shape() -> None:
    assert "both sides" in _hint("x + 7 = 19", action="EXPLAIN_CONCEPT")
    assert "parentheses" in _hint("3(x+4)", action="EXPLAIN_CONCEPT")
