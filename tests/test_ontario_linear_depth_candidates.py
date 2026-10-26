"""Author-side exact-oracle, diagnostic-contract and transfer regressions."""
from __future__ import annotations

import json
import re
from fractions import Fraction

import pytest
from sympy import Eq, Rational, S, Symbol, solveset

from scripts.author_ontario_linear_depth import (
    FAMILIES,
    MODES,
    PRESENTATIONS,
    SKILLS,
    TRANSFER_FAMILY,
    _task_fingerprint,
    authored_journey_learner_projection,
    create_candidate,
    create_pack,
    create_unhinted_transfer,
    learner_projection,
    simulate_authored_learning_journey,
)


def _coefficients_from_prompt(data: dict) -> dict[str, str]:
    """Independently parse actual student text to catch prompt/oracle divergence."""
    family = data["candidate_family"]
    presentation = data["presentation_id"]
    prompt = data["prompt"]
    if family == "TWO_STEP_SIGNED_RATIONAL":
        if presentation == "VARIABLE_TERM_FIRST":
            m = re.fullmatch(r"Solve (-?\d+)x ([+-]\d+) = (-?\d+)\.", prompt)
            assert m is not None
            a, b, d = map(int, m.groups())
            result = (Fraction(a), Fraction(b), Fraction(0), Fraction(d))
        elif presentation == "CONSTANT_TERM_FIRST":
            m = re.fullmatch(r"Solve (-?\d+) ([+-]\d+)x = (-?\d+)\.", prompt)
            assert m is not None
            b, a, d = map(int, m.groups())
            result = (Fraction(a), Fraction(b), Fraction(0), Fraction(d))
        else:
            m = re.fullmatch(r"Solve (-?\d+) = (-?\d+)x ([+-]\d+)\.", prompt)
            assert m is not None
            d, a, b = map(int, m.groups())
            result = (Fraction(0), Fraction(d), Fraction(a), Fraction(b))
    elif family == "TWO_STEP_FRACTIONAL_COEFFICIENT":
        if presentation == "VARIABLE_TERM_FIRST":
            m = re.fullmatch(
                r"Solve \((-?\d+)/(\d+)\)x ([+-]\d+) = (-?\d+)\.",
                prompt,
            )
            assert m is not None
            a, den, b, d = map(int, m.groups())
            result = (Fraction(a, den), Fraction(b), Fraction(0), Fraction(d))
        elif presentation == "CONSTANT_TERM_FIRST":
            m = re.fullmatch(
                r"Solve (-?\d+) ([+-]) \((\d+)/(\d+)\)x = (-?\d+)\.",
                prompt,
            )
            assert m is not None
            b, sign, numerator, den, d = m.groups()
            a = int(numerator) if sign == "+" else -int(numerator)
            result = (Fraction(a, int(den)), Fraction(int(b)), Fraction(0), Fraction(int(d)))
        else:
            m = re.fullmatch(
                r"Solve (-?\d+) = \((-?\d+)/(\d+)\)x ([+-]\d+)\.",
                prompt,
            )
            assert m is not None
            d, a, den, b = map(int, m.groups())
            result = (Fraction(0), Fraction(d), Fraction(a, den), Fraction(b))
    elif family == "MULTISTEP_NEGATIVE_DISTRIBUTION":
        if presentation == "VARIABLE_TERM_FIRST":
            m = re.fullmatch(
                r"Solve -(\d+)\(x - \((-?\d+)\)\) \+ \((-?\d+)\) = (-?\d+)\.",
                prompt,
            )
            assert m is not None
            k, b, c, d = map(int, m.groups())
            result = (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(d))
        elif presentation == "CONSTANT_TERM_FIRST":
            m = re.fullmatch(
                r"Solve \((-?\d+)\) - (\d+)\(x - \((-?\d+)\)\) = (-?\d+)\.",
                prompt,
            )
            assert m is not None
            c, k, b, d = map(int, m.groups())
            result = (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(d))
        else:
            m = re.fullmatch(
                r"Solve (-?\d+) = -(\d+)\(x - \((-?\d+)\)\) \+ \((-?\d+)\)\.",
                prompt,
            )
            assert m is not None
            d, k, b, c = map(int, m.groups())
            result = (Fraction(0), Fraction(d), Fraction(-k), Fraction(k * b + c))
    else:
        assert family == "MULTISTEP_VARIABLES_BOTH_SIDES"
        if presentation == "CONSTANT_TERM_FIRST":
            m = re.fullmatch(
                r"Solve (-?\d+) ([+-]\d+)x = (-?\d+) ([+-]\d+)x\.",
                prompt,
            )
            assert m is not None
            b, a, d, c = map(int, m.groups())
            result = (Fraction(a), Fraction(b), Fraction(c), Fraction(d))
        else:
            m = re.fullmatch(
                r"Solve (-?\d+)x ([+-]\d+) = (-?\d+)x ([+-]\d+)\.",
                prompt,
            )
            assert m is not None
            a, b, c, d = map(int, m.groups())
            result = (Fraction(a), Fraction(b), Fraction(c), Fraction(d))
    return dict(
        zip(
            ("lhs_x", "lhs_constant", "rhs_x", "rhs_constant"),
            (str(value) for value in result),
        )
    )


