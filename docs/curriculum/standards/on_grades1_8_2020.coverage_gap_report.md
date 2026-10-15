# Ontario Mathematics Grades 1–8 (2020) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-14 ·
Manifest: `on_grades1_8_2020.expectations.v1.json`

## Scope

369 specific expectations across Grades 1–8, extracted programmatically from
the official DCP curriculum API (`ws.api.dcp.edu.gov.on.ca`), walking
course → strand → overall → specific for every grade. Six strands per grade:
A SEL/Mathematical Processes, B Number, C Algebra, D Data, E Spatial Sense,
F Financial Literacy.

| Grade | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Expectations | 38 | 39 | 46 | 48 | 51 | 51 | 52 | 44 |

## Findings

1. **Zero repository coverage.** No Ontario elementary packs or skills exist;
   all 369 expectations are `NO_REPOSITORY_CANDIDATE`. Ontario's only
   coverage is MTH1W Grade 9 (43 expectations, merged).
2. **Strand A has no numbered specific expectations** — the SEL /
   Mathematical Processes skills (problem solving, reflecting, connecting,
   representing, communicating, selecting tools) live in overall-expectation
   text and embed across strands B–F. Map them at the *overall* level or
   treat as cross-cutting dispositions, not as content skills.
3. **This replaces the prior 48-cell strand scaffold**
   (`on_grades1_8_2020.strand_acquisition.wave1.v1.json`) which contained
   zero verified expectation IDs — the scaffold's cell count is now
   superseded by real expectation rows.
4. **Ontario adds two strands the DMV doesn't have**: F Financial Literacy
   (money math by grade) and explicit C Algebra coding-pattern expectations —
   new canonical territory that the taxonomy likely can't express yet.

## Handoffs

| Owner | Action |
|---|---|
| Taxonomy | Audit whether `MATH.FIN.*`/`MATH.CODE.*` families exist for strands F and C-coding |
| Standards Mapping | Decide strand-A dedup policy (one canonical set vs per-grade) |
| Content | Authoring is fully greenfield; sequence B (Number) first — it underpins everything |

## Safety

`activation: FORBIDDEN` · zero canonical IDs · zero learner-evidence mutation.
