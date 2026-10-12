# Alias resolution — consumer wiring design (#286 Deliverable B)

**Status:** Design note only. `app/alias_resolution.py` (PR #294) is an
isolated resolver; nothing here activates until mappings are REVIEWED
and an explicit Architecture/Product gate is authorized.

## Resolution boundary

`resolve_alias` answers one question: *which canonical skill IDs does a
pack alias map to?* It returns `RESOLVED` (full `ALL_OF` set + version +
evidence) or `UNRESOLVED` (explicit reason). It never picks one target
from a composite, never falls back, never mutates learner data.

Two joins then connect aliases to runtime behavior:

```
pack alias ──manifest──▶ canonical skill code(s) ──CurriculumSkillMapping──▶ local Skill row(s)
```

The second join already exists in `curriculum_models.py`. Deliverable B
only adds the first hop, read-only.

## Consumer touch points (once activated)

| Consumer | Use of resolution | Unresolved behavior |
|---|---|---|
| `services/problem_selection.py` | Discover eligible canonical families for a jurisdiction skill | Skill shows "no mapped content"; existing local-skill selection unchanged |
| `services/learning_assessment.py` | Nothing — assessments stay keyed to local `skill_id`; reconstruction uses persisted `family_code`+`seed` | Guard behavior unchanged |
| `services/mastery.py` | Nothing — mastery rows stay on local skill IDs | Unchanged |
| `services/learning_effectiveness.py` | Coverage evidence: a REVIEWED `ALL_OF` mapping requires evidence on **every** target | `UNRESOLVED` → not enough evidence, zero coverage credit |
| `services/parent_intelligence.py` | Display "mapped/not yet mapped" status on jurisdiction skills | Show not-assessed state, never imply coverage |
| Curriculum browsing APIs | Surface canonical mapping status per skill card | Show UNMAPPED/PROPOSED honestly |

## Invariants

1. **Activation gate:** consumers call the resolver only behind a flag
   that requires `release_status == REVIEWED_FOR_PUBLICATION` plus
   explicit enablement.
2. **ALL_OF semantics:** composite targets are treated as conjunctive —
   a skill is not "covered" until all targets have content/evidence.
3. **Version provenance:** consumers log `mapping_version` on any
   coverage/credit decision for auditability.
4. **Historical evidence:** no migration of `StudentSkill`, `Attempt`,
   `MasteryEvent`, `ProgressLog`, or assessment IDs. Alias revisions
   change resolution output, not persisted rows.
5. **Content-availability gate (board `6072732668`):** a canonical skill
   existing in the taxonomy ≠ it having generators. Resolution returns
   skill IDs; whether practice content exists is a separate check
   against `FAMILIES` — to be replaced by the redesigned taxonomy when
   Curriculum delivers it.
6. **Fail closed everywhere:** unknown alias, unreviewed mapping,
   malformed manifest → zero credit, no exception leaks to learners.

## Open dependencies

- #293 independent review of batch-1 proposals.
- Curriculum taxonomy redesign (skill existence ≠ generator availability).
- #283 reconciliation contract (eight-predicate coverage gate) before
  any coverage consumer reads resolution output.