def _independent_solution(data: dict) -> Fraction:
    x = Symbol("x")
    p = data["equation_coefficients"]
    lhs = Rational(p["lhs_x"]) * x + Rational(p["lhs_constant"])
    rhs = Rational(p["rhs_x"]) * x + Rational(p["rhs_constant"])
    solved = solveset(Eq(lhs, rhs), x, domain=S.Reals)
    assert solved.is_FiniteSet and len(solved) == 1
    root = next(iter(solved))
    return Fraction(int(root.p), int(root.q))


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", MODES)
def test_exact_noninteger_oracle_and_multi_probe_contract_for_60_seeds(family, mode):
    for seed in range(60):
        q = create_candidate(family, seed=seed, mode=mode)
        correct = Fraction(q["canonical_answer"].split("=", 1)[1])
        wrong = Fraction(q["misconception_answer"].split("=", 1)[1])
        assert correct.denominator > 1
        assert _coefficients_from_prompt(q) == q["equation_coefficients"]
        assert _independent_solution(q) == correct
        assert wrong != correct
        assert q["canonical_skill_hint"] == SKILLS[family]
        contract = q["diagnostic_contract_for_author_review"]
        assert contract["classification_policy"] == "DO_NOT_CLASSIFY_FROM_ONE_RESPONSE"
        assert contract["minimum_corroborating_signals"] == 2
        assert len(contract["signals"]) >= 2
        responses = [
            Fraction(signal["candidate_response"].split("=", 1)[1])
            for signal in contract["signals"]
        ]
        assert len(responses) == len(set(responses))
        assert correct not in responses
        for signal in contract["signals"]:
            assert signal["confirmation_probe_for_author_review"]
            assert signal["confirmation_oracle_for_author_review"]
            assert len(signal["socratic_repair_for_author_review"]) == 2
        projection = json.dumps(learner_projection(q)).casefold()
        assert "answer" not in projection
        assert "hint" not in projection
        assert "misconception" not in projection
        assert q == create_candidate(family, seed=seed, mode=mode)


@pytest.mark.parametrize("family", FAMILIES)
def test_all_presentation_layouts_are_seed_reachable(family):
    observed = {
        create_candidate(family, seed=seed, mode="GUIDED")["presentation_id"]
        for seed in range(120)
    }
    assert observed == set(PRESENTATIONS[family])


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("target_mode", ("INDEPENDENT", "MASTERY"))
def test_unhinted_transfer_changes_reasoning_family_task_and_answer(family, target_mode):
    source = create_candidate(family, seed=11, mode="GUIDED")
    transfer = create_unhinted_transfer(source, target_mode=target_mode)
    assert transfer["source_family"] == family
    assert transfer["target_family"] == TRANSFER_FAMILY[family]
    assert SKILLS[transfer["target_family"]] == SKILLS[family]
    assert transfer["target_mode"] == target_mode
    assert (
        transfer["source_reasoning_structure_id"]
        != transfer["target_reasoning_structure_id"]
    )
    assert transfer["reasoning_structure_changed"] is True
    assert isinstance(transfer["presentation_changed"], bool)
    assert transfer["task_fingerprint_changed"] is True
    assert transfer["answer_changed"] is True
    assert transfer["hints_allowed"] is False
    assert transfer["hinted_success_counts_as_independent"] is False
    assert transfer["runtime_credit_authorized"] is False
    learner = json.dumps(transfer["learner_task"]).casefold()
    assert "answer" not in learner
    assert "hint" not in learner
    assert "misconception" not in learner


