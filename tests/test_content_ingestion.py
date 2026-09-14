import pytest

from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    build_expectation_upserts,
    expectation_keys,
)
from app.content_validation import ContentValidationError


def _expectation(code: str = "8.EE.A.1") -> ExpectationInput:
    return ExpectationInput(
        source_identifier=code,
        title="Integer exponents",
        strand="Expressions and Equations",
        source_uri="https://example.edu/standards/8-ee-a-1",
    )


def test_build_expectation_upserts_has_stable_idempotency_key():
    pack = ContentPackInput(
        curriculum_code="MCPS-G8-MATH",
        curriculum_version="2026-27",
        expectations=(_expectation(),),
    )

    first = build_expectation_upserts(pack)
    second = build_expectation_upserts(pack)

    assert expectation_keys(first) == expectation_keys(second)
    assert expectation_keys(first) == (("MCPS-G8-MATH", "2026-27", "8.EE.A.1"),)


def test_duplicate_source_identifier_in_same_pack_is_rejected():
    pack = ContentPackInput(
        curriculum_code="MCPS-G8-MATH",
        curriculum_version="2026-27",
        expectations=(_expectation(), _expectation()),
    )

    with pytest.raises(ContentValidationError, match="Duplicate source identifier"):
        build_expectation_upserts(pack)


def test_same_expectation_like_code_isolated_by_curriculum_key():
    mcps = ContentPackInput("MCPS-G8-MATH", "2026-27", (_expectation("LINEAR-1"),))
    ontario = ContentPackInput("ON-MTH1W", "2021", (_expectation("LINEAR-1"),))

    assert expectation_keys(build_expectation_upserts(mcps)) != expectation_keys(
        build_expectation_upserts(ontario)
    )


def test_invalid_provenance_uri_is_rejected_before_persistence():
    pack = ContentPackInput(
        curriculum_code="ON-MTH1W",
        curriculum_version="2021",
        expectations=(
            ExpectationInput(
                source_identifier="C2.1",
                title="Algebra",
                source_uri="not-a-uri",
            ),
        ),
    )

    with pytest.raises(ContentValidationError, match="absolute HTTP"):
        build_expectation_upserts(pack)
