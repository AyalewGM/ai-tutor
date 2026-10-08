"""Independent deterministic oracles for Mihur's canonical congruence content."""

import math
import re

import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, generate

CODES = (
    "MATH.GEO.CONGRUENCE.SSS",
    "MATH.GEO.CONGRUENCE.SAS",
    "MATH.GEO.CONGRUENCE.ASA_AAS",
    "MATH.GEO.CONGRUENCE.HL",
    "MATH.GEO.CONGRUENCE.SSA",
    "MATH.GEO.CONGRUENCE.CPCTC",
)


def test_six_reusable_families_have_original_canonical_provenance():
    assert len(CODES) == 6
    for code in CODES:
        spec = FAMILIES[code]
        assert spec.canonical_skill_code == "MATH.GEO.CONGRUENCE"
        assert spec.modes == frozenset(LearningMode)
        assert "congruence_criteria" in spec.evidence_dimensions or code.endswith("CPCTC")
        generated = generate(code, seed=20261008, difficulty=3)
        assert generated.provenance["origin"] == "MIHUR_AUTHORED"
        assert generated.is_correct(generated.canonical_answer)
        assert generated.hints
        assert generated.misconception_answers
        assert all(not generated.is_correct(wrong) for wrong in generated.misconception_answers.values())


@pytest.mark.parametrize("code", CODES)
def test_determinism_diversity_and_mode_isolation(code):
    prompts = set()
    for seed in range(20):
        first = generate(code, seed=seed, difficulty=3)
        second = generate(code, seed=seed, difficulty=3)
        assert first == second
        prompts.add(first.prompt)
    assert len(prompts) >= 8
    variant_ids = {
        generate(code, seed="same-seed", difficulty=3, mode=mode).variant_id
        for mode in LearningMode
    }
    assert len(variant_ids) == len(LearningMode)


def test_existing_independent_variant_ids_are_unchanged():
    """Backward compatibility with materialized INDEPENDENT source keys."""
    import hashlib

    code = "MATH.EQ.TWO.DIRECT"
    seed = "existing-seed"
    difficulty = 3
    old_digest = hashlib.sha256(f"{code}|{seed}|{difficulty}".encode()).hexdigest()
    problem = generate(code, seed=seed, difficulty=difficulty)
    assert problem.variant_id == old_digest[:16]


@pytest.mark.parametrize("seed", range(40))
def test_sss_answer_requires_all_three_corresponding_sides(seed):
    problem = generate(CODES[0], seed=seed, difficulty=3)
    match = re.search(
        r"side lengths (\d+), (\d+), (\d+).*"
        r"side lengths (\d+), (\d+), (\d+)",
        problem.prompt,
    )
    assert match
    first = tuple(map(int, match.groups()[:3]))
    second = tuple(map(int, match.groups()[3:]))
    assert abs(first[0] - first[1]) < first[2] < first[0] + first[1]
    assert problem.canonical_answer == ("yes" if first == second else "no")


@pytest.mark.parametrize("seed", range(40))
def test_sas_included_angle_and_ssa_nonincluded_angle(seed):
    problem = generate(CODES[1], seed=seed, difficulty=3)
    included = "angle between those two sides" in problem.prompt
    assert problem.canonical_answer == ("yes" if included else "no")
    if not included:
        match = re.search(r"lengths (\d+) and (\d+).*a (\d+) degree angle", problem.prompt)
        assert match
        a, b, degrees = map(int, match.groups())
        # The SSA data permits two triangles (ambiguous case), not just a slogan.
        assert b > a > b * math.sin(math.radians(degrees))


@pytest.mark.parametrize("seed", range(40))
def test_asa_aas_classification_is_based_on_side_position(seed):
    problem = generate(CODES[2], seed=seed, difficulty=3)
    assert problem.canonical_answer == (
        "AAS" if "not between" in problem.prompt else "ASA"
    )


@pytest.mark.parametrize("seed", range(40))
def test_hl_requires_matching_hypotenuse_and_leg(seed):
    problem = generate(CODES[3], seed=seed, difficulty=3)
    match = re.search(r"hypotenuses measure (\d+) and (\d+)", problem.prompt)
    assert match
    hyp1, hyp2 = map(int, match.groups())
    assert problem.canonical_answer == ("yes" if hyp1 == hyp2 else "no")


@pytest.mark.parametrize("seed", range(40))
def test_ssa_counterexample_is_mathematically_ambiguous(seed):
    problem = generate(CODES[4], seed=seed, difficulty=3)
    match = re.search(r"sides of length (\d+) and (\d+).*a (\d+) degree", problem.prompt)
    assert match
    a, b, degrees = map(int, match.groups())
    assert b > a > b * math.sin(math.radians(degrees))
    assert problem.canonical_answer == "no"


@pytest.mark.parametrize("seed", range(40))
def test_cpctc_corresponding_side_has_identical_length(seed):
    problem = generate(CODES[5], seed=seed, difficulty=3)
    match = re.search(r"side (AB|BC|AC) is (\d+) cm.*side (DE|EF|DF)", problem.prompt)
    assert match
    side, length, corresponding = match.groups()
    assert {"AB": "DE", "BC": "EF", "AC": "DF"}[side] == corresponding
    assert problem.canonical_answer == length
