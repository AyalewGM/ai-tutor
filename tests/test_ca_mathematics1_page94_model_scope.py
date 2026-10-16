"""Safeguard selected CA Mathematics I page 94 scope qualifiers."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_page94_qualifiers():
    p = ROOT / "ca_math1_p94_sid6_abc_author_notes.v1.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    by_id = {r["expectation_id"]: " ".join(r["material_conditions"]).lower()
             for r in doc["rows"]}
    assert all(x in by_id["S-ID.6.a"]
               for x in ("linear", "quadratic", "exponential"))
    assert "residuals" in by_id["S-ID.6.b"]
    assert doc["independent_source_fidelity"] == "PENDING"
    assert doc["activation"] == "FORBIDDEN"
