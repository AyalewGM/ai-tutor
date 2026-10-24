"""Synthetic scorer checks; no database writes, content activation or learner data."""
from app.services.statistics_scoring import score_box_comparison, score_box_plot


def test_even_and_odd_median_of_halves_convention() -> None:
    values = [2, 4, 8, 10, 14, 17, 19, 20, 21, 22, 26, 34]
    assert score_box_plot(values, {
        "minimum": "2", "q1": "9", "median": "18",
        "q3": "43/2", "maximum": "34",
    }, kind="FIVE_NUMBER").correct
    assert score_box_plot([12, 14, 16, 18, 20, 22, 24, 26, 42], {
        "q1": "15", "median": "20", "q3": "25", "iqr": "10",
    }, kind="QUARTILES_IQR").correct


def test_modified_whisker_is_observation_not_fence() -> None:
    values = [60, 64, 66, 70, 72, 72, 74, 90]
    answer = {
        "q1": "65", "median": "71", "q3": "73", "iqr": "8",
        "lower_fence": "53", "upper_fence": "85",
        "left_whisker": "60", "right_whisker": "74", "outliers": [90],
    }
    assert score_box_plot(values, answer, kind="MODIFIED_BOX").correct
    assert not score_box_plot(
        values, {**answer, "right_whisker": "85"}, kind="MODIFIED_BOX"
    ).correct
    assert not score_box_plot(
        values, {**answer, "upper_fence": "61"}, kind="MODIFIED_BOX"
    ).correct
    assert not score_box_plot(values, {**answer, "outliers": []}, kind="MODIFIED_BOX").correct


def test_comparison_ties_are_not_arbitrarily_assigned() -> None:
    answer = {
        "median_a": "14", "median_b": "24",
        "iqr_a": "6", "iqr_b": "6", "wider": "EQUAL",
    }
    a, b = [10, 12, 14, 16, 18], [20, 22, 24, 26, 28]
    assert score_box_comparison(a, b, answer).correct
    assert not score_box_comparison(a, b, {**answer, "wider": "A"}).correct


def test_strict_response_fields_no_mutation_or_private_oracle() -> None:
    values = [1, 2, 3, 4, 5]
    before = values[:]
    answer = {
        "minimum": "1", "q1": "3/2", "median": "3",
        "q3": "9/2", "maximum": "5",
    }
    outcome = score_box_plot(values, answer, kind="FIVE_NUMBER")
    assert outcome.correct and values == before
    assert not hasattr(outcome, "canonical_answer")
    assert not score_box_plot(
        values, {**answer, "q1": "2"}, kind="FIVE_NUMBER"
    ).correct
    assert not score_box_plot(
        values, {**answer, "private_oracle": "3"}, kind="FIVE_NUMBER"
    ).correct
    assert not score_box_plot(
        values, {**answer, "median": 3.0}, kind="FIVE_NUMBER"
    ).correct
    assert not score_box_plot(values, answer, kind="MASTERED").correct
    assert not score_box_plot([1, 2, 3, 4], answer, kind="FIVE_NUMBER").correct
