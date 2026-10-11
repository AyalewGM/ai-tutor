from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
PACKAGE_DIR = ROOT / "docs/curriculum/drafts/ontario-polynomial-division-package-r1"


def _load_module():
    path = PACKAGE_DIR / "learning_package.py"
    spec = importlib.util.spec_from_file_location("ontario_polynomial_division_package_r1", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


package = _load_module()


def _response(item):
    return copy.deepcopy(item.teacher_oracle["structured_response"])


def test_full_mihur_sequence_and_concrete_visual_symbolic_contract() -> None:
    item = package.generate(7, "guided")
    assert tuple(step["phase"] for step in item.flow) == package.PHASES
    manipulate = item.flow[2]
    assert manipulate["representation"] == "GROUPED_TERM_DIVISION_MVE_NOT_IMPLEMENTED"
    assert manipulate["keyboard_required"] is True
    assert manipulate["screen_reader_equivalent_required"] is True
    assert manipulate["reduced_motion_required"] is True
    assert item.flow[4]["mastery_credit"] is False
    assert item.flow[-1]["mastery_available"] is False


@pytest.mark.parametrize("seed", range(30))
def test_deterministic_replay_distinct_modes_and_exact_round_trip(seed: int) -> None:
    guided = package.generate(seed, "guided")
    replay = package.generate(seed, "guided")
    independent = package.generate(seed, "independent")
    assert guided == replay
    assert guided.variant_id != independent.variant_id
    assert guided.prompt != independent.prompt
    assert all(package.independent_reconstruction(guided))
    assert all(package.independent_reconstruction(independent))


@pytest.mark.parametrize("seed", range(20))
def test_oracle_is_independently_value_preserving(seed: int) -> None:
    item = package.generate(seed, "independent")
    divisor = item.teacher_oracle["divisor"]
    for quotient, dividend in zip(
        item.teacher_oracle["quotient_terms"],
        item.teacher_oracle["dividend_terms"],
        strict=True,
    ):
        for x, y in ((1, 2), (2, 3), (-2, 1)):
            if x == 0 or y == 0:
                continue
            reconstructed = package.exact_value(quotient, x=x, y=y) * package.exact_value(
                divisor, x=x, y=y
            )
            assert reconstructed == package.exact_value(dividend, x=x, y=y)


def test_independent_payload_has_no_answers_hints_or_guided_mve() -> None:
    item = package.generate(13, "independent")
    payload = item.public_payload()
    encoded = json.dumps(payload)
    assert "teacher_oracle" not in encoded
    assert 'domain_restrictions": [' not in encoded
    assert "parameters" not in encoded
    assert "flow" not in payload
    assert "transfer_prompt" not in payload
    assert payload["assessment_contract"] == {
        "hints": False,
        "worked_steps": False,
        "guided_mve": False,
        "practice_credit": False,
        "backend_trusted_scoring": "REQUIRED_NOT_WIRED",
    }
    assert payload["response_schema"] == [
        "terms",
        "domain_restrictions",
        "coefficient_reason",
        "exponent_reason",
        "reconstruction",
    ]
    assert payload["response_contract_revision"] == package.RESPONSE_CONTRACT_REVISION


def test_typed_response_oracle_is_exact_order_independent_and_not_partial_credit() -> None:
    item = package.generate(7, "guided")
    response = _response(item)
    assert package.evaluate_structured_response(response, item) is True
    response["terms"].reverse()
    response["reconstruction"].reverse()
    assert package.evaluate_structured_response(response, item) is True
    response["reconstruction"][0]["product_term"]["coefficient"] = "999"
    assert package.evaluate_structured_response(response, item) is False


def test_response_values_route_specific_misconceptions_without_truth_flags() -> None:
    polynomial = package.generate(7, "guided")
    correct = _response(polynomial)
    assert package.diagnose_response(correct, polynomial) == "NO_REMEDIATION"

    reciprocal = _response(polynomial)
    reciprocal["coefficient_reason"] = "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT"
    assert package.diagnose_response(reciprocal, polynomial) == "POLY.DIV.COEFFICIENT_RECIPROCAL"

    added = _response(polynomial)
    added["exponent_reason"] = "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT"
    assert package.diagnose_response(added, polynomial) == "POLY.DIV.ADD_EXPONENTS"

    one_term = _response(polynomial)
    one_term["terms"] = one_term["terms"][:1]
    one_term["reconstruction"] = one_term["reconstruction"][:1]
    assert package.diagnose_response(one_term, polynomial) == "POLY.DIV.ONE_TERM_ONLY"

    omitted_domain = _response(polynomial)
    omitted_domain["domain_restrictions"] = []
    assert package.diagnose_response(omitted_domain, polynomial) == "POLY.DIV.DOMAIN_OMITTED"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda response: response.update({"client_says_correct": True}),
        lambda response: response["terms"][0].update({"coefficient": "2/4"}),
        lambda response: response["terms"][0].update({"x_exponent": True}),
        lambda response: response.update({"domain_restrictions": ["y", "x"]}),
        lambda response: response["reconstruction"][0].update({"verified": True}),
    ],
)
def test_structured_response_rejects_untyped_noncanonical_or_client_truth_evidence(
    mutation,
) -> None:
    item = package.generate(7, "guided")
    response = _response(item)
    mutation(response)
    with pytest.raises(ValueError):
        package.normalize_structured_response(response)


