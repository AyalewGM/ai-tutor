"""Pin five-gap canonical evidence to source without claiming approved coverage."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "docs/curriculum/standards/md_g6_g7_five_concept_canonical_trace.wave1.v1.json"


def test_five_gap_trace_uses_existing_canonical_generators() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(data["findings"]) == 5
    assert data["summary"]["confirmed_absent_concepts"] == 0
    domain_sources = [
        ROOT / "app/domains/advanced_algebra_geometry_data.py",
        ROOT / "app/domains/geometry_reasoning_depth.py",
        ROOT / "app/domains/geometry_measurement.py",
        ROOT / "app/domains/percent.py",
    ]
    code = "\n".join(p.read_text(encoding="utf-8") for p in domain_sources)
    for finding in data["findings"]:
        for family in finding["canonical"]:
            assert f'"{family}"' in code, (finding["id"], family)
        assert finding["verdict"] in {
            "PARTIALLY_IMPLEMENTED",
            "IMPLEMENTED_BUT_ALIGNMENT_UNVERIFIED",
        }
        assert finding["missing_or_insufficient"]
    assert "rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)" in (
        ROOT / "app/domains/geometry_measurement.py"
    ).read_text(encoding="utf-8")


def test_review_and_mastery_gates_remain_closed() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["review_gates"] == {
        "math_review": "PENDING",
        "standards_mapping": "PROVISIONAL",
        "content_production": "CANDIDATE_REQUIREMENTS_NOT_APPROVED",
        "qa": "PENDING",
        "release": "NOT_AUTHORIZED",
    }
    assert all(data["safety"].values())
