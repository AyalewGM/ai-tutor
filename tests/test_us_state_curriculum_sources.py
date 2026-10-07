from app.us_state_curriculum_sources import (
    Grade9Structure,
    WAVE1_VERIFIED_SOURCES,
    source_for,
)


def test_wave1_registry_is_unique_and_grade_1_9_scoped():
    codes = [source.state_code for source in WAVE1_VERIFIED_SOURCES]
    assert len(codes) == len(set(codes))
    assert all(source.grades == tuple(range(1, 10)) for source in WAVE1_VERIFIED_SOURCES)
    assert all(source.lifecycle_status == "IMPLEMENTED" for source in WAVE1_VERIFIED_SOURCES)


def test_registry_preserves_high_school_structure_instead_of_inventing_grade9_equivalence():
    assert source_for("CA").grade9_structure is Grade9Structure.PATHWAY
    assert source_for("NY").grade9_structure is Grade9Structure.COURSE
    assert source_for("NJ").grade9_structure is Grade9Structure.COURSE
    assert source_for("VA").grade9_structure is Grade9Structure.COURSE


def test_unknown_state_fails_closed():
    assert source_for("TX") is None
    assert source_for("XX") is None


def test_authoritative_sources_are_state_agency_https_urls():
    for source in WAVE1_VERIFIED_SOURCES:
        assert source.source_uri.startswith("https://")
        assert any(
            host in source.source_uri
            for host in ("cde.ca.gov", "nysed.gov", "nj.gov", "doe.virginia.gov")
        )
