"""Deterministic tests for the isolated alias resolver (#286 B groundwork).

These tests prove the resolver is fail-closed by default: only
independently REVIEWED mappings resolve, composites keep their full
ALL_OF target set, and nothing — including the real merged manifest —
grants coverage credit to unreviewed aliases.
"""
from __future__ import annotations

import json

import pytest

from app.alias_resolution import (
    AliasManifestError,
    ResolutionStatus,
    load_manifest,
    resolve_alias,
)


def _manifest(entries, path, version="test-v1", tmp_name="manifest.json"):
    file = path / tmp_name
    file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mapping_version": version,
                "authority": "test",
                "release_status": "DRAFT_NOT_FOR_RUNTIME",
                "aliases": entries,
            }
        )
    )
    return load_manifest(file)


def _entry(
    alias="MATH.ELEMENTARY.TEST",
    status="UNMAPPED",
    relation=None,
    targets=None,
    evidence=None,
    reviewed_by=None,
):
    return {
        "alias": alias,
        "status": status,
        "relation": relation,
        "target_skill_codes": [] if targets is None else targets,
        "evidence": [] if evidence is None else evidence,
        "reviewed_by": reviewed_by,
    }


class TestManifestLoading:
    def test_duplicate_alias_fails_closed(self, tmp_path):
        with pytest.raises(AliasManifestError, match="duplicate alias"):
            _manifest([_entry(), _entry()], tmp_path)

    def test_wrong_schema_version_fails_closed(self, tmp_path):
        file = tmp_path / "m.json"
        file.write_text(
            json.dumps({"schema_version": 99, "mapping_version": "x", "aliases": []})
        )
        with pytest.raises(AliasManifestError, match="schema_version"):
            load_manifest(file)

    def test_reviewed_without_reviewer_fails_closed(self, tmp_path):
        bad = _entry(
            status="REVIEWED",
            relation="ALL_OF",
            targets=["MATH.NS.ADDITION"],
            evidence=["e"],
            reviewed_by=None,
        )
        with pytest.raises(AliasManifestError, match="requires reviewer"):
            _manifest([bad], tmp_path)

    def test_reviewed_without_all_of_fails_closed(self, tmp_path):
        bad = _entry(
            status="REVIEWED",
            relation=None,
            targets=["MATH.NS.ADDITION"],
            evidence=["e"],
            reviewed_by="curriculum-reviewer",
        )
        with pytest.raises(AliasManifestError, match="ALL_OF"):
            _manifest([bad], tmp_path)


class TestFailClosedResolution:
    def test_unknown_alias_is_unresolved(self, tmp_path):
        m = _manifest([_entry()], tmp_path)
        r = resolve_alias(m, "MATH.ELEMENTARY.DOES_NOT_EXIST")
        assert r.status == ResolutionStatus.UNRESOLVED
        assert "unknown alias" in r.reason
        assert r.target_skill_codes == ()

    def test_unmapped_alias_is_unresolved(self, tmp_path):
        m = _manifest([_entry(status="UNMAPPED")], tmp_path)
        r = resolve_alias(m, "MATH.ELEMENTARY.TEST")
        assert r.status == ResolutionStatus.UNRESOLVED
        assert "UNMAPPED" in r.reason

    def test_proposed_alias_is_unresolved_pending_review(self, tmp_path):
        e = _entry(
            status="PROPOSED",
            relation="ALL_OF",
            targets=["MATH.NS.ADDITION"],
            evidence=["proposal"],
        )
        m = _manifest([e], tmp_path)
        r = resolve_alias(m, "MATH.ELEMENTARY.TEST")
        assert r.status == ResolutionStatus.UNRESOLVED
        assert "PROPOSED" in r.reason


class TestReviewedResolution:
    def test_reviewed_all_of_returns_complete_target_set(self, tmp_path):
        e = _entry(
            status="REVIEWED",
            relation="ALL_OF",
            targets=["MATH.NS.ADDITION", "MATH.NS.SUBTRACTION"],
            evidence=["1.OA review"],
            reviewed_by="curriculum-reviewer",
        )
        m = _manifest([e], tmp_path, version="v-reviewed")
        r = resolve_alias(m, "MATH.ELEMENTARY.TEST")
        assert r.status == ResolutionStatus.RESOLVED
        assert r.relation == "ALL_OF"
        assert set(r.target_skill_codes) == {
            "MATH.NS.ADDITION",
            "MATH.NS.SUBTRACTION",
        }
        assert len(r.target_skill_codes) == 2  # composite never reduced
        assert r.mapping_version == "v-reviewed"
        assert r.evidence == ("1.OA review",)

    def test_resolution_is_deterministic(self, tmp_path):
        e = _entry(
            status="REVIEWED",
            relation="ALL_OF",
            targets=["MATH.NS.ADDITION", "MATH.NS.SUBTRACTION"],
            evidence=["e"],
            reviewed_by="rev",
        )
        m = _manifest([e], tmp_path)
        assert resolve_alias(m, "MATH.ELEMENTARY.TEST") == resolve_alias(
            m, "MATH.ELEMENTARY.TEST"
        )


class TestMergedManifest:
    """The real manifest currently on main: 4 PROPOSED, 38 UNMAPPED,
    zero REVIEWED — so every alias must resolve UNRESOLVED."""

    def test_every_real_alias_is_unresolved(self):
        manifest = load_manifest()
        assert len(manifest.entries) == 42
        for alias in manifest.entries:
            r = resolve_alias(manifest, alias)
            assert r.status == ResolutionStatus.UNRESOLVED, alias
            assert r.target_skill_codes == ()

    def test_resolution_grants_no_targets_for_proposed_entries(self):
        manifest = load_manifest()
        proposed = [
            a
            for a, e in manifest.entries.items()
            if e["status"] == "PROPOSED"
        ]
        assert len(proposed) == 4  # batch-1 proposals are pending review
        for alias in proposed:
            assert (
                resolve_alias(manifest, alias).status
                == ResolutionStatus.UNRESOLVED
            )
