import json
from pathlib import Path


def test_grade6_teks_percent_and_unit_conversion_qualifiers():
    base = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
    p = base / "tx_regular_grade6_proportionality_4e_5c_author.v1.json"
    rows = {r["id"]: r["scope"] for r in json.loads(p.read_text())["rows"]}
    assert "such as" in rows["111.26(b)(4)(F)"]
    assert "33 1/3%" in rows["111.26(b)(4)(F)"]
    assert "monetary" in rows["111.26(b)(4)(G)"]
    assert "within a measurement system" in rows["111.26(b)(4)(H)"]
    assert "concrete and pictorial" in rows["111.26(b)(5)(B)"]
