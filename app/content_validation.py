from dataclasses import dataclass
from uuid import UUID


class ContentValidationError(ValueError):
    """Raised when curriculum content violates deterministic repository rules."""


@dataclass(frozen=True)
class CurriculumScopedRef:
    id: UUID
    curriculum_id: UUID


def validate_expectation_skill_mapping(
    *,
    mapping_curriculum_id: UUID,
    expectation: CurriculumScopedRef,
    skill: CurriculumScopedRef,
) -> None:
    """Reject mappings that do not stay inside one curriculum boundary."""
    if expectation.curriculum_id != mapping_curriculum_id:
        raise ContentValidationError(
            "Expectation curriculum does not match mapping curriculum"
        )
    if skill.curriculum_id != mapping_curriculum_id:
        raise ContentValidationError("Skill curriculum does not match mapping curriculum")


def validate_prerequisite_edge(
    *,
    skill: CurriculumScopedRef,
    prerequisite: CurriculumScopedRef,
) -> None:
    """Reject prerequisite edges crossing curriculum boundaries."""
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ContentValidationError(
            "Prerequisite edges cannot cross curriculum boundaries"
        )
    if skill.id == prerequisite.id:
        raise ContentValidationError("A skill cannot be its own prerequisite")


def validate_problem_scope(
    *,
    pack_curriculum_id: UUID,
    primary_skill: CurriculumScopedRef,
) -> None:
    """Reject a problem assigned to a skill outside the ingested content pack."""
    if primary_skill.curriculum_id != pack_curriculum_id:
        raise ContentValidationError(
            "Problem primary skill must belong to the content-pack curriculum"
        )


def validate_active_skill_traceability(
    *,
    skill: CurriculumScopedRef,
    mapped_expectation_count: int,
) -> None:
    """Require every active pilot skill to have authoritative source traceability."""
    if mapped_expectation_count < 1:
        raise ContentValidationError(
            f"Active skill {skill.id} must map to at least one curriculum expectation"
        )


def validate_problem_inventory(
    *,
    skill: CurriculumScopedRef,
    problem_count: int,
    minimum_required: int,
) -> None:
    """Require enough distinct problems for the caller's accepted learning modes."""
    if minimum_required < 1:
        raise ValueError("minimum_required must be positive")
    if problem_count < minimum_required:
        raise ContentValidationError(
            f"Skill {skill.id} has {problem_count} problems; "
            f"at least {minimum_required} are required"
        )