def test_mode_pools_and_pack_are_distinct_and_fail_closed():
    pack = create_pack(count_per_family_mode=25)
    assert pack["schema"] == "MIHUR_DRAFT_RATIONAL_EQUATION_CANDIDATES_V5"
    assert len(pack["candidates"]) == 25 * len(FAMILIES) * len(MODES)
    assert pack["runtime_registered"] is False
    assert pack["runtime_activation"] is False
    assert pack["math_review"] == "PENDING_INDEPENDENT"
    assert pack["diagnosis_requires_multiple_probes"] is True
    assert (
        pack["authored_learning_journey"]
        == "RESPONSE_PROBE_REPAIR_RETEST_TRANSFER_V1"
    )
    assert pack["hinted_success_counts_as_independent"] is False
    assert pack["transfer_requires_changed_reasoning_structure"] is True
    assert pack["transfer_requires_changed_presentation"] is False
    assert pack["task_fingerprint_version"] == "AFFINE_SIDE_SYMMETRY_V1"
    assert len({q["variant_id"] for q in pack["candidates"]}) == len(pack["candidates"])
    for family in FAMILIES:
        group = [q for q in pack["candidates"] if q["candidate_family"] == family]
        assert len({q["task_fingerprint"] for q in group}) == len(group)
        assert {q["mode"] for q in group} == set(MODES)
        assert {q["presentation_id"] for q in group} == set(PRESENTATIONS[family])
        assert {q["reasoning_structure_id"] for q in group} == {family}
    assert pack == create_pack(count_per_family_mode=25)


@pytest.mark.parametrize("family", FAMILIES)
def test_authored_journey_routes_corroborated_error_to_fresh_guided_retest(family):
    source = create_candidate(family, seed=37, mode="GUIDED")
    signal = source["diagnostic_contract_for_author_review"]["signals"][0]

    confirm = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
    )
    assert confirm["stage"] == "CONFIRM_REASONING"
    assert confirm["confirmed_misconception_for_author_review"] is None
    assert len(confirm["confirmation_choices"]) == 3
    public_confirm = authored_journey_learner_projection(confirm)
    assert "misconception" not in json.dumps(public_confirm).casefold()
    assert "evidence_choice" not in json.dumps(public_confirm).casefold()

    guided = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
    )
    assert guided["stage"] == "GUIDED_RETEST"
    retest = guided["private_guided_retest_for_author_review"]
    assert retest["candidate_family"] == family
    assert retest["task_fingerprint"] != source["task_fingerprint"]
    assert retest["canonical_answer"] != source["canonical_answer"]
    assert signal["misconception_code"] in {
        item["misconception_code"]
        for item in retest["diagnostic_contract_for_author_review"]["signals"]
    }
    public_guided = authored_journey_learner_projection(guided)
    assert public_guided["guided_retest_task"] == learner_projection(retest)
    assert "canonical_answer" not in json.dumps(public_guided)
    assert "oracle" not in json.dumps(public_guided).casefold()


@pytest.mark.parametrize("family", FAMILIES)
def test_authored_journey_requires_retest_then_unhinted_independent_exit(family):
    source = create_candidate(family, seed=83, mode="GUIDED")
    signal = source["diagnostic_contract_for_author_review"]["signals"][0]
    guided = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
    )
    retest = guided["private_guided_retest_for_author_review"]

    retry = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
        guided_retest_response="x=0",
        readiness_confirmed=True,
    )
    assert retry["stage"] == "GUIDED_RETEST_RETRY"
    assert "private_transfer_for_author_review" not in retry

    ready = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
        guided_retest_response=retest["canonical_answer"],
    )
    assert ready["stage"] == "READY_FOR_TRANSFER_CONFIRMATION"
    assert ready["guided_retest_succeeded"] is True
    assert ready["guided_success_counts_as_independent"] is False

    independent = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
        guided_retest_response=retest["canonical_answer"],
        readiness_confirmed=True,
    )
    assert independent["stage"] == "INDEPENDENT_EXIT"
    transfer = independent["private_transfer_for_author_review"]
    assert transfer["target_family"] == TRANSFER_FAMILY[family]
    assert transfer["target_mode"] == "INDEPENDENT"
    assert transfer["hints_allowed"] is False
    public_exit = authored_journey_learner_projection(independent)
    assert public_exit["independent_task"] == transfer["learner_task"]
    assert "socratic_repair" not in json.dumps(public_exit)
    assert "oracle" not in json.dumps(public_exit).casefold()

    independent_retry = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
        guided_retest_response=retest["canonical_answer"],
        readiness_confirmed=True,
        independent_response="x=0",
    )
    assert independent_retry["stage"] == "INDEPENDENT_RETRY"
    assert independent_retry["independent_success"] is False
    public_retry = authored_journey_learner_projection(independent_retry)
    assert "socratic_repair" not in json.dumps(public_retry)
    assert "oracle" not in json.dumps(public_retry).casefold()

    complete = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
        guided_retest_response=retest["canonical_answer"],
        readiness_confirmed=True,
        independent_response=transfer["private_exact_oracle_for_review"],
    )
    assert complete["stage"] == "COMPLETE"
    assert complete["independent_success"] is True
    assert complete["guided_success_counts_as_independent"] is False
    assert [
        event["stage"]
        for event in complete["journey_transcript_for_author_review"]
    ] == [
        "PRACTICE",
        "CONFIRM_REASONING",
        "GUIDED_RETEST",
        "READY_FOR_TRANSFER_CONFIRMATION",
        "INDEPENDENT_EXIT",
        "COMPLETE",
    ]


