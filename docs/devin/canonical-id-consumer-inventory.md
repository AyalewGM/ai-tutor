# Canonical-ID Consumer Inventory

**Issue:** [#286](https://github.com/AyalewGM/ai-tutor/issues/286)  
**Owner:** Devin (core tutor engine, learner-parent workflows)  
**Scope:** Identify every Devin-owned code path that reads or writes canonical mathematics IDs or problem-family metadata, and the invariants that must survive the Curriculum/Architecture namespace bridge in #282.

## Authority model

- **Application canonical skill registry** (`app.curriculum_models.CanonicalSkill`) is the authority.
- **Curriculum-local skills** (`app.models.Skill`) are jurisdiction/version-specific.
- **CurriculumSkillMapping** links a curriculum-local skill row to exactly one canonical skill.
- **Learner evidence** is **always** keyed to the curriculum-local `Skill.id`. It must never be re-keyed to a canonical ID, even when the bridge in #282 changes which canonical skill a pack alias resolves to.
- **ProblemFamily** and **AssessmentItem.family_code** are generation-family identifiers, not canonical skill identifiers. They are stable because they are bound to generator implementations, not to curriculum mappings.

## Write flows (Devin-owned or consumed by Devin paths)

| File / Function | Canonical / family ID written | Survives #282? | Notes |
|-----------------|------------------------------|----------------|-------|
| `app/canonical_problem_registry.py::register_problem_families` | `CanonicalSkill.code`, `ProblemFamily.code`, `ProblemFamily.canonical_skill_id` | Yes — authority | Curriculum-owned content registration; Devin paths read the result. |
| `app/canonical_problem_adapter.py::materialize_problem` | `Problem.solution["canonical_source_key"]`, `Problem.solution["canonical_skill_code"]`, `Problem.solution["family_code"]` | Must survive | Adapter from canonical generated content to legacy `Problem` rows. |
| `app/services/problem_generation.py::generate_problem` | `Problem.solution["problem_family"]` | Must survive | Legacy generator path uses different metadata key than the adapter above. |
| `app/services/learning_assessment.py::_generate_items` | `AssessmentItem.family_code`, `AssessmentItem.generation_seed` | Must survive | Reconstructs the exact problem for deterministic scoring. |
| `app/models.py` `StudentSkill`, `Attempt`, `MasteryEvent`, `TutorSession`, `LearningAssessment`, `SkillReviewSchedule`, `InterventionRecord` | curriculum-local `skill_id` | Yes — invariant | Evidence must remain bound to jurisdiction-local IDs. |

## Read flows (Devin-owned consumers)

| File / Function | Canonical / family ID read | Invariant |
|-----------------|-----------------------------|-----------|
| `app/services/learning_assessment.py::_families_for_skill`, `_select_assessment_families` | `canonical_skill_code` from `app/canonical_problem_families.FAMILIES` | Family selection must continue to match the canonical skill of the curriculum-local skill being assessed. |
| `app/services/problem_selection.py::_last_attempt_family` | `Problem.solution["problem_family"]` | Must correctly read the family key written by the generation path it targets. |
| `app/services/learning_assessment.py::record_item_response` | `AssessmentItem.family_code` + `AssessmentItem.generation_seed` | Reconstruction must be byte-for-byte identical to the generated item. |
| `app/services/learning_effectiveness.py::compute_effectiveness` | curriculum-local `skill_id` via `LearningAssessment.skill_id` | Effectiveness comparisons stay within one curriculum-local skill; cross-skill transfer is explicit and separate. |
| `app/services/mastery.py::update_mastery` | curriculum-local `skill_id` (from caller) | Mastery updates never query canonical IDs. |
| `app/parent_intelligence.py::classify_parent_skill_progress` | curriculum-local evidence counts | Parent insight is derived from evidence bound to curriculum-local skill rows. |
| `app/effectiveness_api.py`, `app/parent_api.py` | curriculum-local `skill_id` | APIs expose only jurisdiction-local skill references to parents. |

## Known risks

### Risk 1: Inconsistent problem-family metadata key

`app/services/problem_generation.py::generate_problem` stores `"problem_family"` in `Problem.solution`, while `app/canonical_problem_adapter.py::materialize_problem` stores `"family_code"`.

`app/services/problem_selection.py::_last_attempt_family` only reads `"problem_family"`. Canonical-generated problems therefore do not participate in same-family avoidance. This is a consumer-side bug in the adapter or in `_last_attempt_family`; it is not a Curriculum content issue.

**Mitigation for Deliverable A:** regression test asserts the expected key for each `source_type`. Do not silently patch without confirming ownership; the adapter is Devin-consumer territory but touches canonical-generated content.

### Risk 2: Historical evidence re-keying

If #282 introduces a new canonical mapping or reclassifies an existing one, any script that migrates `StudentSkill`, `Attempt`, `MasteryEvent`, `LearningAssessment`, or `TutorSession` rows from one `skill_id` to another would destroy the historical jurisdiction context and invalidate independent assessment evidence.

**Mitigation:** tests assert that `map_existing_skills` does not modify learner evidence rows and that evidence remains on the original curriculum-local `skill_id`.

### Risk 3: Independent-assessment isolation depends on curriculum-local skill

`has_active_assessment` and the centralized guard in `app/services/learning_assessment.py` use `LearningAssessment.skill_id` (curriculum-local). If an adapter ever switched to canonical skill IDs for active-assessment lookup, a student could start a second assessment on the same mathematical topic through a different jurisdiction.

**Mitigation:** tests assert the guard uses curriculum-local IDs.

### Risk 4: Cross-curriculum evidence leakage

`CurriculumSkillMapping` lets two curriculum-local skills share a canonical skill. Consumer code must never join `StudentSkill` on `canonical_skill_id`; doing so would make evidence from one jurisdiction visible to another.

**Mitigation:** tests create two curriculum-local skills mapped to the same canonical skill and verify that learner evidence on one does not appear on the other.

### Risk 5: Assessment item provenance drift

`AssessmentItem` stores `family_code` and `generation_seed`. If #282 renames pack aliases, these stored values must remain valid for deterministic reconstruction. The bridge must map the alias to the generator key, not rename stored assessment metadata.

**Mitigation:** tests assert that `record_item_response` can reconstruct an item from its stored `family_code` + `generation_seed` regardless of any alias label changes.

## Deliverable B integration points

After #282 publishes the approved mapping contract, the consumer-side adapter will live in Devin-owned code and must:

1. Accept a pack alias and resolve it to one or more application canonical skill IDs using the approved, versioned mapping.
2. For composite `ALL_OF` aliases, require evidence on **all** mandatory canonical skills before treating the alias as satisfied.
3. Map the resulting canonical skill IDs to curriculum-local `skill_id`s via `CurriculumSkillMapping`.
4. Fail closed when the alias is unmapped, ambiguous, or the curriculum has no matching local skill.
5. Preserve all historical evidence IDs and never re-key learner records.

Files expected to change in Deliverable B:
- `app/services/canonical_id_resolution.py` (new) — alias → canonical → curriculum-local resolution service
- `app/onboarding_api.py` — use resolution service for placement when alias input is required
- `app/adaptive_api.py`, `app/api.py`, `app/adaptive_response_api.py` — validate canonical skill references without breaking existing curriculum-local flows
