---
name: Post-Merge Quality Audit Defect
about: Report a reproducible, evidence-backed defect on the merged Mihur main branch (never post secrets, child data or exploit details).
title: "[AUDIT][UNVERIFIED] "
assignees: []
---

> For potential active compromise, real child-data disclosure or sensitive exploit instructions, **do not post exploit details publicly**. Escalate through an appropriate restricted security channel first.

**Audit coordination:** #433

### Triage

- **Audit lane:** Engineering / AppSec / Math / Pedagogy / Muse QA / Standards / DevOps
- **State:** UNVERIFIED / CONFIRMED / FIX_IN_PROGRESS / AWAITING_INDEPENDENT_REVIEW / CLOSED_VERIFIED
- **Provisional severity:** P0 / P1 / P2 / P3 — supporting impact reasoning:
- **Exact merged main SHA:** 
- **UTC audit date and reviewer:** 
- **Prior finding or review links (deduplicate first):**

### Actual versus expected behavior

- **Scope:** file:function, endpoint, UI flow, math package/seed, standard ID or migration
- **Preconditions (synthetic only):**
- **Expected:**
- **Observed:**
- **Who/what is affected:** learner/parent/session/mastery/accessibility/source-fidelity

### Reproducible evidence

- **Source inspection or executed test?** (distinguish explicitly)
- **Environment and isolated/synthetic guarantee:**
- **Minimal steps and exact test command:**
- **Counts:** passed / failed / skipped / xfailed
- **Log or artifact link:** (sanitize; no real tokens, passwords, personal records)
- **Deterministic seed / input identity if applicable:**
- **Limitations and unverified assumptions:**

### Ownership and remediation

- **Fix owner (not the independent approver):**
- **Smallest bounded correction and regression tests required:**
- **Affected release/pilot:** HOLD / unaffected / pending assessment
- **Preservation checks:** unchanged UUIDs, Attempt, DiagnosticAttempt, MasteryEvent, history, variant evidence, independent-scoring isolation and provisional taxonomy/standards guards

### Independent gates and closure

- [ ] Exact-head CI and AppSec, as applicable
- [ ] Scoped Engineering/Architecture review
- [ ] Independent Mathematical review if mathematical contracts affected
- [ ] Independent Pedagogy if learner teaching behavior affected
- [ ] Independent Standards source-fidelity if mapping affected
- [ ] Independent Muse browser/accessibility QA if interactions affected
- [ ] Privacy/legal and DevOps where applicable
- [ ] Fix PR URL, merge SHA and post-merge main reproduction now passing
- [ ] Verified by independent reviewer on exact corrected SHA
- [ ] Linked back to coordination issue #433 and control board #278

**No issue status, GitHub check or PR merge alone grants permission to enroll children or deploy.**
