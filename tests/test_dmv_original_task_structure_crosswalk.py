import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "docs/curriculum/standards/dmv_original_task_structure_crosswalk.v1.json"


def _load():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_dmv_crosswalk_is_fail_closed_and_ranked():
    data = _load()
    assert data["status"] == "DRAFT_UNVERIFIED_RESEARCH_ONLY_RUNTIME_DISABLED"
    assert data["governance"]["runtime_activation"] == "NOT_AUTHORIZED"
    assert data["governance"]["self_approval"] is False
    rows = data["task_structures"]
    assert 10 <= len(rows) <= 15
    assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))
    assert {row["canonical_disposition"] for row in rows} <= {
        "REUSE",
        "EXTEND",
        "PROPOSE_IDENTITY_REVIEW",
    }


def test_dmv_crosswalk_has_traceability_without_claiming_acceptance():
    data = _load()
    assert data["summary"]["accepted_standards_mappings"] == 0
    assert data["summary"]["qa_approved_packages"] == 0
    for row in data["task_structures"]:
        assert row["owners"]
        assert row["variability"]
        assert row["gap"]
        assert row["implementation"]["backend_independent_assessment"] != "APPROVED"
        assert row["implementation"]["qa"] == "NOT_REVIEWED"


def test_sources_are_official_and_research_only():
    data = _load()
    allowed_hosts = (
        "msde.maryland.gov",
        "mcap.msde.maryland.gov",
        "montgomeryschoolsmd.org",
        "amplify.com",
        "doe.virginia.gov",
        "osse.dc.gov",
    )
    for source in data["source_registry"]:
        assert source["url"].startswith("https://")
        assert any(host in source["url"] for host in allowed_hosts)
        assert "REFERENCE_ONLY" in source["license"] or "RESEARCH_ONLY" in source["license"]
        assert source["use_constraint"]


def test_legacy_virginia_task_codes_are_not_current_mappings():
    data = _load()
    source = next(s for s in data["source_registry"] if s["source_id"] == "VA_RICH_TASKS_2016")
    assert "2016" in source["publication_or_version"]
    assert "MUST NOT" in source["use_constraint"]


def test_current_mcps_listing_is_separate_from_vendor_and_standards_authority():
    data = _load()
    current = next(
        source
        for source in data["source_registry"]
        if source["source_id"] == "MCPS_CURRENT_CURRICULUM_2026"
    )
    amplify = next(
        source
        for source in data["source_registry"]
        if source["source_id"] == "AMPLIFY_DESMOS_6_12_CAREGIVER_2026"
    )

    expected = {
        "Math 6": "Amplify Desmos Math Grade 6",
        "Accelerated Math 6": "Amplify Desmos Math Accelerated Grade 6",
        "Math 7": "Amplify Desmos Math Grade 7",
        "Accelerated Math 7": "Amplify Desmos Math Accelerated Grade 7",
        "Math 8": "Amplify Desmos Math Grade 8",
        "Algebra 1": "Amplify Desmos Math Algebra 1",
        "Honors Geometry": "Illustrative Mathematics Geometry",
    }
    assert {
        row["mcps_course"]: row["curriculum"]
        for row in current["exact_listed_courses"]
    } == expected
    assert current["authority"] == "MCPS_CURRENT_DISTRICT_CURRICULUM_LISTING"
    assert current["standards_authority"] is False
    assert current["statewide_adoption_evidence"] is False

    assert amplify["authority"] == "VENDOR_UNIT_TOPIC_SEQUENCE_ONLY"
    assert amplify["standards_authority"] is False
    assert amplify["current_mcps_adoption_proof"] is False
    assert amplify["student_facing_link_allowed"] is False
    assert data["governance"]["vendor_units_are_standards_authority"] is False


def test_amplify_course_sequences_are_course_scoped_and_infer_no_standard_ids():
    data = _load()
    rows = data["mcps_current_course_sequences"]
    assert {row["mcps_course"] for row in rows} == {
        "Math 6",
        "Accelerated Math 6",
        "Math 7",
        "Accelerated Math 7",
        "Math 8",
        "Algebra 1",
    }
    assert all(row["units"] for row in rows)
    assert all(
        [unit["unit_number"] for unit in row["units"]]
        == list(range(1, len(row["units"]) + 1))
        for row in rows
    )
    assert all(row["evidence_authority"] == "VENDOR_UNIT_TOPIC_SEQUENCE_ONLY" for row in rows)
    assert all(row["maryland_standard_ids"] == [] for row in rows)
    assert all(row["student_facing_external_links"] is False for row in rows)
    assert data["summary"]["vendor_derived_standard_ids"] == 0


