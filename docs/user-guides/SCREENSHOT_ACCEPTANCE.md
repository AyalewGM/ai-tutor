# Mihur Help Center — Actual Screenshot Acceptance Checklist

**State:** PENDING independent Muse screenshot capture and accessibility review. Do not publish mockups or synthetic illustration art as actual product screenshots.

## Capture only the running Mihur interface

Use a disposable **synthetic** parent account and synthetic child profiles in an independently approved isolated localhost browser stack or restricted staging environment after DevOps authorization. The captured screen must correspond to the same exact commit being documented. No real child data, emails, invitation tokens, full bearer URLs, PINs, photographs, transcripts or protected school worksheets may appear.

Capture only after the script and page behavior have been independently verified:

| File to add later | Actual screen | Acceptance requirements |
| --- | --- | --- |
| `parent-registration.png` | Parent registration fields | Synthetic email redacted, country/state control, four-digit PIN obscured; no invitation token or error from production |
| `parent-learner-setup.png` | Practice → Add a learner | Alias only, actual accepted curriculum, no unsupported/topic-swap demonstration |
| `parent-private-links.png` | Settings & privacy → private links | Show per-child controls and status; **no raw private URL** visible |
| `student-home.png` | Direct learner Practice screen | Synthetic learner alias, ready skills; no sibling profile or parent-only controls |
| `student-guided-work.png` | Guided practice Workspace | Actual app state with a synthetic test problem; no hidden teacher oracle, no independent-assessment hints |
| `student-independent-check.png` | Independent practice or mastery check | Correct active mode and no hints; only after trusted backend/scoring and Muse acceptance |

## Review and publishing

1. Record the exact source commit, browser/OS/viewport, synthetic fixture, route and feature mode for each screen in a sidecar evidence note; keep sensitive test-run secrets out.
2. Muse verifies keyboard focus, screen-reader reading order, alt text and expected visual state. Product Owner approves wording. Security reviews images for identity/link leakage.
3. Downsample/compress images for small devices, add descriptive alt text, and link the accepted screenshots to the correct Markdown user guide. Re-run the generated Help Center parity and browser checks.
4. If staging or the target feature is not approved, leave the image **absent** and retain the honest screenshot-pending note. Do not silently substitute a design mockup or CI unit-test fixture for a real browser capture.

Coordinator: [Help Center Issue #468](https://github.com/AyalewGM/ai-tutor/issues/468), [Muse QA #439](https://github.com/AyalewGM/ai-tutor/issues/439), [Engineering #278](https://github.com/AyalewGM/ai-tutor/issues/278). Screenshots are non-blocking for draft code review but are a requested **pilot publishing gate** for the illustrated learner guide.
