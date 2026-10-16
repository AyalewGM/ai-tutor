"""WA source-provenance parity checks; these are not publisher authentication."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_wa_uploaded_workbook_hash_consistent_across_author_artifacts():
    source = json.loads((BASE / "wa_2026_v3_1_source_extraction.json").read_text())
    blocker = json.loads((BASE / "national_wa_2026_grades7_9.source_blocker.v1.json").read_text())
    anomalies = json.loads((BASE / "wa_2026_v3_1_workbook_anomalies.v1.json").read_text())
    audit = json.loads((BASE / "wa_2026_v3_1_course_scope_cell_audit.v1.json").read_text())
    matrix = json.loads((BASE / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["WA"]
    digest = source["source"]["sha256"]
    assert len(digest) == 64
    assert digest == blocker["uploaded_final_adoption_workbook"]["sha256"]
    assert digest == anomalies["workbook_sha256"]
    assert digest == audit["source_sha256"]
    assert digest == matrix["uploaded_workbook_source_extraction"]["sha256"]
    assert digest == blocker["source_acquisition"]["expected_uploaded_workbook_sha256"]
    assert source["source"]["publisher_byte_match"] == "NOT_INDEPENDENTLY_VERIFIED"
    assert blocker["source_acquisition"]["publisher_hash_independently_verified"] is False
    assert blocker["source_acquisition"]["direct_final_workbook_url_status"] == "UNRESOLVED_OFFICIAL_OSPI_FILE_LINK"
    assert matrix["verified_2026_expectation_rows"] == 0
    assert source["acceptance"]["activation"] == "FORBIDDEN"


def test_wa_original_source_anomalies_not_silently_rewritten():
    source = json.loads((BASE / "wa_2026_v3_1_workbook_anomalies.v1.json").read_text())
    by_code = {a["code"]: a for a in source["anomalies"]}
    assert by_code["M.HS.Q.NVM.5"]["cell"] == "E376"
    assert by_code["M.HS.DA.SCP.3"]["cells"] == ["E65", "E169", "E331"]
    assert "P(B)>0" in by_code["M.HS.DA.SCP.3"]["mathematical_interpretation_unapproved"]
    assert source["source_fidelity"] == "PENDING_INDEPENDENT_REVIEW"
    assert source["curriculum_activation"] == "FORBIDDEN"
