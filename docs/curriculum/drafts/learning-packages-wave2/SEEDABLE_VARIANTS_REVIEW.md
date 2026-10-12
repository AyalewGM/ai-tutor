# Mihur Wave 2 — deterministic learning variants (DRAFT_UNVERIFIED)

## Scope and ownership

Additive depth to the six **existing** Wave 2 learning packages in PR #328, not six new canonical skills. The seedable generator is in `seeded_variants.py`; independent exact-answer checks are in `tests/test_learning_packages_wave2_seeded.py`. This extends the 30 worked examples, 18 remediation pathways, 24 guided items and 18 assessment/transfer items already authored in `content.draft.json`. No runtime imports or activation.

| Package | Structure 0 | Structure 1 | Structure 2 (transfer) |
| --- | --- | --- | --- |
| Grades 1–2 unknown arithmetic | Unknown addend | Unknown subtrahend | Unknown starting quantity in a story |
| Grades 4–5 decimals | Hundredth comparison | Twentieth-to-hundredth conversion | Measured-length subtraction |
| Grades 6–7 ratios | Unit price | Equivalent ratio scaling | Compare two travel rates |
| Grades 6–8 distributions | Raw-data IQR | Five-number-summary IQR | Compare middle-half spread |
| Grades 6–8 cube nets | Surface area | Inverse surface area | Foldability of connected six-square net |
| Grade 9 quadratic patterns | Monic factorization | Both real square roots | Rectangle area expansion |

**18 bounded generative structures**; distinct seeds produce new numbers and scenarios. They do not establish 18 missing concepts, 18 accepted mappings, or a complete jurisdictional curriculum.

## Determinism, exactness and assessment boundaries

- `generate_item(package_id, seed, variant, mode)` accepts nonnegative integer seeds, variants 0–2, and modes `guided`/`independent`; unsupported inputs fail closed.
- RNG domain includes package, mode, variant and seed. Replaying identical inputs produces identical items; guided and independent modes are separated. This does not by itself prove items are pedagogically unseen across every possible seed.
- `student` contains the learner prompt. Guided mode includes three progressive hints and a concept-specific visual instruction; independent mode has neither. The `private` answer, parameter record and oracle kind must **never** be serialized to learners.
- Answers use integers, integer hundredths, or exact `fractions.Fraction` where needed, not floating-point rounding. The cube-net check propagates six 3D face orientations through 90-degree hinges and rejects repeated normals, disconnected shapes and inconsistent folds.
- Tests recompute each of 18 oracle kinds from parameters independently, exercise 8 seeds × 2 modes × 18 structures (288 generated cases), verify replay and hint isolation, validate cube-net rotation/reflection behavior, and reject invalid inputs. Test count in pytest is 25 parameterized test cases; case counts are not claims of approved assessments.

## Review gates and handoffs

- **Standards Mapping (PR #325):** exact Ontario/Maryland expectation IDs, grade placement and source versions remain `PROVISIONAL_NOT_ACCEPTED`; no accepted mapping or coverage credit is inferred from the generator.
- **Independent Mathematical Review (Issue #293):** review quartile median-of-halves convention, distinct roots vs principal square root, net folding proof, ratio units, and misconception targeting. This author does not self-approve.
- **Engineering Lead (Issue #278) / Architecture (Issue #282):** check duplication against #309/#315/#316/#317/#319/#327 and production generator families; never promote draft content to canonical identity.
- **MVE:** the visual prompts are specifications only. No frontend implementation or accessibility acceptance is claimed. Keyboard, spoken descriptions and reduced-motion alternatives remain to be independently verified.
- **Muse QA:** independently test server-only answer-key handling, assisted vs independent assessment separation, variant reproducibility, accessibility and any later integration. This PR does not edit Muse-owned E2E tests.

**Hard gates:** `status=DRAFT_UNVERIFIED`, `runtime_activation=false`, `mastery_writes=false`; no taxonomy edits, UUID changes, learner history writes, production deployment, merge or runtime activation. Exact-head CI/AppSec and independent review are required.
