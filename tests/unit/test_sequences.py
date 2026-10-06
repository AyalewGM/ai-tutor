"""SEQUENCES generator: next term, common difference/ratio, nth
terms for arithmetic and geometric sequences, table reading,
classification and explicit rules, plus the SEQ misconception
rules."""

import random
from types import SimpleNamespace

from app.services.evaluation import MISCONCEPTION_RULES, _normalize
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(2500):
        generated = GENERATORS["SEQUENCES"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no SEQUENCES/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _rule(prompt: str, answer: str, canonical: str):
    rule = next(
        r for r in MISCONCEPTION_RULES if r.__name__ == "_sequence_errors")
    return rule(_normalize(prompt), answer, canonical)


def _correct_text(generated) -> str:
    return next(
        c["text"] for c in generated.choices if c["id"] == generated.canonical_answer)


def test_tier_coverage() -> None:
    for tier in ("next_term", "common_value"):
        assert _gen(tier, difficulty=1)
    for tier in ("nth_term", "geometric_nth", "table_term", "classify"):
        assert _gen(tier, difficulty=2)
    assert _gen("explicit_rule", difficulty=3)


def test_next_term_and_common_value_correctness() -> None:
    for seed in range(120):
        generated = GENERATORS["SEQUENCES"](random.Random(seed), 1)
        seq = generated.parameters["sequence"]
        tier = generated.parameters["tier"]
        if tier == "next_term":
            if "ratio" in generated.parameters:
                assert int(generated.canonical_answer) == seq[-1] * generated.parameters["ratio"]
            else:
                assert int(generated.canonical_answer) == seq[-1] + generated.parameters["difference"]
        elif tier == "common_value":
            if "ratio" in generated.parameters:
                assert int(generated.canonical_answer) == seq[1] // seq[0]
            else:
                assert int(generated.canonical_answer) == seq[1] - seq[0]


def test_nth_terms() -> None:
    arith = _gen("nth_term", difficulty=2)
    a1, d, n = (arith.parameters[k] for k in ("first", "difference", "n"))
    assert int(arith.canonical_answer) == a1 + (n - 1) * d
    geo = _gen("geometric_nth", difficulty=2)
    a1, r, n = (geo.parameters[k] for k in ("first", "ratio", "n"))
    assert int(geo.canonical_answer) == a1 * r ** (n - 1)


def test_table_term_renders_xy_table() -> None:
    generated = _gen("table_term", difficulty=2)
    assert generated.answer_kind == "MULTIPLE_CHOICE"
    spec = visualization_for(_as_problem(generated))
    assert spec is not None and spec["type"] == "xy_table"
    assert spec["col_labels"] == ["n", "a(n)"]
    pairs = generated.parameters["pairs"]
    last = pairs[-1][1]
    if "ratio" in generated.parameters:
        assert _correct_text(generated) == str(last * generated.parameters["ratio"])
    else:
        assert _correct_text(generated) == str(last + generated.parameters["difference"])


def test_only_table_term_has_a_visual() -> None:
    for tier, difficulty in (
            ("next_term", 1), ("common_value", 1), ("nth_term", 2),
            ("geometric_nth", 2), ("classify", 2), ("explicit_rule", 3)):
        assert visualization_for(_as_problem(_gen(tier, difficulty=difficulty))) is None


def test_off_by_one_is_seq_001() -> None:
    arith = _gen("nth_term", difficulty=2)
    a1, d, n = (arith.parameters[k] for k in ("first", "difference", "n"))
    match = _rule(arith.prompt, str(a1 + n * d), arith.canonical_answer)
    assert match is not None and match.code == "SEQ_001"
    geo = _gen("geometric_nth", difficulty=2)
    a1, r, n = (geo.parameters[k] for k in ("first", "ratio", "n"))
    match = _rule(geo.prompt, str(a1 * r ** n), geo.canonical_answer)
    assert match is not None and match.code == "SEQ_001"


def test_growth_type_confusion_is_seq_002() -> None:
    geo = _gen("geometric_nth", difficulty=2)
    a1, r, n = (geo.parameters[k] for k in ("first", "ratio", "n"))
    match = _rule(geo.prompt, str(a1 + (n - 1) * r), geo.canonical_answer)
    assert match is not None and match.code == "SEQ_002"


def test_rate_reported_as_term_is_seq_003() -> None:
    for seed in range(400):
        generated = GENERATORS["SEQUENCES"](random.Random(seed), 1)
        if generated.parameters["tier"] == "next_term" and "difference" in generated.parameters:
            match = _rule(
                generated.prompt, str(generated.parameters["difference"]),
                generated.canonical_answer)
            if match is None:
                continue  # d happens to equal the correct term
            assert match.code == "SEQ_003"
            return
    raise AssertionError("no arithmetic next_term item generated")


def test_classify_and_rule_distractors_are_tagged() -> None:
    generated = _gen("classify", difficulty=2)
    tagged = {c["text"]: c.get("misconception_code") for c in generated.choices}
    assert tagged[_correct_text(generated)] is None
    assert "SEQ_002" in tagged.values() and "SEQ_004" in tagged.values()
    rule_item = _gen("explicit_rule", difficulty=3)
    tagged = {c["text"]: c.get("misconception_code") for c in rule_item.choices}
    assert tagged[_correct_text(rule_item)] is None
    assert "SEQ_001" in tagged.values()


def test_classify_neither_has_changing_steps() -> None:
    for seed in range(400):
        generated = GENERATORS["SEQUENCES"](random.Random(seed), 2)
        if generated.parameters.get("tier") != "classify":
            continue
        text = _correct_text(generated)
        if not text.startswith("Neither"):
            continue
        seq = generated.parameters["sequence"]
        diffs = {seq[i] - seq[i - 1] for i in range(1, len(seq))}
        ratios = {seq[i] / seq[i - 1] for i in range(1, len(seq)) if seq[i - 1] != 0}
        assert len(diffs) > 1 and len(ratios) > 1
        return
    raise AssertionError("no 'neither' classify item generated")


def test_prompt_variety() -> None:
    prompts = {
        GENERATORS["SEQUENCES"](random.Random(seed), 3).prompt
        for seed in range(60)
    }
    assert len(prompts) > 40