@pytest.mark.parametrize("family", FAMILIES)
def test_authored_journey_withholds_diagnosis_for_ambiguous_evidence(family):
    source = create_candidate(family, seed=121, mode="GUIDED")
    signal = source["diagnostic_contract_for_author_review"]["signals"][0]
    disconfirming_choice = next(
        choice["id"]
        for choice in signal["confirmation_choices_for_learner"]
        if choice["id"]
        != signal["confirmation_evidence_choice_for_author_review"]
    )
    ambiguous = simulate_authored_learning_journey(
        source,
        practice_response=signal["candidate_response"],
        follow_up_reasoning_response=disconfirming_choice,
    )
    assert ambiguous["stage"] == "PRACTICE_RETRY"
    assert ambiguous["confirmed_misconception_for_author_review"] is None
    assert "socratic_repair_questions" not in ambiguous

    unmatched = simulate_authored_learning_journey(
        source,
        practice_response="x=999999",
        follow_up_reasoning_response=signal[
            "confirmation_evidence_choice_for_author_review"
        ],
    )
    assert unmatched["stage"] == "PRACTICE_RETRY"
    assert unmatched["confirmed_misconception_for_author_review"] is None
    assert "socratic_repair_questions" not in unmatched


def test_authored_journey_correct_practice_bypasses_repair_and_bad_modes_fail():
    source = create_candidate(FAMILIES[0], seed=5, mode="GUIDED")
    ready = simulate_authored_learning_journey(
        source,
        practice_response=source["canonical_answer"],
    )
    assert ready["stage"] == "READY_FOR_TRANSFER_CONFIRMATION"
    assert ready["practice_was_correct"] is True
    assert ready["confirmed_misconception_for_author_review"] is None

    with pytest.raises(ValueError):
        simulate_authored_learning_journey(
            create_candidate(FAMILIES[0], seed=5, mode="INDEPENDENT"),
            practice_response="x=1",
        )


@pytest.mark.parametrize("family", FAMILIES)
def test_reordered_or_swapped_affine_equations_are_one_mathematical_task(family):
    original = (Fraction(3, 4), Fraction(-7), Fraction(-2), Fraction(5, 3))
    swapped = (original[2], original[3], original[0], original[1])
    # The display structure must not create a new mathematical task identity.
    assert _task_fingerprint(family, original) == _task_fingerprint(family, swapped)
    # Changing a term should make a genuinely different equation.
    changed = (original[0], original[1] + 1, original[2], original[3])
    assert _task_fingerprint(family, original) != _task_fingerprint(family, changed)


def test_unseen_mode_pool_deduplicates_sides_reversed_and_term_order():
    # Different presentation layouts can represent an identical affine
    # equation; separate hashes would falsely declare independent transfer.
    family = FAMILIES[0]
    terms_first = (Fraction(5), Fraction(-7), Fraction(0), Fraction(8))
    constant_first = (Fraction(5), Fraction(-7), Fraction(0), Fraction(8))
    sides_reversed = (Fraction(0), Fraction(8), Fraction(5), Fraction(-7))
    fingerprints = {
        _task_fingerprint(family, item)
        for item in (terms_first, constant_first, sides_reversed)
    }
    assert len(fingerprints) == 1
    # Distinct mathematical *representations* are intentionally preserved
    # between families; the user must still make the same-family transfer.
    assert _task_fingerprint(FAMILIES[1], terms_first) not in fingerprints


def test_invalid_requests_cannot_bypass_scope():
    with pytest.raises(ValueError):
        create_candidate("UNKNOWN", seed=1, mode="GUIDED")
    with pytest.raises(ValueError):
        create_candidate(FAMILIES[0], seed=1, mode="EXTENSION")
    with pytest.raises(ValueError):
        create_pack(count_per_family_mode=0)
    with pytest.raises(ValueError):
        create_pack(count_per_family_mode=101)
    source = create_candidate(FAMILIES[0], seed=1, mode="GUIDED")
    with pytest.raises(ValueError):
        create_unhinted_transfer(source, target_mode="GUIDED")