@pytest.mark.parametrize("misconception_id", sorted(package.MISCONCEPTIONS))
def test_fresh_exit_is_deterministic_and_structurally_fresh(misconception_id: str) -> None:
    source = package.generate(4, "guided")
    exit_item = package.fresh_exit(4, "guided", misconception_id)
    assert exit_item == package.fresh_exit(4, "guided", misconception_id)
    assert exit_item.variant_id != source.variant_id
    if misconception_id == "POLY.DIV.ONE_TERM_ONLY":
        assert exit_item.structure == "POLYNOMIAL_BY_MONOMIAL"
    if misconception_id == "POLY.DIV.ADD_EXPONENTS":
        assert any(
            exponent < 0
            for term in exit_item.teacher_oracle["quotient_terms"]
            for _, exponent in term.powers
        )


def test_scaffold_fades_and_restores_from_diagnosed_evidence() -> None:
    state = package.advance_scaffold("MODELED", "EVIDENCE_CORRECT")
    assert state == "COACHED"
    state = package.advance_scaffold(state, "EVIDENCE_CORRECT")
    assert state == "INDEPENDENT_READINESS"
    assert package.advance_scaffold(state, "MISCONCEPTION_DIAGNOSED") == "COACHED"


@pytest.mark.parametrize("seed", range(20))
def test_unseen_composite_area_transfer_has_exact_changed_context(seed: int) -> None:
    item = package.generate(seed, "guided")
    parameters = item.transfer["parameters"]
    oracle = item.transfer["oracle"]
    height = parameters["common_height"]
    assert oracle["width_terms"] == oracle["total_width_terms"]
    assert len(oracle["width_terms"]) == len(oracle["multiplication_checks"]) == 2
    for check, area in zip(oracle["multiplication_checks"], parameters["area_terms"], strict=True):
        quotient = package._parse_term_record(check["quotient_term"])
        divisor = package._parse_term_record(check["divisor_term"])
        product = package._parse_term_record(check["product_term"])
        assert quotient[0] * divisor[0] == product[0]
        assert quotient[1] + divisor[1] == product[1]
        assert quotient[2] + divisor[2] == product[2]
        assert check["product_term"] == package._term_record(area)
        assert check["divisor_term"] == package._term_record(height)
    assert "composite display" in item.transfer["prompt"]
    assert oracle["units"] == {"width": "units", "area": "square units"}


@pytest.mark.parametrize(
    ("seed", "mode", "error"),
    [
        (True, "guided", TypeError),
        (1.5, "guided", TypeError),
        (-1, "guided", ValueError),
        (1, "mastery", ValueError),
    ],
)
def test_invalid_generation_values_fail_closed(seed, mode, error) -> None:
    with pytest.raises(error):
        package.generate(seed, mode)


def test_machine_readable_provenance_and_runtime_gate() -> None:
    provenance = json.loads((PACKAGE_DIR / "provenance.json").read_text())
    contract = json.loads((PACKAGE_DIR / "package_contract.json").read_text())
    response_contract = json.loads((PACKAGE_DIR / "response_contract.json").read_text())
    assert provenance["package_id"] == package.PACKAGE_ID
    assert provenance["runtime_activation"] is False
    assert provenance["standards"]["exact_expectation_ids"] == []
    assert provenance["standards"]["mapping_approval"] == "NONE"
    assert provenance["independent_reviews"]["mathematical"].startswith("REQUEST_CHANGES_AT_")
    assert provenance["independent_reviews"]["muse_qa"] == "UNKNOWN_NOT_RUN"
    assert contract["phases"] == list(package.PHASES)
    assert contract["response_contract"]["revision"] == package.RESPONSE_CONTRACT_REVISION
    assert contract["manipulation_contract"]["implemented"] is False
    assert contract["assessment_isolation"]["practice_credit"] is False
    assert response_contract["runtime_activation"] is False
    assert response_contract["scoring_authority"] == "BACKEND_REQUIRED_NOT_WIRED"
    assert response_contract["reconstruction_record"]["client_truth_flags_allowed"] is False
    assert (
        response_contract["assessment_isolation"]["partial_field_credit_can_award_mastery"] is False
    )
