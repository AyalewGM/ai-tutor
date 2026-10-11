import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = (
    ROOT
    / "docs/curriculum/taxonomy_candidate_scope.algebra_boundaries.v1.json"
)


def _load():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _cards(data):
    return {card["proposed_code"]: card for card in data["cards"]}


def test_algebra_scope_cards_are_draft_and_runtime_inert():
    data = _load()
    assert data["review_state"] == (
        "DRAFT_PENDING_INDEPENDENT_MATHEMATICAL_REVIEW_"
        "AND_ARCHITECTURE_COLLISION_CONFIRMATION"
    )
    assert data["authority"] == "NONE_NOT_FOR_RUNTIME"
    assert data["preservation"] == {
        "production_taxonomy_changed": False,
        "aliases_changed": False,
        "standards_mappings_changed": False,
        "learner_records_changed": False,
        "historical_mastery_changed": False,
        "runtime_activation": False,
    }


def test_algebra_scope_cards_are_unique_complete_and_collision_audited():
    data = _load()
    cards = data["cards"]
    assert len(cards) == 11
    codes = [card["proposed_code"] for card in cards]
    assert len(codes) == len(set(codes))
    assert all(code.startswith("MATH.") for code in codes)

    for card in cards:
        assert card["scope_rule"]
        assert card["inclusions"]
        assert card["exclusions"]
        assert card["prerequisite_concepts"]
        assert card["boundary_conditions"]
        assert card["examples"]
        assert card["misconceptions"]
        assert card["assessment_evidence"]["required"]
        assert card["assessment_evidence"]["exact_oracle"]
        assert card["collision_audit"]["exact_code_on_main"] == (
            "NOT_FOUND_IN_PRODUCTION_TAXONOMY_OR_MERGED_CANDIDATE_SCOPE_REGISTRIES"
        )
        assert "PENDING_INDEPENDENT_MATHEMATICAL_REVIEW" in (
            card["collision_audit"]["disposition"]
        )


def test_historical_broad_families_are_never_proposed_as_new_atoms():
    data = _load()
    codes = {card["proposed_code"] for card in data["cards"]}
    assert codes.isdisjoint(
        {
            "MATH.NS.EXPONENTS",
            "MATH.NS.SCIENTIFIC_NOTATION",
            "MATH.NS.ROOTS",
            "MATH.EE.POLYNOMIAL_OPERATIONS",
            "MATH.EXP.PRODUCT",
            "MATH.EXP.QUOTIENT",
            "MATH.EXP.POWER",
        }
    )


def test_exponent_atoms_preserve_zero_negative_and_domain_boundaries():
    cards = _cards(_load())
    exponent_codes = {
        "MATH.EXPONENT.LAW.PRODUCT",
        "MATH.EXPONENT.LAW.QUOTIENT",
        "MATH.EXPONENT.LAW.POWER_OF_POWER",
        "MATH.EXPONENT.ZERO_NONZERO_BASE",
        "MATH.EXPONENT.NEGATIVE_AS_RECIPROCAL",
    }
    assert exponent_codes <= cards.keys()

    zero = cards["MATH.EXPONENT.ZERO_NONZERO_BASE"]
    assert any(example.get("input") == "0^0" and example.get("valid") is False for example in zero["examples"])
    assert "a≠0" in zero["scope_rule"]

    negative = cards["MATH.EXPONENT.NEGATIVE_AS_RECIPROCAL"]
    assert "a≠0" in negative["scope_rule"]
    assert any(example.get("input") == "0^-2" and example.get("valid") is False for example in negative["examples"])

    quotient = cards["MATH.EXPONENT.LAW.QUOTIENT"]
    assert any("original denominator" in item for item in quotient["boundary_conditions"])


def test_scientific_notation_operations_are_independent_atoms():
    cards = _cards(_load())
    conversion = cards["MATH.SCIENTIFIC_NOTATION.CONVERT_NORMALIZE"]
    multiplication = cards["MATH.SCIENTIFIC_NOTATION.MULTIPLY_NORMALIZE"]
    division = cards["MATH.SCIENTIFIC_NOTATION.DIVIDE_NORMALIZE"]

    for card in (conversion, multiplication, division):
        assert "1≤|a|<10" in card["scope_rule"]
    assert any("zero" in item.lower() for item in conversion["boundary_conditions"])
    assert any("zero denominator" in item.lower() for item in division["exclusions"])
    assert multiplication["proposed_code"] != division["proposed_code"]


def test_polynomial_division_is_two_atoms_with_one_prerequisite_edge():
    cards = _cards(_load())
    monomial = cards["MATH.POLY.DIVIDE_MONOMIALS"]
    polynomial = cards["MATH.POLY.DIVIDE_POLYNOMIAL_BY_MONOMIAL"]

    assert polynomial["prerequisite_concepts"][0] == monomial["proposed_code"]
    assert any("every term" in item.lower() for item in polynomial["inclusions"])
    assert any("original-divisor restrictions" in item.lower() for item in polynomial["assessment_evidence"]["required"])
    assert any("order-independent" in item.lower() for item in polynomial["assessment_evidence"]["required"])
    assert any("negative-result exponent" in item.lower() for item in polynomial["assessment_evidence"]["required"])


def test_square_equation_card_requires_complete_real_solution_sets():
    card = _cards(_load())["MATH.ALGEBRA.SQUARE_EQUATION_REAL_SOLUTIONS"]
    assert "two solutions when r>0" in card["scope_rule"]
    assert "one repeated solution when r=0" in card["scope_rule"]
    assert "no real solutions when r<0" in card["scope_rule"]

    examples = {example["input"]: example for example in card["examples"]}
    assert set(examples["(-2x+1)^2=9"]["answer_set"]) == {"-1", "2"}
    assert examples["(3x+6)^2=0"]["answer_set"] == ["-2"]
    assert examples["(x-4)^2=-5"]["answer_set"] == []

    principal = next(
        item for item in card["misconceptions"] if item["code"] == "ROOT.PRINCIPAL_ONLY"
    )
    assert "ax+b=+√r" in principal["response_pattern"]


def test_reporting_profiles_are_noncanonical_and_award_no_credit():
    data = _load()
    codes = {card["proposed_code"] for card in data["cards"]}
    profiles = data["noncanonical_reporting_profiles"]
    assert {profile["profile_id"] for profile in profiles} == {
        "EXPONENT_LAWS_COMBINED",
        "SCIENTIFIC_NOTATION_OPERATIONS",
        "POLYNOMIAL_DIVISION",
    }
    for profile in profiles:
        assert profile["semantics"] == "REPORTING_ONLY_ALL_OF"
        assert set(profile["members"]) <= codes
        assert profile["credit_rule"] == "NO_DIRECT_OR_COMPONENT_MASTERY_FROM_PROFILE_RESPONSE"
