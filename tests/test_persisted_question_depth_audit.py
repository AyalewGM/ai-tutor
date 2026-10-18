"""Depth audit counts mathematical tasks and honors synthetic-only boundaries."""
from types import SimpleNamespace

from scripts.audit_persisted_question_depth import (
    _sample_canonical,
    _task_key,
    summarize_skill,
)


def problem(id, prompt, answer, *, params=None, difficulty=2, problem_type="UNSUPPORTED"):
    return SimpleNamespace(
        id=id,
        prompt=prompt,
        canonical_answer=answer,
        choices=None,
        solution={"parameters": params} if params is not None else None,
        difficulty=difficulty,
        problem_type=problem_type,
        source_type="CURATED",
    )


def test_visual_parameters_distinguish_mathematically_distinct_tasks() -> None:
    a = problem("a", "What is the slope of the line shown?", "2", params={"m": 2, "b": 1})
    b = problem("b", "What is the slope of the line shown?", "-3", params={"m": -3, "b": 1})
    assert _task_key(a) != _task_key(b)


def test_thin_skill_reports_duplicate_tasks_and_mode_metadata_without_claiming_qa() -> None:
    curriculum = SimpleNamespace(code="SYNTH_G8", grade_level="8", version="1", jurisdiction="Synthetic")
    skill = SimpleNamespace(code="M8.EE.TEST", name="Synthetic skill")
    items = [
        problem("a", "  Solve x + 2 = 5", "3"),
        problem("b", "Solve x + 2 = 5", "3"),
        problem("c", "Solve x + 2 = 5", "4"),
        problem("d", "Extra", "2"),
    ]
    metadata = {
        "a": SimpleNamespace(extension_eligible=False, diagnostic_eligible=True,
                             guided_eligible=True, independent_eligible=False, mastery_eligible=False),
        "b": SimpleNamespace(extension_eligible=False, diagnostic_eligible=False,
                             guided_eligible=True, independent_eligible=False, mastery_eligible=False),
        "c": SimpleNamespace(extension_eligible=False, diagnostic_eligible=False,
                             guided_eligible=False, independent_eligible=True, mastery_eligible=False),
        "d": SimpleNamespace(extension_eligible=True, diagnostic_eligible=True,
                             guided_eligible=True, independent_eligible=True, mastery_eligible=True),
    }
    row = summarize_skill(curriculum, skill, items, metadata, None, None, samples=1)
    assert row["grade_or_course"] == "8"
    assert row["stored_total"] == 4
    assert row["stored_non_extension"] == 3
    assert row["stored_distinct_tasks"] == 1
    assert row["duplicate_task_rows"] == 2
    assert row["conflicting_answer_task_groups"] == 1
    assert row["declared_mode_pool_counts"]["diagnostic"] == 1
    assert row["declared_mode_pool_counts"]["independent"] == 1
    assert row["declared_mode_pool_counts"]["mastery"] == 0
    assert row["learner_visible_integrated_status"] == "NOT_VERIFIED"
    assert "SAME_TASK_DIFFERENT_ANSWERS" in row["issues_for_triage"]
    assert "MISSING_DECLARED_INDEPENDENT_OR_MASTERY_POOL" in row["issues_for_triage"]
    assert row["canonical_mapping_approval"] == "NOT_ASSESSED"


def test_missing_metadata_never_becomes_verified_assessment_depth() -> None:
    curriculum = SimpleNamespace(code="SYNTH_G2", grade_level="2", version="1", jurisdiction="Synthetic")
    skill = SimpleNamespace(code="M2.OA.TEST", name="Synthetic skill")
    row = summarize_skill(curriculum, skill, [problem("a", "2 + 3", "5")], {}, None, None, samples=1)
    assert row["stored_non_extension"] == 1
    assert row["missing_metadata_rows"] == 1
    assert row["declared_mode_pool_counts"] == {
        "diagnostic": 0, "guided": 0, "independent": 0, "mastery": 0,
    }
    assert row["learner_selectable_non_extension_upper_bound"] == 1
    assert row["cross_session_repetition"].startswith("AT_RISK")


def test_canonical_generator_sample_is_not_mathematical_approval() -> None:
    result = _sample_canonical("MATH.EE.EQUATION.ONE", 2)
    assert result["declared_families"] >= 1
    for record in result["family_samples"].values():
        assert record["tested_seeds"] == 2
        assert record["unique_sample_tasks"] <= 2
        assert record["math_review"] == "NOT_ASSESSED"
        assert record["learner_route"] == "NOT_VERIFIED"

def test_explicit_qa_visual_fixture_is_reported_but_not_instructional_priority() -> None:
    curriculum = SimpleNamespace(code="MCPS_MATH_8", grade_level="8", version="1", jurisdiction="MD")
    skill = SimpleNamespace(code="M8.PROB.MARBLE_QA", name="Marble QA only")
    row = summarize_skill(curriculum, skill, [problem("qa", "Blue marbles?", "3/8")], {}, None, None, samples=1)
    assert row["is_qa_fixture"] is True
    assert row["instructional_priority_eligible"] is False
    assert row["stored_distinct_tasks"] == 1
