import json
from pathlib import Path


def test_grade6_teks_ratio_vs_rate_boundary():
    base = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
    p = base / "tx_regular_grade6_proportionality_4a_4d_author.v1.json"
    rows = {r["id"]: r["scope"] for r in json.loads(p.read_text())["rows"]}
    assert "y=ax" in rows["111.26(b)(4)(A)"]
    assert "y=x+a" in rows["111.26(b)(4)(A)"]
    assert "same attribute" in rows["111.26(b)(4)(C)"]
    assert "different-attribute" in rows["111.26(b)(4)(D)"]
