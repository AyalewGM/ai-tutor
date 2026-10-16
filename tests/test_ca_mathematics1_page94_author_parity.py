"""California Math I page 94: author-only parity; no publisher acceptance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = (
    "ca_math1_p94_g_gpe3_author_notes.v1.json",
    "ca_math1_p94_sid1_2_author_notes.v1.json",
    "ca_math1_p94_sid3_5_author_notes.v1.json",
    "ca_math1_p94_sid6_abc_author_notes.v1.json",
    "ca_math1_p94_sid7_9_author_notes.v1.json",
)


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_math1_page94_inventory_and_gate():
    batches = [read(f) for f in FILES]
    ids = [r["expectation_id"] for b in batches for r in b["rows"]]
    audit = read("ca_2013_mathematics1_pages90_94_author_audit.v1.json")
    assert ids == [r["expectation_id"] for r in audit["rows"]
                   if r["source_printed_page"] == 94]
    assert len(ids) == len(set(ids)) == 13
    for b in batches:
        assert (b["source_printed_page"], b["source_pdf_zero_based_page_index"]) == (94, 100)
        assert b["supplemental_existing_placements_only"] is True
        assert b["independent_source_fidelity"] == "PENDING"
        assert b["activation"] == "FORBIDDEN"
