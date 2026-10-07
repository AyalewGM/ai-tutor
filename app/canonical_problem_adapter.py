"""Compatibility adapter from canonical generated content to legacy Problem rows."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.canonical_problem_families import GeneratedProblem
from app.models import Problem, Skill


def materialize_problem(
    db: Session,
    *,
    generated: GeneratedProblem,
    curriculum_skill: Skill,
) -> Problem:
    """Materialize one canonical variant without transferring learner evidence.

    The caller supplies the curriculum-local skill already mapped to the
    generated problem's canonical skill. The generated family remains the
    source of mathematical truth; this row is a compatibility projection for
    existing tutoring flows.
    """
    source_key = f"{generated.family_code}:{generated.variant_id}"
    existing = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == curriculum_skill.id,
            Problem.source_type == "CANONICAL_GENERATED",
            Problem.solution["canonical_source_key"].as_string() == source_key,
        )
    )
    if existing is not None:
        return existing

    problem = Problem(
        primary_skill_id=curriculum_skill.id,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        prompt=generated.prompt,
        canonical_answer=generated.canonical_answer,
        answer_kind="FREE_TEXT",
        solution={
            "canonical_source_key": source_key,
            "canonical_skill_code": generated.canonical_skill_code,
            "family_code": generated.family_code,
            "variant_id": generated.variant_id,
            "mode": generated.mode.value,
            "hints": list(generated.hints),
            "misconception_answers": generated.misconception_answers,
            "provenance": generated.provenance,
            "visual_spec": generated.visual_spec,
        },
        source_type="CANONICAL_GENERATED",
    )
    db.add(problem)
    db.flush()
    return problem
