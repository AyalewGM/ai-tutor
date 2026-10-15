# California CCSS 2013 Grades 1–9 — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-14 ·
Manifest: `ca_ccss_2013_grades1_9.expectations.v1.json`

## Scope

255 expectations: 207 across grades 1–8 (canonical CCSS per-grade sets) + 48
in the Algebra I course (CCSS Appendix A traditional pathway, including CA's
absolute-value modification of A.CED.1). Statements cross-verified against the
official ADA-compliant CCSS document; the CDE PDF's inline footnote numbering
makes direct naive extraction unreliable.

## Findings

1. **Zero repository coverage** — no CA packs, seeds, or skills exist; all
   255 rows are `NO_REPOSITORY_CANDIDATE`.
2. **Cheap mapping opportunity.** CA codes are identical to CCSS codes, so
   every accepted DC CCSS `EQUIVALENCES` entry is a *candidate* CA crosswalk —
   a review decision that could map large blocks at once, not an automatic
   transfer.
3. **CA additions reconciliation is the known gap.** CA added a small number
   of state-specific K-8 standards (marked in the CDE PDF footnotes); the
   core set here is verified CCSS, and additions need a dedicated
   reconciliation pass before `official_expectation_count` can be called
   final.
4. **Supersedes the 173-row intake artifact** (`national_ca_grades7_9`) —
   that artifact listed IDs with null scope text; this manifest carries
   verified statements and also adds grades 1–6 and Algebra I that the
   intake only partially covered.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Reconcile CA additions against CDE footnotes; decide CCSS-code reuse policy |
| Math Review | Confirm CA-modified standards (A.CED.1 et al.) against canonical equivalents |
| Content | Greenfield except where CCSS-equivalent packs could transfer post-review |

## Safety

`activation: FORBIDDEN` · zero canonical IDs · zero learner-evidence mutation.
