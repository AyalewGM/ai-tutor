"""Fail-closed, side-effect-free release eligibility for new question packages.

This Boolean preflight cannot authorize diagnostic, guided, independent, or
mastery. The runtime selector still requires explicit ProblemContentMetadata.
Content merges, draft declarations, and CI alone never grant mode authority.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PackageReleaseEvidence:
    """Release evidence bound to one exact immutable content revision."""

    package_sha: str
    math_accepted_sha: str | None = None
    pedagogy_accepted_sha: str | None = None
    backend_scoring_sha: str | None = None
    frontend_integration_sha: str | None = None
    muse_qa_sha: str | None = None
    engineering_authorized_sha: str | None = None
    canonical_mapping_approved: bool = False
    exact_scorer_verified: bool = False
    response_schema_verified: bool = False
    history_preservation_verified: bool = False
    runtime_activation_approved: bool = False


def release_preflight_passes(evidence: PackageReleaseEvidence) -> bool:
    """Check release evidence without granting any runtime mode permissions.

    The SHA checks are intentionally strict: an approval for a previous source
    revision cannot authorize a newly modified content package. Frontend,
    backend, Muse and Engineering integrations must also attest to this
    package revision; their own implementation commit identities belong in
    their review reports rather than replacing the content SHA.
    """

    sha = evidence.package_sha
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        return False
    reviewers = (
        evidence.math_accepted_sha,
        evidence.pedagogy_accepted_sha,
        evidence.backend_scoring_sha,
        evidence.frontend_integration_sha,
        evidence.muse_qa_sha,
        evidence.engineering_authorized_sha,
    )
    if not all(reviewed == sha for reviewed in reviewers):
        return False
    return all(
        (
            evidence.canonical_mapping_approved,
            evidence.exact_scorer_verified,
            evidence.response_schema_verified,
            evidence.history_preservation_verified,
            evidence.runtime_activation_approved,
        )
    )
