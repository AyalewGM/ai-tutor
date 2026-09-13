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
