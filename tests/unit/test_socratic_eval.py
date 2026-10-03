import json

from scripts.evals.socratic_eval import Scenario, check_message


def _scenario(**kwargs) -> Scenario:
    base = {
        "name": "s",
        "request": {"action": "A", "curriculum_name": "c", "grade_level": "8",
                    "skill_name": "s", "problem_prompt": "p"},
    }
    return Scenario(**{**base, **kwargs})


def _block(payload: dict) -> str:
    return "```json:cpa\n" + json.dumps(payload) + "\n```"


_BALANCE = {
    "type": "BALANCE_SCALE",
    "balanceScale": {"leftExpr": "2x", "rightExpr": "11", "leftValue": 8, "rightValue": 11},
}


def test_clean_message_with_block_passes() -> None:
    violations = check_message(
        f"What happens to both sides?\n\n{_block(_BALANCE)}",
        _scenario(canonical_answer="x=4"),
    )
    assert violations == []


def test_two_blocks_violate_single_visual_rule() -> None:
    violations = check_message(
        f"Look?\n\n{_block(_BALANCE)}\n{_block(_BALANCE)}",
        _scenario(),
    )
    assert any("max 1" in v for v in violations)


def test_answer_in_text_or_solved_scale_violates() -> None:
    assert check_message("The answer is x = 4?", _scenario(canonical_answer="x=4"))
    leaky = {"type": "BALANCE_SCALE",
             "balanceScale": {"leftExpr": "x", "rightExpr": "4"}}
    assert check_message(
        f"See?\n\n{_block(leaky)}", _scenario(canonical_answer="x=4")
    )


def test_forbidden_and_required_flags() -> None:
    assert check_message(
        "Sure?\n\n```json:cpa\n{}\n```",
        _scenario(cpa_forbidden=True),
    )
    assert check_message("Just text?", _scenario(cpa_required=True))


def test_missing_question_flagged() -> None:
    assert check_message("Do the step.", _scenario())
