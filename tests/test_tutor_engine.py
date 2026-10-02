from app.services.tutor_engine import StepEvidence, TutorContext, TutorEngine


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


def _step_context(action: str, hint_level: int | None, evidence: StepEvidence | None):
    return TutorContext(
        grade_level="8",
        curriculum_name="MCPS Grade 8 Mathematics",
        state="GUIDED_PRACTICE",
        skill_name="Two-Step Equations",
        action=action,
        hint_level=hint_level,
        problem_prompt="Solve 3x + 12 = 30.",
        step_evidence=evidence,
    )


def test_step_voice_names_the_learners_line_from_hint_level_two() -> None:
    evidence = StepEvidence("3x + 12 = 30", "3x = 42", "EQ_001")
    level_one = TutorEngine().generate(_step_context("GIVE_HINT", 1, evidence)).message
    level_two = TutorEngine().generate(_step_context("GIVE_HINT", 2, evidence)).message
    # Level 1 stays a nudge; level 2 quotes the line and names the move.
    assert "3x = 42" not in level_one
    assert "3x = 42" in level_two
    assert "subtract" in level_two.lower()
    assert "wrong direction" in level_two


def test_step_voice_without_a_code_still_cites_both_lines() -> None:
    evidence = StepEvidence("3x + 12 = 30", "3x = 17", None, invalid_count=2)
    message = TutorEngine().generate(_step_context("EXPLAIN_CONCEPT", None, evidence)).message
    assert "3x = 17" in message and "3x + 12 = 30" in message
    assert "again" in message  # second miss adds the retry nudge


def test_no_step_evidence_keeps_the_generic_ladder() -> None:
    message = TutorEngine().generate(_step_context("GIVE_HINT", 2, None)).message
    assert "both sides" in message.lower() or "other side" in message.lower()


def test_step_evidence_describe_is_compact_and_codes_the_move() -> None:
    text = StepEvidence("3x + 12 = 30", "3x = 42", "EQ_001").describe()
    assert text == "from '3x + 12 = 30' the learner wrote '3x = 42' (classified EQ_001)"