def test_historical_mcps_sources_cannot_prove_current_adoption():
    data = _load()
    legacy = next(
        source
        for source in data["source_registry"]
        if source["source_id"] == "MCPS_ALGEBRA1_SUPPORT"
    )
    assert legacy["authority"] == "HISTORICAL_RESEARCH_ONLY_NOT_CURRENT_ADOPTION_PROOF"
    assert legacy["current_adoption_evidence"] is False
    assert legacy["standards_authority"] is False

    assert len(data["historical_research_tracks"]) == 2
    for track in data["historical_research_tracks"]:
        assert track["status"] == "HISTORICAL_RESEARCH_ONLY_NOT_CURRENT_ADOPTION_PROOF"
        assert track["current_course_claim"] is False
        assert track["standards_mapping_authority"] is False
        assert track["student_facing_link_allowed"] is False


def test_publisher_topic_evidence_never_becomes_mapping_or_implementation_proof():
    data = _load()
    for row in data["task_structures"]:
        assert "publisher_sequence_evidence" in row
        for evidence in row["publisher_sequence_evidence"]:
            assert evidence["source_id"] == "AMPLIFY_DESMOS_6_12_CAREGIVER_2026"
            assert evidence["evidence_type"] == "VENDOR_UNIT_TOPIC_SEQUENCE_ONLY"
            assert evidence["standards_authority"] is False
        assert row["implementation"]["backend_independent_assessment"] != "APPROVED"
        assert row["implementation"]["qa"] == "NOT_REVIEWED"

    assert data["summary"]["accepted_standards_mappings"] == 0
    assert data["summary"]["qa_approved_packages"] == 0

def test_architecture_reconciliation_keeps_algebra_candidates_fail_closed():
    data = _load()
    assert data["revision"] == "2026-10-11-architecture-boundary-reconciliation-r3"
    assert data["governance"]["draft_candidates_are_canonical"] is False
    assert data["governance"]["integrated_tasks_award_component_mastery"] is False
    assert data["governance"]["one_response_one_primary_atom"] is True

    rows = {row["task_type_id"]: row for row in data["task_structures"]}
    exponent = rows["DMV.TASK.EXPONENTS.LAWS_EQUIVALENCE"]
    scientific = rows["DMV.TASK.SCIENTIFIC_NOTATION.CONVERT_OPERATE_REASONABLE"]
    polynomial = rows["DMV.TASK.POLYNOMIAL.MONOMIAL_DIVIDE_RESTRICT"]

    for row in (exponent, scientific, polynomial):
        assert row["canonical_disposition"] == "PROPOSE_IDENTITY_REVIEW"
        assert row["canonical_skill_codes"] == []
        assert "NO_BACK_OR_DUPLICATE_CREDIT" in row["architecture_boundary"]["integrated_task_semantics"]
        assert row["implementation"]["backend_independent_assessment"] != "APPROVED"
        assert row["implementation"]["qa"] == "NOT_REVIEWED"

    assert exponent["architecture_boundary"]["historical_family_not_expanded"] == "MATH.NS.EXPONENTS"
    assert scientific["architecture_boundary"]["historical_family_not_expanded"] == "MATH.NS.SCIENTIFIC_NOTATION"
    assert polynomial["architecture_boundary"]["historical_family_not_expanded"] == "MATH.EE.POLYNOMIAL_OPERATIONS"
    assert polynomial["architecture_boundary"]["candidate_codes"] == [
        "MATH.POLY.DIVIDE_MONOMIALS",
        "MATH.POLY.DIVIDE_POLYNOMIAL_BY_MONOMIAL",
    ]
    assert data["summary"]["ranked_task_types"] == 13
    assert data["summary"]["reuse"] == 3
    assert data["summary"]["extend"] == 7
    assert data["summary"]["propose_identity_review"] == 3

