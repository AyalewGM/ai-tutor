# Maryland Grades 6–8 (2025) seed-skill reconciliation — Wave 1

**Status:** PROVISIONAL evidence only; not an accepted standards mapping, canonical taxonomy change, coverage claim, or production activation.

## Authoritative source

- Issuer: Maryland State Department of Education (MSDE)
- Framework: revised Maryland Comprehensive Curricular Framework for Mathematics
- Adopted: **July 29, 2025**
- Implementation: **school year 2026–2027**
- Landing page: https://msde.maryland.gov/academics-0/curriculum-academic-standards/mathematics
- Grade 6: [crosswalk](https://msde.maryland.gov/media/17816) · [companion](https://msde.maryland.gov/media/17817)
- Grade 7: [crosswalk](https://msde.maryland.gov/media/17818) · [companion](https://msde.maryland.gov/media/17819)
- Grade 8: [crosswalk](https://msde.maryland.gov/media/17820) · [companion](https://msde.maryland.gov/media/17821)

Source access was checked on 2026-10-09. The crosswalks, rather than historical Common Core placement, govern the expectation identifiers and grade placement below.

## Result

All **28** existing local Maryland Grades 6–8 seed scopes now have a source-linked reconciliation row:

| Grade | Local seed rows | Result |
|---|---:|---|
| 6 | 7 | All are provisional partial/composite relations; none accepted |
| 7 | 15 | Two local seeds straddle Grade 7 and Grade 8 expectations |
| 8 | 6 | Two local seeds are outside the current 2025 Grade 8 placement |
| **Total** | **28** | **0 accepted / 0 verified mappings** |

The machine-readable source of truth is `md_grades6_8_2025.seed_skill_reconciliation.v1.json`. It keeps source verification separate from canonical identity, mapping acceptance, generator availability, validated practice, assessment readiness, and verified mastery.

## Material placement findings

### 1. Grade 7 geometry is a cross-grade composite

`M7.G.GEO` currently combines circles, angle relationships, and triangle angle sums.

- Circle area/circumference remains current Grade 7 scope under **7.GR.B.3**.
- Unknown-angle work using complementary, supplementary, vertical, and adjacent relationships belongs under current **8.GR.A.1**.
- Triangle angle-sum/exterior-angle reasoning belongs under current **8.GR.A.3**.

Consequently, the local seed must not be treated as one Grade 7 equivalent mapping. Architecture must decide decomposition/identity; Content and independent Math Review must then review bounded scope cards.

### 2. Grade 7 probability also straddles grades

`M7.SP.PROB` combines Grade 7 probability-model concepts with compound events.

- Probability scale, long-run relative frequency, and probability-model comparison are **7.DS.C.4–7.DS.C.6**.
- Compound events and organized sample spaces are current **8.DS.C.6**.

A single equivalent Grade 7 mapping would overclaim the revised framework and risks double credit.

### 3. Two Grade 8 seeds are no longer current Grade 8 placements

The 2025 Grade 8 crosswalk moves the former transformation/congruence/similarity expectations:

- former **8.G.A.1** and **8.G.A.2** → Integrated Algebra I;
- former **8.G.A.3** → Integrated Algebra I and Integrated Algebra II;
- former **8.G.A.4** → Integrated Algebra II.

Therefore `M8.G.TRANS` and `M8.G.SIM` have no asserted current Grade 8 target in this manifest. They are preservation/placement questions, not deletion instructions. Any historical UUID, alias, student evidence, or mastery link must remain unchanged until Architecture approves an explicit migration/no-double-credit contract.

## Other gaps exposed by reconciliation

- **Grade 6 statistics:** local wording omits histogram, box-plot, IQR, distribution-shape, and context-linked summary evidence in 6.DS.A.3–A.4 and 6.DS.B.5–B.6.
- **Grade 6 geometry:** one broad seed spans 6.GR.A.1–A.4 but does not by title establish fractional-edge volume, coordinate polygons, nets, or pyramid surface area.
- **Grade 7 solids:** local scope does not by itself establish slices of 3D figures, spheres, or the full contextual measurement evidence in 7.GR.A.2 and 7.GR.B.4.
- **Grade 8 Pythagorean work:** local scope does not by itself establish reasoning/proof or acute/obtuse classification using inequalities in 8.GR.B.4.
- **Grade 8 radicals:** “simplify radicals” is extra local wording relative to the two directly reconciled number-system targets, 8.NOS.A.1–A.2, and needs placement review.

## Architecture disposition recorded

Architecture Issue #282 decision [6093222041](https://github.com/AyalewGM/ai-tutor/issues/282#issuecomment-6093222041) resolves the identity behavior while leaving every mapping provisional:

- Grade/course placement is mapping metadata, not canonical mathematical identity.
- `M7.G.GEO` and `M7.SP.PROB` are preserved cross-grade local composites, not canonical atoms or equivalence aliases. New bounded scope cards must separate their Grade 7 and Grade 8 evidence.
- `M8.G.TRANS` and `M8.G.SIM` are preserved legacy-placement identifiers with no current Maryland Grade 8 equivalence. Later Integrated Algebra I/II mappings must target independently reviewed, placement-neutral atoms.
- Historical identifiers, variants and learner evidence are immutable. There is no backfill, rekey, evidence copy, grade reassignment or retroactive reinterpretation.
- A legacy composite may be reported only through fail-closed `ALL_OF` over accepted atoms. It carries no canonical row, UUID, variant, attempt, mastery event or duplicate credit.

This narrows the authoring handoff but does not create canonical IDs, approve definitions or accept standards mappings.

## Independent review and refined identity consequences

At PR #326 r3 head `6e30bd5522ba299a73b39c1e8d493577a033a5b6`, Independent Mathematical Review approved the three corrected cards; together with the eight earlier approvals, all eleven cross-grade scope cards now have mathematical-scope approval. The reviewed r3 artifact blob is `9f4773c7e5964d8336b59d9ee2f76950bac7d280`, recorded on Issue #293 comment 6095975833. These are governance inputs, not accepted Maryland mappings.

- Circle circumference, circle area, triangle interior/exterior-angle reasoning, complementary angles, supplementary angles, vertical-angle equality, and adjacent-angle addition now have mathematically approved DRAFT scope cards. They remain unactivated and unmapped.
- The broad `MATH.GEO.ANGLE.RELATIONSHIPS` proposal remains rejected as a canonical atom. Current **8.GR.A.1** may ultimately map only to independently accepted component atoms or to the fail-closed reporting-only `ALL_OF`; that profile carries no UUID or mastery credit.
- Likelihood-scale and experimental-frequency cards now have mathematical-scope approval. The former is bounded to finite discrete models with positive-probability elementary outcomes for the probability-0/1 converses; the latter requires independent repeated trials under unchanged conditions with constant event probability.
- Expected count `n×p` remains a distinct competency and cannot be credited from successes/trials evidence.
- `MATH.PROB.COMPOUND.SAMPLE_SPACE` remains a mathematically approved DRAFT candidate relevant to **8.DS.C.6**. This does not accept the standards relation or establish assessment readiness.
- The official Grade 8 crosswalk independently establishes **8.DS.C.5** and **8.DS.C.6**. Their appearance as gap candidates does not mean `M8.SP.STAT` maps to them; that local row expressly does not establish the required two-way-table or compound-event evidence.
## Owner handoff

1. **Architecture (#282):** preserve the recorded cross-grade identity, reporting-only `ALL_OF`, historical-identifier, and no-double-credit decisions; resolve only genuinely new identity tradeoffs.
2. **Curriculum Content:** keep the mathematically approved cards DRAFT and close remaining source-grounded content gaps without claiming jurisdiction coverage.
3. **Independent Mathematical Review (#293):** re-review only if a mathematically material card revision is introduced.
4. **Standards Mapping:** obtain independent standards-mapping acceptance before converting any provisional relation.
5. **Muse QA / Assessment:** independently validate practice and assessment evidence; seeder or generator presence is not proof.

## Non-actions

This artifact does not modify production taxonomy, canonical aliases, student records, mastery evidence, generators, or assessments. It does not claim jurisdiction coverage or authorize implementation.
