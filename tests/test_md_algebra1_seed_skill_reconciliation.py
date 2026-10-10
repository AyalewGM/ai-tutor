"""Contract checks for the read-only Maryland Algebra I seed-to-standards audit."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs" / "curriculum" / "standards"
RECON = DOCS / "md_algebra1_2026_27.seed_skill_reconciliation.v1.json"
STANDARDS = DOCS / "md_algebra1_traditional_2026_27.expectations.v1.json"
SEED = ROOT / "scripts" / "seed_algebra1.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_seeded_local_skills_reconciled_without_canonical_promotion() -> None:
    audit = _load(RECON)
    source = SEED.read_text(encoding="utf-8")
    seed_codes = set(re.findall(r'_skill\(db, curriculum, "(A1\.[^"]+)"', source))
    rows = audit["skills"]
    local_codes = {row["curriculum_local_skill_code"] for row in rows}
    assert len(seed_codes) == len(rows) == 15
    assert local_codes == seed_codes
    assert audit["summary"]["seed_local_skills"] == 15
    for row in rows:
        assert row["legacy_code_status"] == (
            "EXISTING_SEED_DERIVED_NOT_REVIEWED_ATOMIC_CANONICAL_ID"
        )
        assert row["classification"]["verified_mastery_evidence"] == (
            "NO_AND_MUST_NOT_BE_INFERRED"
        )


def test_relations_are_provisional_and_all_official_ids_exist() -> None:
    audit = _load(RECON)
    ids = {x["expectation_id"] for x in _load(STANDARDS)["expectations"]}
    covered = set()
    relation_count = 0
    for skill in audit["skills"]:
        for relation in skill["proposed_relations"]:
            assert relation["official_parent_standard_id"] in ids
            assert relation["relation"] in {
                "POTENTIAL_PARTIAL",
                "UNCONFIRMED_RELATED",
            }
            assert relation["review_status"] == "PROPOSED_UNVERIFIED"
            covered.add(relation["official_parent_standard_id"])
            relation_count += 1
    assert audit["summary"]["proposed_relations"] == relation_count
    assert audit["summary"]["standards_with_at_least_one_provisional_relation"] == (
        len(covered)
    )
    assert set(audit["unrelated_or_unmatched_official_standards"]) == ids - covered
    assert audit["summary"]["standards_with_no_provisional_relation"] == (
        len(ids) - len(covered)
    )


def test_reconciliation_cannot_activate_coverage_or_mastery() -> None:
    audit = _load(RECON)
    assert audit["status"] == (
        "DRAFT_REPOSITORY_SKILL_TO_OFFICIAL_STANDARD_RECONCILIATION"
    )
    assert audit["summary"]["accepted_relations"] == 0
    assert audit["summary"]["verified_coverage"] == 0
    assert audit["safety"] == {
        "activation": "FORBIDDEN",
        "canonical_id_creation": False,
        "learner_mastery_mutation": False,
        "source_code_mutation": False,
        "full_standard_coverage_from_partial": False,
    }
