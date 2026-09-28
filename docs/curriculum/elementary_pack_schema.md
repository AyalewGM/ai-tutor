# Declarative elementary curriculum-pack framework

This framework is the F-024 ingestion boundary for DMV Grades 1–5 packs. It separates five concerns:

1. **Authority and curriculum identity** — exact jurisdiction, authority, curriculum code, version, grade, and official source.
2. **Curriculum-local skills** — the only skill IDs used by sessions, attempts, mastery, reviews, interventions, and awards.
3. **Canonical concepts** — reusable mathematical identity and generator/visual architecture; never a learner-evidence key.
4. **Problem-family eligibility** — an explicit allowlist per local skill, validated against application-owned generators.
5. **Authored problems and learning modes** — stable problem keys, deterministic answers/parameters, and non-overlapping diagnostic, guided, independent, and mastery pools.

## Usage

```bash
python scripts/load_elementary_pack.py path/to/pack.json
```

Parsing and all structural validation complete before database writes. Persistence runs in a nested transaction and is idempotent by exact authority/code/version, curriculum-local skill code, canonical code, expectation source identifier, prerequisite pair, and stable problem key.

## Launch-depth validation

Every skill must satisfy its declared readiness policy. The default requires:

- at least four curated problems;
- at least one problem in each deterministic mode;
- no problem reused across diagnostic, guided, independent, and mastery pools;
- at least one eligible problem family;
- every family registered in the application generator registry;
- every problem family allowed by its curriculum-local skill;
- every skill mapped to an expectation declared by the same pack;
- all prerequisites declared within the same pack;
- an acyclic prerequisite graph.

A pack that fails validation is not partially persisted.

## Evidence isolation

The loader does not import or reference `Student`, `StudentSkill`, `Attempt`, `MasteryEvent`, `TutorSession`, review schedules, interventions, or awards. It writes curriculum/content tables only. A canonical mapping cannot transfer mastery because learner evidence continues to use the exact curriculum-local `Skill.id`.

## Original-content requirement

The schema accepts only `origin: "AUTHORED"` for curated pack problems. Every problem stores authority, source, version, author, and license provenance. Commercial question-bank or assessment content must not be placed in a pack.

## Versioning and updates

`schema_version` is currently `1`. A changed official curriculum must receive an explicit curriculum version; loaders must not silently mutate a different authority/code/version identity. Stable `problem.key` values allow editorial updates without creating duplicate rows.

The Maryland Grade 3, DC Grade 3, and Virginia Grade 3 packs will be separate follow-up PRs built on this framework. Grades 1, 2, 4, and 5 remain blocked until those three Grade 3 packs prove cross-jurisdiction reuse and isolation.
