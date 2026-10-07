from app.us_state_curriculum_sources import (
    WAVE1_VERIFIED_SOURCES,
    Grade9Structure,
    source_for,
)


def test_wave1_registry_is_unique_and_grade_1_9_scoped():
    codes = [source.state_code for source in WAVE1_VERIFIED_SOURCES]
    assert len(codes) == len(set(codes))
    assert all(source.grades == tuple(range(1, 10)) for source in WAVE1_VERIFIED_SOURCES)
    assert all(source.lifecycle_status == "IMPLEMENTED" for source in WAVE1_VERIFIED_SOURCES)


def test_registry_preserves_high_school_structure_instead_of_inventing_grade9_equivalence():
    assert source_for("CA").grade9_structure is Grade9Structure.PATHWAY
    assert source_for("TX").grade9_structure is Grade9Structure.COURSE
    assert source_for("FL").grade9_structure is Grade9Structure.COURSE
    assert source_for("NY").grade9_structure is Grade9Structure.COURSE
    assert source_for("NJ").grade9_structure is Grade9Structure.COURSE
    assert source_for("VA").grade9_structure is Grade9Structure.COURSE


def test_unknown_state_fails_closed():
    assert source_for("XX") is None


def test_authoritative_sources_are_state_agency_https_urls():
    approved_hosts = (
        "cde.ca.gov",
        "tea.texas.gov",
        "fldoe.org",
        "nysed.gov",
        "nj.gov",
        "doe.virginia.gov",
    )
    for source in WAVE1_VERIFIED_SOURCES:
        assert source.source_uri.startswith("https://")
        assert any(host in source.source_uri for host in approved_hosts)


def test_verified_sources_enrich_coverage_without_claiming_completion():
    from app.curriculum_coverage import (
        completed_cells,
        national_coverage_matrix,
        state_complete,
        with_verified_state_source,
    )

    wave1_codes = ("CA", "TX", "FL", "NY", "NJ", "VA")
    cells = national_coverage_matrix()
    for code in wave1_codes:
        cells = with_verified_state_source(cells, code)

    verified = [cell for cell in cells if cell.state_code in set(wave1_codes)]
    assert len(verified) == 54
    assert all(cell.source_verified for cell in verified)
    assert completed_cells(tuple(verified)) == 0
    assert all(not state_complete(cells, code) for code in wave1_codes)
