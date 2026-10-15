# Virginia Algebra 1 (2023 SOL) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-14 ·
Manifest: `va_algebra1_2023.expectations.v1.json`

## Scope

10 official VDOE 2023 Algebra 1 expectations (A.EO.1–4, A.EI.1–3, A.F.1–2,
A.ST.1), extracted from the archived Algebra 1 SOL document (`48985`; direct
VDOE fetch 403s). Note the strand scheme changes at high school: **EO/EI/F/ST**,
not the K–8 NS/CE/MG/PS/PFA scheme.

## Findings

1. **The seed covers 3 of 10 expectations — the linear/expression slice only.**
   `VAA1.EXPR` → A.EO.1, `VAA1.LINEAR.EQ` → A.EI.1, `VAA1.LINEAR.FN*` → A.F.1.
2. **Seven expectations have zero repository candidates:** polynomial
   operations/factoring (EO.2), laws of exponents (EO.3), radicals (EO.4),
   systems (EI.2), quadratics (EI.3), quadratic/exponential functions (F.2),
   and the data cycle (ST.1). The seed is a linear-functions course, not an
   Algebra 1 course.
3. **Every linked seed uses invented canonical codes.** `MATH.ALGEBRA1.*`
   codes are absent from the taxonomy catalog — see
   `seed_canonical_decomposition.v1` where all five are already flagged
   DECOMPOSE. The MD Algebra 1 seed additionally *generates* codes by string
   concatenation.
4. **Virginia mirrors Maryland's Algebra I situation** — both jurisdictions
   have seeds predating the reviewed-taxonomy requirement, and both need
   atomic decompositions before any EQUIVALENCES entry can be accepted.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Verify the 3 scope-derived links against official text |
| Math Review | Decompose `VAA1.*` alongside `DCA1.*`/`A1.*` as one algebra wave |
| Content | Author the 7 missing expectations (EO.2–4, EI.2–3, F.2, ST.1) |

## Safety

`activation: FORBIDDEN` · zero canonical IDs · zero learner-evidence mutation.
