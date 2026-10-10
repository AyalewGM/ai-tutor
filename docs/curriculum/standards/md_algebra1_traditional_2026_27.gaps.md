# Maryland traditional Algebra I (2026–27): official standards inventory and readiness gaps

**Status:** DRAFT_PROPOSED_NOT_VERIFIED. No mapping or coverage accepted.  
**Manifest:** `docs/curriculum/standards/md_algebra1_traditional_2026_27.expectations.v1.json`  
**Source checked:** 2026-10-09

## Authority and version boundaries

- MSDE [Algebra I standards](https://msde.maryland.gov/media/17798), seven pages, marked **August 2022**.
- MSDE [Algebra I Mathematics Evidence Statements](https://msde.maryland.gov/media/17801), marked **August 2024**. This document contains additional assessment-item specifications, reasoning/modeling evidence and calculator restrictions that cannot be inferred from standards identifiers alone.
- [MSDE mathematics index](https://msde.maryland.gov/academics-0/curriculum-academic-standards/mathematics) explicitly lists this traditional Algebra I pathway for **SY 2026–2027**. It separately lists a future **Integrated Algebra 1** pathway. Do not conflate the two.

## Inventory: 40 top-level standards

| Conceptual category | Top-level standards | Accepted mappings | Exact-target generator / validated practice / assessment / mastery |
|---|---:|---:|---|
| Number and Quantity | 4 | 0 | Not independently verified |
| Algebra | 17 | 0 | Not independently verified |
| Functions | 15 | 0 | Not independently verified |
| Statistics | 4 | 0 | Not independently verified |
| **Total** | **40** | **0** | **No readiness or mastery credit** |

The manifest records each official top-level identifier, source page, and short **editorial paraphrase**. These are draft extraction records, not verified coverage. The lettered subparts (e.g., A.REI.B.4a/b and F.IF.C.7a/b) are *not* counted as independent top-level standards. They must be decomposed and source-checked before any completeness or mastery assertion.

## Reconciliation with existing Mihur content

The previous Maryland Integrated Algebra I audit (draft PR #322) found **15 curriculum-local skills** in `MD_ALGEBRA_1_2026_27`, but no official expectation-level identifier assignments in that traditional seed. The 40 official standard IDs here must **not** be matched to those 15 labels by string similarity or course-title similarity.

Existing `MATH.ALGEBRA1.*` codes are not independently reviewed canonical identities. This PR creates **zero new canonical skill IDs**, zero crosswalk mappings, and zero evidence/migration changes.

## Priority gaps and independent review needs

1. **Standards fidelity:** Independently check all 40 identifiers, their page locators, and the short paraphrases against the official August 2022 PDF; inspect lettered subparts.
2. **Assessment evidence:** Cross-reference the August 2024 MSDE evidence statements for assessment-specific restrictions, including content vs reasoning vs modeling evidence, calculators, and instructional-only standards.
3. **Atomic decomposition:** Composite standards such as `A.SSE.B.3`, `A.REI.B.4`, `F.IF.C.7`, `F.LE.A.1`, and `S.ID.B.6` require more than a single procedural generator.
4. **Taxonomy gate:** Issue #282 / draft PR #308 governs independent canonical identities; mathematical review #293 and Architecture must accept exact skill scope before proposed mappings can advance.
5. **Implementation isolation:** Do not attach these draft standards to learner mastery, course aliases, existing UUIDs, or production coverage.
6. **Separate Maryland course identities:** Traditional `MD_ALGEBRA_1_2026_27` and Integrated `MD_INTEGRATED_ALGEBRA_1_2027_28` have distinct official source documents and implementation years.

## Next bounded review batch

Reconcile the 15 existing traditional-course local skills against the 40 standards with a **proposed-only** source-linked relation matrix. Every relation must declare partial/equivalent/unknown and include mathematical rationale; do not claim `EQUIVALENT` by name matching. Request Architecture approval of composite and overlap semantics before promoting any relation. Standards reviewers must independently confirm official source fidelity.

**No canonical IDs, production mappings, mastery records, or curriculum-coverage claims are activated by this inventory.**

## Source-located lettered requirements (second review layer)

The official seven-page August 2022 Algebra I standards PDF explicitly contains **17 lettered requirements across 8 parent standards**. They are inventoried in `md_algebra1_2026_27.lettered_subparts.v1.json`:

| Parent standard | Distinct published subparts | Review implication |
|---|---|---|
| `A.SSE.A.1` | a, b | Parts of expressions versus composite-entity interpretation |
| `A.SSE.B.3` | a, b, c | Quadratic factor, quadratic vertex, exponential rewrite |
| `A.REI.B.4` | a, b | Derivation versus solving quadratics and complex roots |
| `F.IF.C.7` | a, b | Linear/quadratic versus radical/piecewise graphs |
| `F.IF.C.8` | a | Contextual quadratic equivalent forms |
| `F.BF.A.1` | a | Explicit/recursive function construction |
| `F.LE.A.1` | a, b, c | Differences/factors, additive rate, percent change |
| `S.ID.B.6` | a, b, c | Fit, residuals, linear regression |

**Important:** Subpart IDs are source-indexing keys, not new canonical IDs. A correct answer to one subpart cannot automatically satisfy the parent standard. Architecture must decide exact atomic and `ALL_OF` semantics; independent mathematical review must validate scopes. This manifest grants no generator, assessment, coverage or learner mastery credit.

Source-locator correction: `A.REI.D.12` starts on official **page 4**, not page 3. The `N.Q.A.2` editorial summary now retains the official measurement-accuracy requirement. Both corrections are source fidelity only.

## Actual seed-to-official-standard reconciliation (third review layer)

I inspected the actual repository seed `scripts/seed_algebra1.py` (not just course metadata) and found **15 curriculum-local skills**: three broad anchors (`A1.EXPR`, `A1.LINEAR.EQ`, `A1.LINEAR.FN`) and 12 narrower skills for distribution, combining like terms, equation solving, linear functions, quadratics, polynomials, systems, exponentials, inequalities, and sequences.

A new versioned [read-only reconciliation manifest](md_algebra1_2026_27.seed_skill_reconciliation.v1.json) records **25 provisional relations** from those 15 local skills to **17 of the 40** official parent standards. The remaining **23** parent standards have no candidate relation in this first seed-focused pass. A relation means a potential mathematical topic overlap, **not verified mapping, partial coverage, or mastery**. One relation (`A1.LINEAR.INEQ` → `A.CED.A.1`) is specifically `UNCONFIRMED_RELATED` because solving inequalities does not imply constructing them from context.

| Existing seed group | Illustrative official candidates | Why no full coverage is claimed |
|---|---|---|
| Expressions, distribution, like terms | `A.SSE.A.1`, `A.SSE.A.2` | Interpretation and structure subskills are not interchangeable |
| One/two/multi-step equations | `A.REI.A.1`, `A.REI.B.3` | Justification and inequalities need separate evidence |
| Slope/intercept and function evaluation | `F.IF.A.2`, `F.IF.B.6`, `F.LE.A.2` | Contextual interpretation and exponential modeling not established |
| Quadratic and polynomial functions | `F.IF.C.7`, `F.IF.C.8`, `A.APR.B.3` | Multi-family graphing, equivalent forms, and zeros need separate evidence |
| Systems, exponential functions, inequalities, sequences | `A.REI.C.6`, `F.LE.A.1`, `A.REI.B.3`, `F.IF.A.3` | Composite requirements and modeling constraints remain untested |

**Additional architecture risk found in existing seed infrastructure:** the historical state-authority seeder derives `MATH.ALGEBRA1.*` canonical-looking codes from local `A1.*` codes and creates `EQUIVALENT` relations (see `scripts/seed_md_algebra1.py` from the F-019 implementation). This predates independent atomic identity review. The new manifest records those codes as legacy-looking references, **not approved canonical identities**. This PR deliberately does not change the seeder, existing database relations, student UUIDs, or historical mastery.

### Next handoff

- **Architecture #282:** determine whether each existing broad anchor is composite and whether the 25 candidate relations are partial, unknown, or invalid; define required `ALL_OF` sub-evidence where relevant.
- **Mathematical Review #293:** independently check exact local skill scopes, official standards requirements, and any proposed atomic decompositions.
- **Standards Mapping reviewer:** verify source fidelity, 40 parent IDs, 17 lettered subparts, and the 25 candidate rationales. No `EQUIVALENT` claim has been made by this mapping agent.
- **Muse QA (after acceptance):** inspect actual generators, curated practice, assessment contracts, and historical evidence isolation; a curated item in the seed is not proof of generator availability.
