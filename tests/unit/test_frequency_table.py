"""FREQUENCY_TABLE generator: two-way table reading, joint and conditional
relative frequencies, association judgements, and the table visual spec."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(1500):
        generated = GENERATORS["FREQUENCY_TABLE"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no FREQUENCY_TABLE/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _totals(cells: list[list[int]]) -> tuple[list[int], list[int], int]:
    row = [cells[0][0] + cells[0][1], cells[1][0] + cells[1][1]]
    col = [cells[0][0] + cells[1][0], cells[0][1] + cells[1][1]]
    return row, col, sum(row)


def test_low_difficulty_only_reads_cells_and_marginals() -> None:
    for seed in range(200):
        generated = GENERATORS["FREQUENCY_TABLE"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"read_cell", "marginal"}


def test_read_cell_answer_matches_the_asked_cell() -> None:
    for _ in range(120):
        generated = _gen("read_cell", difficulty=1)
        params = generated.parameters
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert int(correct) == params["cells"][params["ri"]][params["ci"]]
        # Every distractor is a value actually in the table — a misread.
        values = {
            str(v) for v in (
                params["cells"][0] + params["cells"][1]
                + _totals(params["cells"])[0]
                + _totals(params["cells"])[1]
                + [_totals(params["cells"])[2]]
            )
        }
        for choice in generated.choices:
            assert choice["text"] in values
            if choice["id"] != generated.canonical_answer:
                assert choice["misconception_code"] == "STAT_007"


def test_marginal_and_grand_total_answers() -> None:
    for _ in range(100):
        generated = _gen("marginal", difficulty=1)
        params = generated.parameters
        row, col, grand = _totals(params["cells"])
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        expected = row[params["index"]] if params["axis"] == "row" else col[params["index"]]
        assert int(correct) == expected
    generated = _gen("grand_total", difficulty=2)
    row, col, grand = _totals(generated.parameters["cells"])
    correct = next(
        c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
    )
    assert int(correct) == grand
    # Every distractor is a partial sum, never the real total.
    for choice in generated.choices:
        if choice["id"] != generated.canonical_answer:
            assert int(choice["text"]) < grand
            assert choice["misconception_code"] == "STAT_007"


def test_joint_and_conditional_fractions_reduce() -> None:
    for _ in range(120):
        generated = _gen("joint_frequency", difficulty=2)
        params = generated.parameters
        row, col, grand = _totals(params["cells"])
        cell = params["cells"][params["ri"]][params["ci"]]
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct == str(Fraction(cell, grand))
        # The conditional-frequency distractors must be present and tagged.
        tagged = {c["text"] for c in generated.choices if c.get("misconception_code") == "STAT_006"}
        assert str(Fraction(cell, row[params["ri"]])) in tagged
    for _ in range(120):
        generated = _gen("conditional_frequency", difficulty=3)
        params = generated.parameters
        row, col, grand = _totals(params["cells"])
        i, j = params["index"], params["target"]
        if params["axis"] == "row":
            cell, denom = params["cells"][i][j], row[i]
        else:
            cell, denom = params["cells"][j][i], col[i]
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct == str(Fraction(cell, denom))
        tagged = {c["text"] for c in generated.choices if c.get("misconception_code") == "STAT_006"}
        assert str(Fraction(cell, grand)) in tagged


def test_association_answer_matches_the_rates() -> None:
    for _ in range(120):
        generated = _gen("association", difficulty=4)
        params = generated.parameters
        cells = params["cells"]
        p_yes = Fraction(cells[0][0], cells[0][0] + cells[0][1])
        p_no = Fraction(cells[1][0], cells[1][0] + cells[1][1])
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert params["associated"] == (abs(p_yes - p_no) >= Fraction(1, 4))
        if params["associated"]:
            assert ("more likely" in correct) == (p_yes > p_no)
        else:
            assert correct.startswith("No")
            assert abs(p_yes - p_no) <= Fraction(1, 20)


def test_totals_hidden_only_when_they_are_the_answer() -> None:
    for tier, difficulty in (("marginal", 1), ("grand_total", 2)):
        generated = _gen(tier, difficulty=difficulty)
        spec = visualization_for(_as_problem(generated))
        assert spec is not None and spec["type"] == "frequency_table"
        assert "row_totals" not in spec
    for tier, difficulty in (("read_cell", 1), ("joint_frequency", 2),
                             ("conditional_frequency", 3), ("association", 4)):
        generated = _gen(tier, difficulty=difficulty)
        spec = visualization_for(_as_problem(generated))
        assert spec is not None and spec["type"] == "frequency_table"
        assert "row_totals" in spec and "grand_total" in spec


def test_every_item_offers_four_distinct_choices() -> None:
    seen_tiers = set()
    for seed in range(1500):
        for difficulty in (1, 2, 3, 4):
            generated = GENERATORS["FREQUENCY_TABLE"](random.Random(seed), difficulty)
            seen_tiers.add(generated.parameters["tier"])
            texts = [c["text"] for c in generated.choices]
            assert len(texts) == 4
            assert len(set(texts)) == 4
    assert seen_tiers == {
        "read_cell", "marginal", "grand_total",
        "joint_frequency", "conditional_frequency", "association",
    }
