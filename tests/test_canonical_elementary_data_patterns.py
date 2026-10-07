import re
from itertools import pairwise

from app.canonical_problem_families import FAMILIES, LearningMode, generate

CODES = [
    "MATH.DATA.BAR.COMPARE",
    "MATH.DATA.BAR.READ",
    "MATH.DATA.BAR.TOTAL",
    "MATH.DATA.FREQ.MODE",
    "MATH.DATA.LINEPLOT.DIFFERENCE",
    "MATH.DATA.LINEPLOT.FREQUENCY",
    "MATH.DATA.PICTURE.SCALE",
    "MATH.DATA.TALLY.READ",
    "MATH.PATTERN.ADDITIVE.NEXT",
    "MATH.PATTERN.ERROR.DIFFERENCE",
    "MATH.PATTERN.MULTIPLICATIVE.NEXT",
    "MATH.PATTERN.RULE.INPUT_OUTPUT",
]


def _build(code: str, seed: int = 23):
    problem = generate(code, seed=seed, difficulty=3)
    return problem.prompt, problem.canonical_answer, problem.hints, problem.misconception_answers


def test_elementary_data_pattern_batch_has_twelve_families() -> None:
    assert len(CODES) == 12
    skills = {FAMILIES[code].canonical_skill_code for code in CODES}
    assert {
        "MATH.DATA.ELEMENTARY.REPRESENT",
        "MATH.DATA.ELEMENTARY.COMPARE",
        "MATH.PATTERN.NUMERIC",
        "MATH.PATTERN.FUNCTION_RULE",
    } <= skills


def test_elementary_data_patterns_are_deterministic_and_support_all_modes() -> None:
    for code in CODES:
        assert _build(code, 71) == _build(code, 71), code
        assert FAMILIES[code].modes == frozenset(LearningMode), code


def test_elementary_misconceptions_do_not_collide_with_truth() -> None:
    for code in CODES:
        for seed in range(12):
            _, answer, _, misconceptions = _build(code, seed)
            truth = "".join(answer.lower().split())
            for candidate in misconceptions.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_picture_graph_scale_is_multiplicative() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DATA.PICTURE.SCALE", seed)
        match = re.fullmatch(
            r"In a picture graph, each symbol represents (\d+) students\. "
            r"A category has (\d+) symbols\. How many students does it represent\?",
            prompt,
        )
        assert match
        scale, symbols = map(int, match.groups())
        assert int(answer) == scale * symbols


def test_tally_groups_are_counted_in_fives() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DATA.TALLY.READ", seed)
        match = re.fullmatch(
            r"A tally table shows (\d+) complete groups of five marks and (\d+) extra marks\. "
            r"What count does it represent\?",
            prompt,
        )
        assert match
        groups, extras = map(int, match.groups())
        assert int(answer) == 5 * groups + extras


def test_additive_pattern_uses_constant_difference() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.PATTERN.ADDITIVE.NEXT", seed)
        values = [int(x) for x in re.search(r"\[(.*)\]", prompt).group(1).split(", ")]
        differences = [b - a for a, b in pairwise(values)]
        assert len(set(differences)) == 1
        assert int(answer) == values[-1] + differences[0]


def test_multiplicative_pattern_uses_constant_ratio() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.PATTERN.MULTIPLICATIVE.NEXT", seed)
        values = [int(x) for x in re.search(r"\[(.*)\]", prompt).group(1).split(", ")]
        ratios = [b // a for a, b in pairwise(values)]
        assert len(set(ratios)) == 1
        assert int(answer) == values[-1] * ratios[0]


def test_input_output_rule_matches_direct_oracle() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.PATTERN.RULE.INPUT_OUTPUT", seed)
        match = re.fullmatch(
            r"A rule multiplies an input by (\d+), then adds (\d+)\. "
            r"What is the output for input (\d+)\?",
            prompt,
        )
        assert match
        multiplier, addend, value = map(int, match.groups())
        assert int(answer) == multiplier * value + addend


def test_elementary_data_pattern_metadata_is_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario", "alberta"}
    for code, spec in FAMILIES.items():
        metadata = f"{code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)
