"""Fail-closed regression for bounded DC Grade 8 function scope evidence."""
import json
from pathlib import Path
LEDGER = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "dc_grades6_8_ccss.source_fidelity_locators.v1.json"
)


def _corrections() -> dict[str, dict]:
    evidence = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = {row["expectation_id"]: row for row in evidence["records"]}
    return {
        standard_id: rows[standard_id][
            "retrospective_source_fidelity_correction_20261020"
        ]
        for standard_id in ("8.F.A.1", "8.F.B.4", "8.F.B.5")
    }


def test_dc_grade8_function_conditions_are_preserved() -> None:
    rows = _corrections()

    function_definition = " ".join(rows["8.F.A.1"]["requirements"].values()).lower()
    assert "exactly one output" in function_definition
    assert "function notation is not required in grade 8" in function_definition

    linear_model = " ".join(rows["8.F.B.4"]["requirements"].values()).lower()
    for term in (
        "description",
        "ordered-pair",
        "table",
        "graph",
        "rate of change",
        "initial value",
        "modeled situation",
    ):
        assert term in linear_model

    graph_features = " ".join(rows["8.F.B.5"]["requirements"].values()).lower()
    for term in (
        "increasing",
        "decreasing",
        "linear",
        "nonlinear",
        "described verbally",
    ):
        assert term in graph_features


def test_dc_grade8_function_corrections_remain_fail_closed() -> None:
    for correction in _corrections().values():
        assert correction["short_summary_exhaustive"] is False
        assert correction["independent_source_fidelity"] == "PENDING"
        assert correction["canonical_equivalence"] == "UNVERIFIED"
        assert correction["assessment"] == "UNVERIFIED"
        assert correction["mastery"] == "UNVERIFIED"
        assert correction["activation"] == "FORBIDDEN"
