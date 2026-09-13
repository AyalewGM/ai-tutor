# ADR-006: Curriculum Authority, Versioning, and Jurisdiction Isolation

Status: Accepted for F-006 implementation
Date: 2026-09-13
Issue: #11

## Context

The current data model stores `Curriculum.jurisdiction` as free text and assigns a curriculum directly to `Student`. That was sufficient for a single MCPS Grade 8 seed, but it cannot safely represent Ontario provincial curriculum ownership, Maryland county-board curriculum authority, U.S. state/local instructional-material roles, effective-date changes, or multiple curricula with overlapping skill codes.

Product Owner research across all 50 U.S. states + DC established that standards authority, curriculum authority, material review authority, material selection authority, and enforcement authority are distinct roles. They can vary by jurisdiction, subject, grade, and effective date. Ontario is different again: Ontario Ministry of Education owns/publishes MTH1W while OCDSB is implementation context rather than curriculum owner.

The application must therefore model authority and provenance explicitly rather than deriving curriculum ownership from geography or a state-level boolean.

## Decision

### 1. Separate geography from education authority

Use a hierarchical `jurisdictions` registry:
- COUNTRY
- STATE_PROVINCE_TERRITORY
- LOCAL_EDUCATION_AREA
- SCHOOL (optional)

A jurisdiction has an optional parent jurisdiction. Geography does not imply curriculum ownership.

Use `education_authorities` for organizations that exercise an education role, such as:
- MINISTRY
- STATE_AGENCY
- COUNTY_BOARD
- DISTRICT
- SCHOOL_BOARD
- SCHOOL

An authority belongs to a jurisdiction and records provenance/effective dates.

### 2. Curriculum has an explicit publishing/owning authority and version

`curricula` gains:
- `authority_id`
- `version`
- `effective_from`
- `effective_to`
- source/provenance metadata

Curriculum identity is scoped by authority + code + version/effective period rather than geography alone.

Legacy free-text `jurisdiction` and direct `Student.curriculum_id` remain temporarily during migration compatibility; new code treats enrollment as authoritative when present.

### 3. Model authority roles as data, not state-specific code branches

`authority_roles` records which authority performs a role for an applicability scope:
- STANDARDS
- CURRICULUM
- MATERIAL_REVIEW
- MATERIAL_SELECTION
- ASSESSMENT_ACCOUNTABILITY
- ENFORCEMENT

Each role may carry subject/grade scope, effective dates, and provenance. This supports a state changing policy over time without schema replacement and avoids a single misleading `state_adoption` flag.

These records are governance/provenance data. They do not directly alter tutoring behavior unless an accepted curriculum ingestion/enrollment references them.

### 4. Preserve local implementation separately

`local_implementation_overlays` references a curriculum and a local authority. It is versioned and provenance-backed. It cannot mutate the source curriculum definition.

For Ontario MTH1W, Ontario Ministry is curriculum authority; OCDSB may be local context/overlay.
For Maryland/MCPS, the authority relationship may legitimately make MCPS/county board the curriculum authority for a local curriculum aligned to Maryland standards.

### 5. Make student enrollment explicit and historical

`student_curriculum_enrollments` records:
- student
- curriculum/version
- optional local authority context
- active/effective period
- provenance

Only one active enrollment is allowed per student in F-006. Historical enrollments remain immutable enough to interpret past evidence.

Tutor sessions will snapshot the curriculum enrollment/curriculum used for the session so later curriculum changes cannot reinterpret historical attempts.

### 6. Curriculum-scope all learning graph lookup

Skills are curriculum-scoped. Skill codes must be unique within a curriculum rather than globally.

All of the following must resolve inside the session/student curriculum scope:
- target/active skill
- prerequisite traversal
- problems
- misconceptions
- diagnostics
- mastery evidence
- dashboard reads

No automatic cross-curriculum skill mapping is permitted. A future equivalency layer, if added, must be explicit and non-mutating.

### 7. Fail closed on cross-curriculum references

Application services must reject a session or request when:
- selected skill does not belong to the student's active curriculum;
- a prerequisite edge crosses curricula;
- a problem resolves to a skill outside the session curriculum;
- diagnostic/mastery evidence is submitted against a foreign curriculum scope.

LLMs receive only already-resolved curriculum-scoped context. They cannot choose jurisdiction, curriculum, authority, standards, overlays, prerequisite edges, or enrollment.

## Migration strategy

F-006 uses additive migration first:
1. create jurisdiction/authority/role/overlay/enrollment tables;
2. add curriculum authority/version/effective/provenance fields;
3. add session curriculum snapshot fields;
4. backfill the existing MCPS curriculum into United States -> Maryland -> Montgomery County/MCPS authority records and create active enrollments for existing students;
5. retain legacy free-text/direct curriculum fields during this feature to avoid destructive migration;
6. change skill-code uniqueness from global to `(curriculum_id, code)`;
7. add application-level cross-curriculum guards and regression tests before considering legacy-field removal in a later feature.

## Initial ingestion examples

### Maryland / MCPS
- Country: United States
- State: Maryland
- Local authority context: Montgomery County Public Schools / county board
- State standards/policy authority: Maryland State Department of Education / State Board as applicable
- Curriculum: MCPS Grade 8 Mathematics, represented with its verified local/state authority relationship and source provenance

### Ontario / MTH1W
- Country: Canada
- Province: Ontario
- Curriculum authority: Ontario Ministry of Education
- Curriculum: Ontario Curriculum, Grade 9 Mathematics MTH1W
- Optional local implementation context: Ottawa-Carleton District School Board

OCDSB does not create a duplicate MTH1W curriculum merely by being the student's board.

## Consequences

Benefits:
- correct representation of Ontario and heterogeneous U.S. governance;
- no curriculum leakage caused by free-text jurisdiction matching;
- historical interpretation through version/effective periods;
- curriculum additions become data/ingestion operations rather than application deployments;
- state policy changes do not require schema redesign.

Costs:
- additional normalized tables and migration/backfill work;
- every tutoring/diagnostic selection path must carry curriculum scope;
- jurisdiction ingestion requires authoritative provenance and effective dates.

## Definition-of-Done implications

F-006 is not complete until tests prove:
- Ontario MTH1W provincial ownership with OCDSB local context;
- Maryland/MCPS authority flexibility;
- same skill code can exist in separate curricula;
- cross-curriculum session/problem/prerequisite/diagnostic access fails closed;
- historical enrollment/session evidence remains attached to its curriculum version;
- F-001 through F-005 regressions remain green;
- CI migration + seed + full tests succeed.
