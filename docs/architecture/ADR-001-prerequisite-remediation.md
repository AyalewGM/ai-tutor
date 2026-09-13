# ADR-001: Persist Original Goal Separately from Active Remediation Skill

Status: Accepted
Date: 2026-09-13
Feature: F-001

## Context

The current tutor session stores one `primary_skill_id`. Prerequisite-aware remediation needs to temporarily teach a different skill while preserving the learner's original goal so the tutor can return to it after remediation.

The data model already has `SkillPrerequisite`, `StudentSkill`, misconception history, immutable attempts, tutor turns, and mastery events.

## Decision

Keep `TutorSession.primary_skill_id` as the original target skill for the session.

Add persisted remediation context:
- `active_skill_id`: the skill currently being practiced; defaults to the primary skill;
- `remediation_skill_id`: nullable prerequisite currently being remediated;
- `remediation_reason`: nullable machine-readable reason/code.

Problem selection and mastery updates operate on `active_skill_id`.

When readiness logic determines that a prerequisite gap is sufficiently evidenced:
1. persist the remediation transition;
2. set `active_skill_id` to the prerequisite;
3. enter `REMEDIATION`;
4. teach and assess the prerequisite;
5. require independent evidence before exit;
6. clear remediation fields;
7. restore `active_skill_id = primary_skill_id`;
8. resume the original target with a suitable problem.

## Readiness decision

A deterministic `PrerequisiteService` owns prerequisite selection. It may use:
- explicit prerequisite edges;
- prerequisite mastery score;
- evidence confidence;
- misconception-to-skill mapping;
- repeated-error evidence.

The LLM may explain the transition but cannot choose the prerequisite or declare remediation complete.

## Consequences

Positive:
- original goal is never lost;
- remediation is auditable;
- no nested conversational memory is required;
- future recommendation/optimization logic can operate on the same graph;
- frontend can explain that the tutor will return to the original goal.

Tradeoffs:
- session logic becomes skill-aware in addition to state-aware;
- API responses should eventually expose learner-friendly focus information;
- nested remediation should be explicitly constrained in the MVP rather than allowed recursively.

## MVP constraint

F-001 supports one active remediation level. If the remediation skill itself reveals a deeper prerequisite gap, record the evidence but do not recursively descend during this first implementation unless the Product Owner expands the acceptance criteria.
