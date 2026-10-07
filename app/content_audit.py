from __future__ import annotations

import uuid

"""Database-backed deterministic content audits for F-007.

Audits in this module are application-owned quality gates. They do not call an
LLM and never infer curriculum equivalence across jurisdictions.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.content_models import (
    CurriculumExpectation,
    ExpectationSkillMapping,
    ProblemContentMetadata,
)
from app.content_validation import (
    ContentValidationError,
    CurriculumScopedRef,
    validate_active_skill_traceability,
    validate_expectation_skill_mapping,
    validate_fresh_problem_sets,
    validate_learning_mode_inventory,
    validate_problem_metadata,
    validate_problem_scope,
)
from app.models import Curriculum, Problem, Skill, SkillPrerequisite


def _active_curriculum(session: Session, curriculum_id) -> Curriculum:
    curriculum = session.get(Curriculum, curriculum_id)
    if curriculum is None or not curriculum.active:
        raise ValueError("Active curriculum is required for content audit")
    return curriculum


def audit_curriculum_isolation(
    session: Session,
    *,
    curriculum_id,
) -> None:
    """Re-audit persisted records that could leak across curriculum boundaries.

    Normal ingestion validates these relationships before persistence. This
    audit intentionally reads the database back and fails closed if records were
    inserted or modified through another path. It provides an independent QA
    gate for the repository's strict jurisdiction-isolation requirement.
    """
    curriculum = _active_curriculum(session, curriculum_id)
    skills = session.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)).all()
    skill_by_id = {skill.id: skill for skill in skills}
    selected_skill_ids = set(skill_by_id)

    expectations = session.scalars(
        select(CurriculumExpectation).where(
            CurriculumExpectation.curriculum_id == curriculum.id
        )
    ).all()
    expectation_by_id = {expectation.id: expectation for expectation in expectations}
    selected_expectation_ids = set(expectation_by_id)

    # Mapping rows are deliberately inspected globally so a row with a forged
    # mapping.curriculum_id cannot hide a reference into this curriculum.
    for mapping in session.scalars(select(ExpectationSkillMapping)).all():
        if not (
            mapping.curriculum_id == curriculum.id
            or mapping.expectation_id in selected_expectation_ids
            or mapping.skill_id in selected_skill_ids
        ):
            continue
        expectation = session.get(CurriculumExpectation, mapping.expectation_id)
        skill = session.get(Skill, mapping.skill_id)
        if expectation is None or skill is None:
            raise ContentValidationError("Expectation mapping references missing persisted records")
        if mapping.curriculum_id != curriculum.id:
            raise ContentValidationError(
                "Expectation mapping touching audited curriculum uses another curriculum_id"
            )
        validate_expectation_skill_mapping(
            mapping_curriculum_id=mapping.curriculum_id,
            expectation=CurriculumScopedRef(
                id=expectation.id,
                curriculum_id=expectation.curriculum_id,
            ),
            skill=CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id),
        )

    # A prerequisite edge has no curriculum_id column, so validate every edge
    # touching an audited skill from the curricula attached to both endpoints.
    # Cross-grade edges are permitted when both endpoints belong to the same
    # jurisdiction (and authority/version), preserving state-level isolation.
    curricula_by_id: dict[uuid.UUID, Curriculum] = {}

    def _curriculum_for_skill(skill: Skill) -> Curriculum:
        c = curricula_by_id.get(skill.curriculum_id)
        if c is None:
            c = session.get(Curriculum, skill.curriculum_id)
            curricula_by_id[skill.curriculum_id] = c
        if c is None:
            raise ContentValidationError(
                "Prerequisite edge references a skill with no curriculum"
            )
        return c

    for edge in session.scalars(select(SkillPrerequisite)).all():
        if (
            edge.skill_id not in selected_skill_ids
            and edge.prerequisite_skill_id not in selected_skill_ids
        ):
            continue
        skill = session.get(Skill, edge.skill_id)
        prerequisite = session.get(Skill, edge.prerequisite_skill_id)
        if skill is None or prerequisite is None:
            raise ContentValidationError("Prerequisite edge references missing persisted skills")
        if skill.id == prerequisite.id:
            raise ContentValidationError("A skill cannot be its own prerequisite")
        skill_curriculum = _curriculum_for_skill(skill)
        prereq_curriculum = _curriculum_for_skill(prerequisite)
        if skill_curriculum.jurisdiction != prereq_curriculum.jurisdiction:
            raise ContentValidationError(
                "Prerequisite edge crosses jurisdiction boundaries"
            )

    # Metadata is also inspected globally so a forged metadata.curriculum_id
    # cannot disguise a problem whose primary skill belongs to this curriculum.
    for metadata in session.scalars(select(ProblemContentMetadata)).all():
        problem = session.get(Problem, metadata.problem_id)
        if problem is None:
            raise ContentValidationError("Problem metadata references a missing problem")
        if (
            metadata.curriculum_id != curriculum.id
            and problem.primary_skill_id not in selected_skill_ids
        ):
            continue
        primary_skill = session.get(Skill, problem.primary_skill_id)
        if primary_skill is None:
            raise ContentValidationError("Problem references a missing primary skill")
        if metadata.curriculum_id != curriculum.id:
            raise ContentValidationError(
                "Problem attached to audited curriculum skill uses another curriculum_id"
            )
        validate_problem_scope(
            pack_curriculum_id=metadata.curriculum_id,
            primary_skill=CurriculumScopedRef(
                id=primary_skill.id,
                curriculum_id=primary_skill.curriculum_id,
            ),
        )


def audit_curriculum_skill_traceability(
    session: Session,
    *,
    curriculum_id,
) -> None:
    """Require every skill in one curriculum to have source expectation traceability.

    The current schema does not expose a per-skill active flag, so the pilot
    completeness rule applies to every skill registered under the selected
    curriculum. Mapping counts are constrained by both mapping.curriculum_id and
    skill_id so a mapping from another jurisdiction cannot satisfy this audit.
    """
    curriculum = _active_curriculum(session, curriculum_id)

    skills = session.scalars(
        select(Skill).where(Skill.curriculum_id == curriculum.id).order_by(Skill.code)
    ).all()

    for skill in skills:
        mapped_expectation_count = session.scalar(
            select(func.count())
            .select_from(ExpectationSkillMapping)
            .where(
                ExpectationSkillMapping.curriculum_id == curriculum.id,
                ExpectationSkillMapping.skill_id == skill.id,
            )
        )
        validate_active_skill_traceability(
            skill=CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id),
            mapped_expectation_count=int(mapped_expectation_count or 0),
        )


def audit_curriculum_problem_inventory(
    session: Session,
    *,
    curriculum_id,
) -> None:
    """Audit persisted pilot problems for complete, fresh application-owned pools.

    Every skill in an accepted pilot pack must have at least one persisted
    problem reserved for each deterministic learning mode. Problem IDs may not
    be shared across mode pools, which guarantees that post-help independent and
    mastery evidence can be selected from genuinely fresh content without asking
    an LLM to decide whether reuse is pedagogically acceptable.

    Both metadata.curriculum_id and the problem's primary skill are constrained
    to the selected curriculum. Cross-jurisdiction records therefore cannot make
    an incomplete pack pass this audit. Persisted metadata is revalidated here
    as a second-line acceptance gate so database corruption or bypassed ingestion
    cannot make assessment evidence depend on an LLM.
    """
    curriculum = _active_curriculum(session, curriculum_id)
    skills = session.scalars(
        select(Skill).where(Skill.curriculum_id == curriculum.id).order_by(Skill.code)
    ).all()

    for skill in skills:
        rows = session.execute(
            select(Problem.id, ProblemContentMetadata)
            .join(
                ProblemContentMetadata,
                ProblemContentMetadata.problem_id == Problem.id,
            )
            .where(
                Problem.primary_skill_id == skill.id,
                ProblemContentMetadata.curriculum_id == curriculum.id,
            )
        ).all()

        pools = {
            "diagnostic": [],
            "guided": [],
            "independent": [],
            "mastery": [],
        }
        skill_ref = CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id)
        for problem_id, metadata in rows:
            validate_problem_metadata(
                metadata_curriculum_id=metadata.curriculum_id,
                primary_skill=skill_ref,
                objective=metadata.objective,
                evaluation_type=metadata.evaluation_type,
                diagnostic_eligible=metadata.diagnostic_eligible,
                guided_eligible=metadata.guided_eligible,
                independent_eligible=metadata.independent_eligible,
                mastery_eligible=metadata.mastery_eligible,
                llm_solution_required=metadata.llm_solution_required,
            )
            if metadata.diagnostic_eligible:
                pools["diagnostic"].append(problem_id)
            if metadata.guided_eligible:
                pools["guided"].append(problem_id)
            if metadata.independent_eligible:
                pools["independent"].append(problem_id)
            if metadata.mastery_eligible:
                pools["mastery"].append(problem_id)

        validate_learning_mode_inventory(
            skill=skill_ref,
            diagnostic_count=len(pools["diagnostic"]),
            guided_count=len(pools["guided"]),
            independent_count=len(pools["independent"]),
            mastery_count=len(pools["mastery"]),
        )
        validate_fresh_problem_sets(
            skill=skill_ref,
            diagnostic_problem_ids=pools["diagnostic"],
            guided_problem_ids=pools["guided"],
            independent_problem_ids=pools["independent"],
            mastery_problem_ids=pools["mastery"],
        )


def audit_curriculum_pack_readiness(
    session: Session,
    *,
    curriculum_id,
) -> None:
    """Run the deterministic acceptance gates for one persisted curriculum pack.

    This deliberately composes independent database-backed checks instead of
    inferring readiness from CI or from an LLM. A pack is only structurally ready
    when jurisdiction isolation, official-source traceability, and fresh
    mode-specific problem inventory all pass against persisted records.
    """
    audit_curriculum_isolation(session, curriculum_id=curriculum_id)
    audit_curriculum_skill_traceability(session, curriculum_id=curriculum_id)
    audit_curriculum_problem_inventory(session, curriculum_id=curriculum_id)


# ===========================================================================
# Canonical Content Coverage Auditor
#
# Deterministically evaluates the pedagogical depth and coverage of every
# canonical skill, going beyond raw family counts.
#
# Usage:
#     python -m app.content_audit          # pretty-print to stdout
#     python -m app.content_audit --json   # machine-readable JSON
# ===========================================================================

import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

from app.canonical_problem_families import FAMILIES, LearningMode

# ---------------------------------------------------------------------------
# Evidence dimensions the auditor tracks
# ---------------------------------------------------------------------------

ALL_EVIDENCE_DIMS = frozenset({
    "procedural_fluency",
    "conceptual_understanding",
    "representation",
    "number_sense",
    "estimation",
    "modeling",
    "transfer",
    "comparison",
    "reasoning",
    "error_analysis",
    "misconception_probe",
})

# ---------------------------------------------------------------------------
# Expected profiles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoverageExpectation:
    """Defines minimum coverage expectations for a skill category."""
    min_families: int = 3
    required_evidence: frozenset[str] = frozenset()
    require_word_problem: bool = False
    require_misconception: bool = False
    require_diagnostic: bool = True
    require_mastery: bool = True
    min_difficulty_span: int = 2
    description: str = ""


COVERAGE_PROFILES: dict[str, CoverageExpectation] = {
    "major_operation": CoverageExpectation(
        min_families=8,
        required_evidence=frozenset({
            "procedural_fluency", "conceptual_understanding",
            "modeling", "error_analysis", "misconception_probe",
        }),
        require_word_problem=True,
        require_misconception=True,
        require_diagnostic=True,
        require_mastery=True,
        min_difficulty_span=3,
        description="Major arithmetic operation (add/sub/mul/div)",
    ),
    "core_concept": CoverageExpectation(
        min_families=5,
        required_evidence=frozenset({
            "conceptual_understanding", "reasoning",
        }),
        require_word_problem=False,
        require_misconception=True,
        require_diagnostic=True,
        require_mastery=True,
        min_difficulty_span=2,
        description="Core concept (place value, integers, estimation, etc.)",
    ),
    "supplementary": CoverageExpectation(
        min_families=2,
        required_evidence=frozenset(),
        require_word_problem=False,
        require_misconception=False,
        require_diagnostic=True,
        require_mastery=True,
        min_difficulty_span=1,
        description="Supplementary or narrow skill",
    ),
}

SKILL_PROFILE_MAP: dict[str, str] = {
    # Major operations
    "MATH.NS.ADDITION": "major_operation",
    "MATH.NS.SUBTRACTION": "major_operation",
    "MATH.NS.MULTIPLICATION": "major_operation",
    "MATH.NS.DIVISION": "major_operation",
    "MATH.NF.ADD_SUBTRACT": "major_operation",
    "MATH.NF.MULTIPLY": "major_operation",
    "MATH.NF.DIVIDE": "major_operation",
    # Core concepts
    "MATH.NS.PLACE_VALUE": "core_concept",
    "MATH.NS.COMPARE_ORDER": "core_concept",
    "MATH.NS.COUNTING": "core_concept",
    "MATH.NS.INTEGERS": "core_concept",
    "MATH.NS.INTEGER_OPERATIONS": "core_concept",
    "MATH.NS.FACTORS_MULTIPLES": "core_concept",
    "MATH.NS.GCF_LCM": "core_concept",
    "MATH.NS.PRIME_COMPOSITE": "core_concept",
    "MATH.NS.ORDER_OF_OPERATIONS": "core_concept",
    "MATH.NS.ESTIMATION": "core_concept",
    "MATH.NS.PROPERTIES": "core_concept",
    "MATH.NS.ROUNDING": "core_concept",
    "MATH.RP.PERCENT.OF": "core_concept",
    "MATH.RP.PERCENT.CONVERT": "core_concept",
    "MATH.RP.RATIO.CONCEPT": "core_concept",
    "MATH.RP.UNIT_RATE": "core_concept",
    "MATH.RP.PROPORTION": "core_concept",
    # Supplementary
    "MATH.NS.COMPOSE_DECOMPOSE": "supplementary",
    "MATH.NS.EXPANDED_FORM": "supplementary",
    "MATH.NS.WORD_FORM": "supplementary",
    "MATH.NS.NUMBER_LINE": "supplementary",
    "MATH.NS.DIVISIBILITY": "supplementary",
    "MATH.NF.EQUIVALENT_FRACTIONS": "supplementary",
    "MATH.NF.SIMPLIFY": "supplementary",
    "MATH.NF.COMPARE": "supplementary",
    "MATH.EE.EQUATION.ONE": "supplementary",
    "MATH.EE.EQUATION.TWO": "supplementary",
    "MATH.RP.PERCENT.CHANGE": "supplementary",
    "MATH.RP.PERCENT.APPLICATION": "supplementary",
    "MATH.RP.PERCENT.MULTI": "supplementary",
}


# ---------------------------------------------------------------------------
# Audit data structures
# ---------------------------------------------------------------------------


@dataclass
class SkillAudit:
    """Coverage report for a single canonical skill."""
    skill_code: str
    family_count: int = 0
    family_codes: list[str] = field(default_factory=list)
    evidence_dimensions: set[str] = field(default_factory=set)
    missing_evidence: set[str] = field(default_factory=set)
    problem_types: set[str] = field(default_factory=set)
    learning_modes: set[str] = field(default_factory=set)
    missing_modes: set[str] = field(default_factory=set)
    min_difficulty: int = 99
    max_difficulty: int = 0
    difficulty_span: int = 0
    has_word_problems: bool = False
    word_problem_count: int = 0
    has_misconception_probe: bool = False
    misconception_family_count: int = 0
    has_error_analysis: bool = False
    has_estimation: bool = False
    profile_name: str = ""
    quality_gate_pass: bool = True
    quality_gate_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence_dimensions"] = sorted(d["evidence_dimensions"])
        d["missing_evidence"] = sorted(d["missing_evidence"])
        d["problem_types"] = sorted(d["problem_types"])
        d["learning_modes"] = sorted(d["learning_modes"])
        d["missing_modes"] = sorted(d["missing_modes"])
        return d


@dataclass
class AuditReport:
    """Full coverage audit report."""
    total_families: int = 0
    total_skills: int = 0
    skills: dict[str, SkillAudit] = field(default_factory=dict)
    uncovered_skills: list[str] = field(default_factory=list)
    quality_gate_passes: int = 0
    quality_gate_failures: int = 0
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_families": self.total_families,
            "total_skills": self.total_skills,
            "quality_gate_passes": self.quality_gate_passes,
            "quality_gate_failures": self.quality_gate_failures,
            "uncovered_skills": self.uncovered_skills,
            "summary": self.summary,
            "skills": {k: v.to_dict() for k, v in sorted(self.skills.items())},
        }


# ---------------------------------------------------------------------------
# Coverage auditor
# ---------------------------------------------------------------------------


def audit_canonical_coverage(families: dict | None = None) -> AuditReport:
    """Run the coverage audit and return a structured report.

    Parameters
    ----------
    families : dict, optional
        Family registry to audit.  Defaults to the global ``FAMILIES``.
    """
    if families is None:
        families = FAMILIES

    report = AuditReport(total_families=len(families))
    skills: dict[str, SkillAudit] = defaultdict(lambda: SkillAudit(skill_code=""))

    for code, spec in families.items():
        sk = skills[spec.canonical_skill_code]
        sk.skill_code = spec.canonical_skill_code
        sk.family_count += 1
        sk.family_codes.append(code)
        sk.evidence_dimensions.update(spec.evidence_dimensions)
        sk.problem_types.add(spec.problem_type)
        sk.learning_modes.update(m.value for m in spec.modes)
        sk.min_difficulty = min(sk.min_difficulty, spec.min_difficulty)
        sk.max_difficulty = max(sk.max_difficulty, spec.max_difficulty)

        if spec.problem_type == "WORD_PROBLEM":
            sk.has_word_problems = True
            sk.word_problem_count += 1
        if "error_analysis" in spec.evidence_dimensions:
            sk.has_error_analysis = True
        if "misconception_probe" in spec.evidence_dimensions:
            sk.has_misconception_probe = True
            sk.misconception_family_count += 1
        if "estimation" in spec.evidence_dimensions:
            sk.has_estimation = True
        if spec.problem_type == "ESTIMATION":
            sk.has_estimation = True

    # Compute difficulty span and apply quality gates.
    all_modes = {m.value for m in LearningMode}
    for sk in skills.values():
        sk.difficulty_span = sk.max_difficulty - sk.min_difficulty + 1 if sk.family_count > 0 else 0
        sk.missing_modes = all_modes - sk.learning_modes

        profile_name = SKILL_PROFILE_MAP.get(sk.skill_code, "supplementary")
        sk.profile_name = profile_name
        profile = COVERAGE_PROFILES[profile_name]

        failures: list[str] = []
        if sk.family_count < profile.min_families:
            failures.append(
                f"family_count={sk.family_count} < min={profile.min_families}"
            )
        missing_ev = profile.required_evidence - sk.evidence_dimensions
        if missing_ev:
            failures.append(f"missing_evidence={sorted(missing_ev)}")
            sk.missing_evidence = missing_ev
        if profile.require_word_problem and not sk.has_word_problems:
            failures.append("no word problems")
        if profile.require_misconception and not sk.has_misconception_probe:
            failures.append("no misconception probe")
        if profile.require_diagnostic and LearningMode.DIAGNOSTIC.value not in sk.learning_modes:
            failures.append("no diagnostic mode")
        if profile.require_mastery and LearningMode.MASTERY.value not in sk.learning_modes:
            failures.append("no mastery mode")
        if sk.difficulty_span < profile.min_difficulty_span:
            failures.append(
                f"difficulty_span={sk.difficulty_span} < min={profile.min_difficulty_span}"
            )

        sk.quality_gate_pass = len(failures) == 0
        sk.quality_gate_failures = failures

    report.skills = dict(skills)
    report.total_skills = len(skills)
    report.quality_gate_passes = sum(1 for s in skills.values() if s.quality_gate_pass)
    report.quality_gate_failures = sum(1 for s in skills.values() if not s.quality_gate_pass)

    for expected_skill in SKILL_PROFILE_MAP:
        if expected_skill not in skills:
            report.uncovered_skills.append(expected_skill)

    report.summary = {
        "total_families": report.total_families,
        "total_skills": report.total_skills,
        "skills_passing_quality_gate": report.quality_gate_passes,
        "skills_failing_quality_gate": report.quality_gate_failures,
        "uncovered_expected_skills": len(report.uncovered_skills),
        "families_by_type": _count_by_type(families),
        "families_with_word_problems": sum(
            1 for s in families.values() if s.problem_type == "WORD_PROBLEM"
        ),
        "families_with_error_analysis": sum(
            1 for s in families.values() if "error_analysis" in s.evidence_dimensions
        ),
        "families_with_misconception_probe": sum(
            1 for s in families.values() if "misconception_probe" in s.evidence_dimensions
        ),
        "families_with_estimation": sum(
            1 for s in families.values()
            if "estimation" in s.evidence_dimensions or s.problem_type == "ESTIMATION"
        ),
    }

    return report


# Keep backward-compatible short name
audit = audit_canonical_coverage


def _count_by_type(families: dict) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for spec in families.values():
        counts[spec.problem_type] += 1
    return dict(sorted(counts.items()))


def format_report(report: AuditReport) -> str:
    """Return a human-readable report string."""
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("CANONICAL CONTENT COVERAGE AUDIT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Total families: {report.total_families}")
    lines.append(f"Total skills:   {report.total_skills}")
    lines.append(f"Quality gates:  {report.quality_gate_passes} pass, {report.quality_gate_failures} fail")
    lines.append("")

    s = report.summary
    lines.append("Families by type:")
    for t, c in sorted(s.get("families_by_type", {}).items()):
        lines.append(f"  {t}: {c}")
    lines.append(f"  Word problems: {s.get('families_with_word_problems', 0)}")
    lines.append(f"  Error analysis: {s.get('families_with_error_analysis', 0)}")
    lines.append(f"  Misconception probe: {s.get('families_with_misconception_probe', 0)}")
    lines.append(f"  Estimation: {s.get('families_with_estimation', 0)}")
    lines.append("")

    if report.uncovered_skills:
        lines.append("UNCOVERED EXPECTED SKILLS:")
        for sk in report.uncovered_skills:
            lines.append(f"  - {sk}")
        lines.append("")

    lines.append("-" * 70)
    lines.append("SKILL DETAILS")
    lines.append("-" * 70)
    for code in sorted(report.skills):
        sk = report.skills[code]
        gate = "PASS" if sk.quality_gate_pass else "FAIL"
        lines.append(f"\n{code}  [{sk.profile_name}]  [{gate}]")
        lines.append(f"  Families: {sk.family_count}")
        lines.append(f"  Evidence: {', '.join(sorted(sk.evidence_dimensions))}")
        if sk.missing_evidence:
            lines.append(f"  Missing evidence: {', '.join(sorted(sk.missing_evidence))}")
        lines.append(f"  Types: {', '.join(sorted(sk.problem_types))}")
        lines.append(f"  Modes: {', '.join(sorted(sk.learning_modes))}")
        if sk.missing_modes:
            lines.append(f"  Missing modes: {', '.join(sorted(sk.missing_modes))}")
        lines.append(f"  Difficulty: {sk.min_difficulty}\u2013{sk.max_difficulty} (span {sk.difficulty_span})")
        lines.append(f"  Word problems: {sk.word_problem_count}")
        lines.append(f"  Misconception families: {sk.misconception_family_count}")
        if sk.quality_gate_failures:
            lines.append("  Quality gate failures:")
            for f in sk.quality_gate_failures:
                lines.append(f"    - {f}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    report = audit_canonical_coverage()
    if "--json" in sys.argv:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report(report))


if __name__ == "__main__":
    main()
