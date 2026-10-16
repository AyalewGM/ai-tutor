"""CA Grade 1 source-scope author evidence must stay fail-closed."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def _load(name):
    return json.loads((ROOT / name).read_text())


def test_ca_grade1_author_scope_batches_complete_identifier_inventory():
    a = _load("ca_2013_grade1_bounded_scope_author_slice.v1.json")
    b = _load("ca_2013_grade1_remaining16_scope_author_slice.v1.json")
    c = _load("ca_2013_grade1_id_page_locator_author_slice.v1.json")
    rows = a["rows"] + b["rows"]
    ids = [row["expectation_id"] for row in rows]
    locators = {
        row["expectation_id"]: row["source_printed_page"]
        for row in c["expectations"]
    }
    assert len(a["rows"]) == 5
    assert len(b["rows"]) == 16
    assert len(ids) == len(set(ids)) == len(locators) == 21
    assert set(ids) == set(locators)
    for row in rows:
        assert row["printed_page"] == locators[row["expectation_id"]]
        assert row["pdf_page_index"] == row["printed_page"] + 6
        assert row["scope"]
    for batch in (a, b):
        assert batch["independent_source_fidelity"] == "PENDING"
        assert batch["activation"] == "FORBIDDEN"
        assert all(batch[key] == "UNVERIFIED" for key in (
            "canonical_equivalence", "generator", "assessment", "mastery"
        ))
    assert c["full_author_scope_audit_imported"] is False


def test_ca_grade1_new_batch_retains_material_scope_limits():
    d = _load("ca_2013_grade1_remaining16_scope_author_slice.v1.json")
    rows = {r["expectation_id"]: r["scope"] for r in d["rows"]}
    required = {
        "1.OA.2": ("three whole numbers", "at most 20"),
        "1.OA.3": ("commutativity", "associativity"),
        "1.OA.4": ("unknown-addend",),
        "1.OA.5": ("counting",),
        "1.OA.7": ("true or false",),
        "1.OA.8": ("three whole numbers",),
        "1.NBT.1": ("120",),
        "1.NBT.3": (">", "=", "<"),
        "1.NBT.4": ("within 100", "multiple of 10", "composing a ten"),
        "1.NBT.5": ("without counting",),
        "1.NBT.6": ("between 10 and 90", "positive or zero"),
        "1.MD.1": ("indirectly",),
        "1.MD.3": ("half-hours", "analog", "digital"),
        "1.MD.4": ("up to three categories", "more or fewer"),
        "1.G.1": ("nondefining",),
        "1.G.2": ("two-dimensional", "three-dimensional", "composite shapes"),
    }
    assert set(rows) == set(required)
    for code, fragments in required.items():
        assert all(fragment in rows[code] for fragment in fragments)
