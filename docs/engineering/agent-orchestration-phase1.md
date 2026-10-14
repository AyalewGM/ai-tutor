# Mihur Agent Orchestration — Phase 1 (routing only)

The GitHub Actions workflow observes PR lifecycle and CI/AppSec completion and posts an idempotent, exact-head handoff comment. It **does not run ChatGPT agents**, approve reviews, merge PRs, deploy, or activate drafts.

## Trust boundaries

- Runs the coordinator from the default branch, **never untrusted PR code**.
- Reads PR metadata, changed-file names, and checks via GitHub API.
- Only writes an issue/PR comment containing a SHA/state marker.
- On missing checks, routes to WAIT_CHECKS; on failed checks, AUTHOR_CORRECTION.
- Existing independent Math, Pedagogy, Standards, Assessment, Architecture, Muse, and Engineering approval gates remain unchanged.
- A changed head requires a new exact-SHA review; unaffected prior approvals may be preserved by reviewers.
- No taxonomy, learner history, attempt, mastery, variant, content activation or release mutations.
- A handoff comment is not proof that an agent has executed; Phase 2 requires authorized runners.

## Operations

Track work in #377 and #278. Review each automated handoff and route it to the named existing agent. No new content branch should be created when an existing PR can be corrected. Disable the workflow if it generates noisy comments; state/sha markers prevent repeats of the same handoff. No automatic merge.

## Limitations

PRs with >=100 files or >=100 comments fail closed rather than risk incomplete pagination or duplicate comments. Workflow-run events without linked PRs no-op. For multiple PRs linked to a workflow run, only the first is processed; a later PR event can still route each separately.
