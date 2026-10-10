import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "on_mth1w_2021.expectations.v1.json"
)


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_mth1w_inventory_has_all_specific_b_to_f_expectations():
    data = _manifest()
    ids = [row["expectation_id"] for row in data["expectations"]]
    expected = {
        *(f"MTH1W.B1.{n}" for n in range(1, 4)),
        *(f"MTH1W.B2.{n}" for n in range(1, 3)),
        *(f"MTH1W.B3.{n}" for n in range(1, 6)),
        *(f"MTH1W.C1.{n}" for n in range(1, 6)),
        *(f"MTH1W.C2.{n}" for n in range(1, 4)),
        *(f"MTH1W.C3.{n}" for n in range(1, 4)),
        *(f"MTH1W.C4.{n}" for n in range(1, 5)),
        *(f"MTH1W.D1.{n}" for n in range(1, 4)),
        *(f"MTH1W.D2.{n}" for n in range(1, 6)),
        *(f"MTH1W.E1.{n}" for n in range(1, 7)),
        *(f"MTH1W.F1.{n}" for n in range(1, 5)),
    }
    assert len(ids) == 43
    assert len(ids) == len(set(ids))
    assert set(ids) == expected


def test_mth1w_inventory_is_fail_closed_and_does_not_infer_capabilities():
    data = _manifest()
    assert data["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert data["safety"] == {
        "activation": "FORBIDDEN",
        "mapping_review_required": True,
        "canonical_taxonomy_gate": (
            "PR #308 production TAXONOMY is empty; no DRAFT candidate is an "
            "authorized target."
        ),
        "learner_mastery_mutation": False,
        "verified_coverage_claim": False,
    }
    for row in data["expectations"]:
        classification = row["classification"]
        assert classification["mathematically_reviewed_skill"] == (
            "NO_CURRENT_INDEPENDENT_ACCEPTANCE_EVIDENCE"
        )
        assert classification["validated_practice"] == "NO_VERIFIED_EVIDENCE"
        assert classification["assessment_ready"] == "NO_VERIFIED_EVIDENCE"
        assert classification["verified_mastery_evidence"] == (
            "NO_AND_MUST_NOT_BE_INFERRED"
        )


def test_only_known_seeded_specific_expectations_have_existing_crosswalks():
    data = _manifest()
    mapped = {
        row["expectation_id"]
        for row in data["expectations"]
        if row["repository_existing_crosswalks"]
    }
    assert mapped == {
        "MTH1W.C1.2",
        "MTH1W.C1.3",
        "MTH1W.C1.4",
        "MTH1W.C1.5",
    }
    for row in data["expectations"]:
        for mapping in row["repository_existing_crosswalks"]:
            assert mapping["acceptance_status"] == (
                "UNVERIFIED_UNDER_CURRENT_TAXONOMY_GATE"
            )
