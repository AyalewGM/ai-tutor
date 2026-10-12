# Maryland Grade 7 Unit 6 Algebra — DRAFT_UNVERIFIED

This package is the corrected owner-requested **Maryland Grade 7** content slice. It replaces the wrong-jurisdiction Ontario draft in closed PR #364.

## Why this scope

Maryland's July 2025 Grade 7 MCCRS, implemented in SY 2026–2027, places the core algebra sequence under:

- `7.AT.B.5` — operate on and expand/factor linear expressions with rational coefficients.
- `7.AT.B.6` — rewrite equivalent expressions to illuminate context.
- `7.AT.C.7` — decide whether an equation or inequality models a context and justify the choice.
- `7.AT.C.8` — write/solve contextual equations of Grade 7 forms with rational values, explain the process, and interpret the solution.
- `7.AT.C.9` — write/solve contextual inequalities, graph the solution set, and interpret possible/reasonable values.

MCPS Math 7 Unit 6 publicly organizes the learner experience around **representing and solving px+q=r and p(x+q)=r, inequalities, and equivalent expressions**. Mihur therefore treats these as one coherent teaching package rather than six disconnected drills.

## Reuse-first repository audit

Current main already contains `M7.EE.EXPR`, `M7.EE.EXPR.DIST`, `M7.EE.EXPR.COMBINE`, `M7.EE.EQUATION`, `M7.EE.EQUATION.ONE`, and `M7.EE.EQUATION.TWO` in `scripts/seed_grade7.py`. Existing standards reconciliation on main already identifies `7.AT.B.5/.6` and `7.AT.C.7/.8/.9` as provisional Maryland Grade 7 targets and explicitly warns that equation-vs-inequality choice, graphing, and contextual interpretation need separate evidence.

Accordingly, this PR creates **no new canonical ID**, changes no registry, and does not modify historical mappings. It adds a deep student-usable draft package around the existing Grade 7 scope.

## Mihur teaching design

The package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

and

**Concrete → Visual → Symbolic**

The learner first identifies whether a story describes an exact equality or a constraint/range. Equal-groups and fee/rate models then support translation into `px+q=r`, `p(x+q)=r`, and their inequality counterparts. Learners apply inverse operations to both sides, explain why transformations preserve the relationship, verify equations by substitution, and verify inequalities with a boundary test plus a satisfying witness and counterexample. Independent transfer does not supply the symbolic setup when modeling is the target.

## Misconception-specific repair

The package includes separate Socratic branches for:

- equation vs inequality context signals;
- fixed amount versus repeated coefficient;
- incorrect grouping in `p(x+q)`;
- partial distribution;
- inverse-operation sequencing;
- missing substitution checks;
- strict versus inclusive inequality endpoints;
- graph direction;
- missing contextual/domain interpretation.

Repairs use fresh examples and contrasting cases rather than generic hints.

## Deterministic practice and unseen transfer

`variants.py` creates six seeded structures:

1. model choice;
2. `px+q=r`;
3. `p(x+q)=r`;
4. `px+q <,≤,>,≥ r`;
5. `p(x+q) <,≤,>,≥ r`;
6. equivalent-expression reasoning.

Guided and independent modes have distinct RNG namespaces and disjoint solution bands. `public_payload()` intentionally excludes hidden parameters, answers, hints, canonical skill IDs, and mastery fields. `teacher_oracle()` is draft-only verification data and must never be projected to learners.

The guided classifier returns `GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED` even when structured fields match, because free-text reasoning has not been independently scored. Guided work is not mastery evidence.

## Accessibility / MVE handoff

Frontend/MVE should reuse existing balance and number-line interaction primitives only after confirming they support this exact Grade 7 contract. Requirements include:

- keyboard-equivalent manipulation for both sides;
- accessible equal-group/tape model for `p(x+q)`;
- screen-reader expression announcements;
- OPEN/CLOSED number-line endpoints and LEFT/RIGHT text equivalents;
- substitution table showing original left and right values;
- reduced-motion mode;
- no color-only state;
- mobile-sized controls;
- scaffold fading that changes the actual interface, not only prose.

No MVE is implemented by this PR.

## Provenance and rights

External evidence used for scope only:

- Maryland State Department of Education, Grade 7 MCCRS Mathematics Crosswalk, adopted July 2025, implementation SY 2026–2027: https://msde.maryland.gov/media/17818
- Montgomery County Public Schools, Math 7 Unit 6 public curriculum support: https://www.montgomeryschoolsmd.org/curriculum/math-support/middle/math7-unit6

All examples, scenarios, diagnostics, repair prompts, and generated variants in this package are original Mihur content. No teacher worksheet, copyrighted PDF content, or learner-identifying data is committed.

## Gate status

| Gate | Status |
| --- | --- |
| Authored learning package | YES |
| Draft deterministic generator | YES |
| Draft regression tests | YES |
| Production canonical registration | NO |
| Frontend/MVE wired | NO |
| Assessment backend wired | NO |
| Independent Mathematical Review | PENDING |
| Independent Pedagogical Review | PENDING |
| Standards Mapping acceptance | PENDING |
| Architecture review | PENDING |
| Muse QA | PENDING |
| Runtime activation | FALSE |
| Deployed / pilot-ready | NO |

Suggested focused command:

`pytest -q tests/test_maryland_grade7_unit6_algebra_v1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and browser accessibility/assessment-isolation tests before merge or activation.
