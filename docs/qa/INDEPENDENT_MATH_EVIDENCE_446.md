# Exact-SHA mathematical verification — Issue #446

This is a repeatable, read-only automated evidence runner for draft PRs **#489, #472 and #484**. It pins each current open draft PR's exact head SHA through GitHub's API, checks out that commit, runs the seeded mathematical test suite with independently reconstructed Fraction/SymPy oracles, and archives SHA-bound JUnit XML, test logs, and a JSON manifest even on test failure. A failed suite fails its matrix job, without losing artifacts. Runs require manual workflow dispatch after this workflow is merged.

The tests being run originate in the content PRs. Their independent mathematical *calculations* do not make them an independent **review**; a separate Mathematical Reviewer must inspect the artifact, test source and assumptions and independently derive additional edge cases. Reviewer issues exact-SHA ACCEPT/CHANGES_REQUIRED/PENDING only when actually substantiated. Retain previous scoped approvals; do not expand them to unreviewed families, answer types, standards or mastery gates.

The workflow has repository read-only token permissions. It does not read databases or learner records, seed, register generators, write PR comments, merge, activate or deploy. Evidence for a newer SHA never validates an older or later revision. Content readiness and runtime rollout remain independently gated.
