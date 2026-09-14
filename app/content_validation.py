from collections.abc import Collection, Hashable
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


def validate_source_identity(
    *,
    curriculum_version: str,
    source_identifier: str,
    source_uri: str,
) -> None:
    """Require stable provenance fields before an expectation can be ingested."""
    if not curriculum_version.strip():
        raise ContentValidationError("Curriculum version is required")
    if not source_identifier.strip():
        raise ContentValidationError("Source identifier is required")
    if not source_uri.strip().startswith(("https://", "http://")):
        raise ContentValidationError("Source URI must be an absolute HTTP(S) URI")


def validate_learning_mode_inventory(
    *,
    skill: CurriculumScopedRef,
    diagnostic_count: int,
    guided_count: int,
    independent_count: int,
    mastery_count: int,
) -> None:
    """Require inventory capacity for every deterministic learning mode."""
    counts = {
        "diagnostic": diagnostic_count,
        "guided": guided_count,
        "independent": independent_count,
        "mastery": mastery_count,
    }
    missing = [mode for mode, count in counts.items() if count < 1]
    if missing:
        raise ContentValidationError(
            f"Skill {skill.id} lacks problem inventory for: {', '.join(missing)}"
        )


def validate_fresh_problem_sets(
    *,
    skill: CurriculumScopedRef,
    diagnostic_problem_ids: Collection[Hashable],
    guided_problem_ids: Collection[Hashable],
    independent_problem_ids: Collection[Hashable],
    mastery_problem_ids: Collection[Hashable],
) -> None:
    """Require non-empty, non-overlapping problem pools for deterministic modes.

    A problem used for diagnosis, guided practice, independent evidence, or a
    mastery check must not be reused in another pool. This makes the repository
    acceptance rule for a genuinely fresh post-help independent/mastery problem
    testable without asking an LLM to decide whether a problem is fresh.
    """
    pools = {
        "diagnostic": set(diagnostic_problem_ids),
        "guided": set(guided_problem_ids),
        "independent": set(independent_problem_ids),
        "mastery": set(mastery_problem_ids),
    }

    missing = [mode for mode, problem_ids in pools.items() if not problem_ids]
    if missing:
        raise ContentValidationError(
            f"Skill {skill.id} lacks problem inventory for: {', '.join(missing)}"
        )

    modes = tuple(pools)
    for index, left_mode in enumerate(modes):
        for right_mode in modes[index + 1 :]:
            overlap = pools[left_mode] & pools[right_mode]
            if overlap:
                raise ContentValidationError(
                    f"Skill {skill.id} reuses problem IDs across "
                    f"{left_mode} and {right_mode}: {len(overlap)} overlap"
                )
