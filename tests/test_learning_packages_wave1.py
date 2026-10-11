"""Fail-closed structural and independent arithmetic checks for DRAFT learning wave 1.

Run: pytest -q tests/test_learning_packages_wave1.py
No runtime activation, student records, or production imports.
"""
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/curriculum/drafts/learning-packages-wave1/content.draft.json"


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_batch_is_review_gated_and_complete():
    data = load()
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["runtime_activation"] is False
    assert data["mastery_writes"] is False
    assert len(data["packages"]) == 5
    ids = [p["id"] for p in data["packages"]]
    assert len(ids) == len(set(ids))
    for p in data["packages"]:
        assert p["status"] == "DRAFT_UNVERIFIED"
        assert p["runtime_activation"] is False
        assert p["mastery_writes"] is False
        assert p["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"
        assert p["independent_math_review"] == "PENDING"
        assert len(p["worked_examples"]) >= 5
        assert len(p["misconception_pathways"]) >= 3
        assert len(p["guided_practice"]) >= 4
        assert len(p["independent_assessment"]) >= 3
        assert len(p["lesson_sequence"]) >= 5
        assert p["interactive_spec"]["a11y"]
        assert p["interactive_spec"]["independent_assessment"]
        for m in p["misconception_pathways"]:
            assert len(m["socratic_hints"]) >= 2
        for a in p["independent_assessment"]:
            assert a["hint_access"] is False
            assert a["feedback_visibility"] == "AFTER_SUBMISSION"


def test_independent_volume_oracles():
    # Recalculate representative rational-edge cases independently.
    assert Fraction(3, 4) * Fraction(2, 3) * 6 == 3
    assert Fraction(5, 2) * Fraction(4, 5) * Fraction(3, 2) == 3
    assert Fraction(9, 4) / Fraction(3, 2) == Fraction(3, 2)
    assert Fraction(1, 2) ** 3 == Fraction(1, 8)


def test_independent_percent_oracles():
    from decimal import Decimal
    assert Decimal("0.045") * Decimal(200) == Decimal(9)
    assert Decimal(160) * Decimal("1.03") == Decimal("164.80")
    assert abs(Decimal(36) - Decimal(40)) / Decimal(40) * 100 == 10
    assert Decimal("0.075") * Decimal(120) == Decimal(9)
    assert Decimal("0.06") * Decimal(350) == Decimal(21)
    assert Decimal(240) + Decimal("0.025") * Decimal(240) == Decimal(246)
    assert abs(Decimal(78) - Decimal(80)) / Decimal(80) * 100 == Decimal("2.5")


def test_percent_transfer_requires_distinct_base_meaning_and_units():
    package = next(p for p in load()["packages"] if p["id"] == "W1-G7-PERCENT-COMMISSION-ERROR")
    transfer = package["independent_assessment"][-1]
    assert transfer["response_fields"] == [
        "structure_by_case",
        "reference_base_by_case",
        "calculation_by_case",
        "meaning_and_units_by_case",
    ]
    oracle = transfer["answer"]
    assert {oracle[case]["structure"] for case in oracle} == {
        "PART_OF_BASE",
        "BASE_PLUS_PERCENT",
        "RELATIVE_DIFFERENCE_TO_REFERENCE",
    }
    assert oracle["A"]["result"] == "$21 received"
    assert oracle["B"]["result"] == "$246 final charge"
    assert oracle["C"]["result"] == "2.5% of the reference"
    assert set(transfer["diagnosis_by_error"]) == {
        "A_BASE_SELECTION",
        "B_FEE_VS_TOTAL",
        "C_REFERENCE_DENOMINATOR",
    }
    for route in transfer["diagnosis_by_error"].values():
        assert set(route) == {"socratic_probe", "next_activity", "fresh_exit"}
        assert all(route.values())
    assert "no combined-task back-credit or double credit" in package["mastery_gate"]["require"]


def test_independent_linear_oracles():
    assert (10 - 2) / (3 - (-1)) == 2
    assert 48 / 6 == 8
    assert 2 * 2 + 1 == -2 + 7


def test_linear_package_is_one_context_to_domain_evidence_chain():
    package = next(p for p in load()["packages"] if p["id"] == "W1-G9-LINEAR-MODELING")
    assert "context → table → graph → equation" in package["objective"]
    combined_text = json.dumps(package)
    assert "Find intersection" not in combined_text
    assert "Solve 2x+5=17" not in combined_text
    evidence = package["independent_assessment"][1]
    assert evidence["response_fields"] == [
        "graph_choice",
        "equation",
        "table_graph_consistency",
        "physical_domain",
        "domain_justification",
    ]
    assert evidence["answer"] == (
        "the decreasing line through the three table points; V(t)=30−3t; 0≤t≤10"
    )
    assert "no claim for standalone equation solving or line intersection" in (
        package["mastery_gate"]["require"]
    )
    assert "PR #334 R4 at 8887da16" in package["provenance"]["gap_register"]
