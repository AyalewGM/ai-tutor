from app.services.evaluation import evaluate_problem


def test_free_text_default_behavior_unchanged() -> None:
    assert evaluate_problem("x + 5 = 12", "x=7", "x=7").correct is True
    assert evaluate_problem("x + 5 = 12", "x=8", "x=7").correct is False


def test_integer_kind_accepts_numeric_forms() -> None:
    assert (
        evaluate_problem("Evaluate -6 + 14.", "8", "8", answer_kind="INTEGER").correct
        is True
    )
    assert (
        evaluate_problem(
            "Evaluate -6 + 14.", "08", "8", answer_kind="INTEGER"
        ).correct
        is True
    )
    assert (
        evaluate_problem("Evaluate -6 + 14.", "9", "8", answer_kind="INTEGER").correct
        is False
    )


def test_fraction_kind_accepts_equivalent_fractions() -> None:
    assert (
        evaluate_problem(
            "Simplify the ratio 4 to 8.", "2/4", "1/2", answer_kind="FRACTION"
        ).correct
        is True
    )
    assert (
        evaluate_problem(
            "What fraction is shaded?", "0.5", "1/2", answer_kind="FRACTION"
        ).correct
        is False
    )
    assert (
        evaluate_problem("Simplify.", "1/3", "1/2", answer_kind="FRACTION").correct
        is False
    )
    # Bare integers are valid fractions (n/1).
    assert (
        evaluate_problem("Evaluate 4/2.", "2", "2", answer_kind="FRACTION").correct
        is True
    )


def test_fraction_kind_zero_denominator_never_correct() -> None:
    assert (
        evaluate_problem("Simplify.", "1/0", "1/2", answer_kind="FRACTION").correct
        is False
    )


def test_multiple_choice_grades_by_choice_id() -> None:
    choices = [
        {"id": "a", "text": "x = 4"},
        {"id": "b", "text": "x = 16"},
        {"id": "c", "text": "x = 12"},
    ]
    assert (
        evaluate_problem(
            "Solve x + 4 = 8.", "a", "a", answer_kind="MULTIPLE_CHOICE", choices=choices
        ).correct
        is True
    )
    assert (
        evaluate_problem(
            "Solve x + 4 = 8.", "b", "a", answer_kind="MULTIPLE_CHOICE", choices=choices
        ).correct
        is False
    )


def test_multiple_choice_distractor_maps_to_misconception() -> None:
    choices = [
        {"id": "a", "text": "x = 4"},
        {"id": "b", "text": "x = 16", "misconception_code": "INVERSE_DIRECTION"},
    ]
    result = evaluate_problem(
        "Solve x + 4 = 8.",
        "b",
        "a",
        answer_kind="MULTIPLE_CHOICE",
        choices=choices,
    )
    assert result.correct is False
    assert result.misconception_code == "INVERSE_DIRECTION"


def test_multiple_choice_unmapped_choice_reports_no_misconception() -> None:
    choices = [{"id": "a", "text": "x = 4"}, {"id": "b", "text": "x = 16"}]
    result = evaluate_problem(
        "Solve x + 4 = 8.",
        "b",
        "a",
        answer_kind="MULTIPLE_CHOICE",
        choices=choices,
    )
    assert result.correct is False
    assert result.misconception_code is None
