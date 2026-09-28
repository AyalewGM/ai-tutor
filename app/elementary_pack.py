import json
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_audit import audit_curriculum_pack_readiness
from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    ExpectationSkillMappingInput,
    persist_expectation_pack,
)
from app.content_models import ProblemContentMetadata
from app.content_validation import ContentValidationError
from app.curriculum_models import (
    CanonicalSkill,
    CurriculumSkillMapping,
    EducationAuthority,
    Jurisdiction,
)
from app.models import Curriculum, Problem, Skill
from app.prerequisite_ingestion import PrerequisiteEdgeInput, persist_prerequisite_edges
from app.services.problem_generation import GENERATORS

LearningMode = Literal["diagnostic", "guided", "independent", "mastery"]


class PackModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JurisdictionSpec(PackModel):
    country_code: str = "US"
    code: str
    name: str
    jurisdiction_type: str = "STATE_PROVINCE_TERRITORY"
    source_uri: str


class AuthoritySpec(PackModel):
    code: str
    name: str
    authority_type: str = "STATE_AGENCY"
    source_uri: str


class CurriculumSpec(PackModel):
    code: str
    name: str
    version: str
    grade_level: str
    source_uri: str


class ExpectationSpec(PackModel):
    source_identifier: str
    title: str
    source_uri: str
    strand: str
    description: str | None = None


class CanonicalSkillSpec(PackModel):
    code: str
    name: str
    description: str


class ProblemSpec(PackModel):
    key: str
    family: str
    prompt: str
    canonical_answer: str
    difficulty: int = Field(ge=1, le=10)
    objective: str
    modes: tuple[LearningMode, ...]
    parameters: dict[str, int | float | str] = Field(default_factory=dict)
    evaluation_type: str = "EXACT"
    origin: Literal["AUTHORED"] = "AUTHORED"
    license: str = "proprietary"

    @model_validator(mode="after")
    def validate_modes(self):
        if not self.modes:
            raise ValueError("problem must be eligible for at least one learning mode")
        if len(set(self.modes)) != len(self.modes):
            raise ValueError("problem learning modes must be unique")
        return self


class SkillSpec(PackModel):
    code: str
    name: str
    description: str
    difficulty_level: int = Field(ge=1, le=10)
    canonical: CanonicalSkillSpec
    standard_refs: tuple[str, ...]
    prerequisite_codes: tuple[str, ...] = ()
    problem_families: tuple[str, ...]
    problems: tuple[ProblemSpec, ...]


class ReadinessPolicy(PackModel):
    minimum_curated_per_skill: int = Field(default=4, ge=1)
    required_modes: tuple[LearningMode, ...] = (
        "diagnostic",
        "guided",
        "independent",
        "mastery",
    )


class ElementaryPack(PackModel):
    schema_version: Literal[1]
    jurisdiction: JurisdictionSpec
    authority: AuthoritySpec
    curriculum: CurriculumSpec
    expectations: tuple[ExpectationSpec, ...]
    skills: tuple[SkillSpec, ...]
    readiness: ReadinessPolicy = Field(default_factory=ReadinessPolicy)


class LoadResult(PackModel):
    curriculum_id: str
    skill_count: int
    expectation_count: int
    problem_count: int


def parse_pack(path: Path) -> ElementaryPack:
    try:
        payload = json.loads(path.read_text())
        pack = ElementaryPack.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ContentValidationError(f"Invalid elementary curriculum pack: {exc}") from exc
    validate_pack(pack)
    return pack


def _require_http_uri(value: str, field: str) -> None:
    if not value.startswith(("https://", "http://")):
        raise ContentValidationError(f"{field} must be an absolute HTTP(S) URI")


def _require_unique(values, label: str) -> None:
    values = tuple(values)
    if len(values) != len(set(values)):
        raise ContentValidationError(f"Duplicate {label} in elementary curriculum pack")


def _validate_acyclic(skills: tuple[SkillSpec, ...]) -> None:
    graph = {skill.code: skill.prerequisite_codes for skill in skills}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(code: str) -> None:
        if code in visiting:
            raise ContentValidationError("Elementary prerequisite graph contains a cycle")
        if code in visited:
            return
        visiting.add(code)
        for prerequisite in graph[code]:
            visit(prerequisite)
        visiting.remove(code)
        visited.add(code)

    for code in graph:
        visit(code)


def validate_pack(pack: ElementaryPack) -> None:
    _require_http_uri(pack.jurisdiction.source_uri, "jurisdiction.source_uri")
    _require_http_uri(pack.authority.source_uri, "authority.source_uri")
    _require_http_uri(pack.curriculum.source_uri, "curriculum.source_uri")
    if not pack.skills:
        raise ContentValidationError("Elementary curriculum pack must contain skills")
    if not pack.expectations:
        raise ContentValidationError("Elementary curriculum pack must contain expectations")

    _require_unique((item.source_identifier for item in pack.expectations), "expectation identifier")
    _require_unique((item.code for item in pack.skills), "skill code")
    expectation_ids = {item.source_identifier for item in pack.expectations}
    skill_codes = {item.code for item in pack.skills}
    problem_keys: set[str] = set()

    for expectation in pack.expectations:
        _require_http_uri(expectation.source_uri, "expectation.source_uri")
    for skill in pack.skills:
        if not skill.standard_refs or not set(skill.standard_refs) <= expectation_ids:
            raise ContentValidationError(
                f"Skill {skill.code} must reference expectations declared in the pack"
            )
        if not skill.problem_families:
            raise ContentValidationError(f"Skill {skill.code} must declare problem-family eligibility")
        _require_unique(skill.problem_families, f"problem family for {skill.code}")
        unsupported = set(skill.problem_families) - set(GENERATORS)
        if unsupported:
            raise ContentValidationError(
                f"Skill {skill.code} uses unsupported problem families: {', '.join(sorted(unsupported))}"
            )
        unknown_prerequisites = set(skill.prerequisite_codes) - skill_codes
        if unknown_prerequisites:
            raise ContentValidationError(
                f"Skill {skill.code} references prerequisites outside this pack"
            )
        if skill.code in skill.prerequisite_codes:
            raise ContentValidationError(f"Skill {skill.code} cannot require itself")
        if len(skill.problems) < pack.readiness.minimum_curated_per_skill:
            raise ContentValidationError(
                f"Skill {skill.code} has thin curated inventory: {len(skill.problems)}"
            )
        mode_keys: dict[str, set[str]] = {
            mode: set() for mode in pack.readiness.required_modes
        }
        for problem in skill.problems:
            if problem.key in problem_keys:
                raise ContentValidationError(f"Duplicate problem key: {problem.key}")
            problem_keys.add(problem.key)
            if problem.family not in skill.problem_families:
                raise ContentValidationError(
                    f"Problem {problem.key} uses a family not eligible for skill {skill.code}"
                )
            if not problem.prompt.strip() or not problem.canonical_answer.strip():
                raise ContentValidationError(
                    f"Problem {problem.key} requires prompt and canonical answer"
                )
            for mode in problem.modes:
                if mode in mode_keys:
                    mode_keys[mode].add(problem.key)
        missing_modes = [mode for mode, keys in mode_keys.items() if not keys]
        if missing_modes:
            raise ContentValidationError(
                f"Skill {skill.code} lacks inventory for: {', '.join(missing_modes)}"
            )
        mode_names = tuple(mode_keys)
        for index, left in enumerate(mode_names):
            for right in mode_names[index + 1 :]:
                if mode_keys[left] & mode_keys[right]:
                    raise ContentValidationError(
                        f"Skill {skill.code} reuses problems across {left} and {right}"
                    )
    _validate_acyclic(pack.skills)


def _jurisdiction(session: Session, spec: JurisdictionSpec) -> Jurisdiction:
    country = session.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id.is_(None), Jurisdiction.code == spec.country_code
        )
    )
    if country is None:
        country = Jurisdiction(
            code=spec.country_code,
            name="United States",
            jurisdiction_type="COUNTRY",
        )
        session.add(country)
        session.flush()
    row = session.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id == country.id, Jurisdiction.code == spec.code
        )
    )
    if row is None:
        row = Jurisdiction(parent_id=country.id, code=spec.code)
        session.add(row)
    row.name = spec.name
    row.jurisdiction_type = spec.jurisdiction_type
    row.source_uri = spec.source_uri
    row.provenance_json = {"source_type": "OFFICIAL_CURRICULUM"}
    session.flush()
    return row


def _authority(session: Session, jurisdiction: Jurisdiction, spec: AuthoritySpec):
    row = session.scalar(
        select(EducationAuthority).where(
            EducationAuthority.jurisdiction_id == jurisdiction.id,
            EducationAuthority.code == spec.code,
        )
    )
    if row is None:
        row = EducationAuthority(jurisdiction_id=jurisdiction.id, code=spec.code)
        session.add(row)
    row.name = spec.name
    row.authority_type = spec.authority_type
    row.source_uri = spec.source_uri
    row.provenance_json = {"source_type": "OFFICIAL_CURRICULUM"}
    session.flush()
    return row


def _curriculum(session: Session, authority, jurisdiction: Jurisdiction, spec: CurriculumSpec):
    row = session.scalar(
        select(Curriculum).where(
            Curriculum.authority_id == authority.id,
            Curriculum.code == spec.code,
            Curriculum.version == spec.version,
        )
    )
    if row is None:
        row = Curriculum(authority_id=authority.id, code=spec.code, version=spec.version)
        session.add(row)
    row.name = spec.name
    row.jurisdiction = jurisdiction.name
    row.grade_level = spec.grade_level
    row.source_uri = spec.source_uri
    row.provenance_json = {"source_type": "OFFICIAL_CURRICULUM"}
    row.active = True
    session.flush()
    return row


def _skills(session: Session, curriculum: Curriculum, pack: ElementaryPack):
    rows: dict[str, Skill] = {}
    for spec in pack.skills:
        skill = session.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id, Skill.code == spec.code
            )
        )
        if skill is None:
            skill = Skill(curriculum_id=curriculum.id, code=spec.code)
            session.add(skill)
        skill.name = spec.name
        skill.description = spec.description
        skill.difficulty_level = spec.difficulty_level
        skill.mastery_threshold = Decimal("0.850")
        session.flush()

        canonical = session.scalar(
            select(CanonicalSkill).where(CanonicalSkill.code == spec.canonical.code)
        )
        if canonical is None:
            canonical = CanonicalSkill(code=spec.canonical.code)
            session.add(canonical)
        canonical.name = spec.canonical.name
        canonical.description = spec.canonical.description
        canonical.subject = "MATHEMATICS"
        session.flush()

        mapping = session.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == skill.id
            )
        )
        if mapping is None:
            mapping = CurriculumSkillMapping(skill_id=skill.id)
            session.add(mapping)
        elif mapping.canonical_skill_id != canonical.id:
            raise ContentValidationError(
                f"Skill {skill.code} is already mapped to a different canonical concept"
            )
        mapping.canonical_skill_id = canonical.id
        mapping.mapping_type = "EQUIVALENT"
        mapping.provenance_json = {
            "basis": "AI Tutor reviewed standards mapping",
            "curriculum_code": curriculum.code,
            "curriculum_version": curriculum.version,
            "expectation_refs": list(spec.standard_refs),
        }
        session.flush()
        rows[spec.code] = skill
    return rows


def _problems(session: Session, curriculum: Curriculum, pack: ElementaryPack, skills):
    count = 0
    for skill_spec in pack.skills:
        skill = skills[skill_spec.code]
        for spec in skill_spec.problems:
            problem = session.scalar(
                select(Problem).where(
                    Problem.primary_skill_id == skill.id,
                    Problem.solution["pack_problem_key"].astext == spec.key,
                )
            )
            solution = {
                "answer": spec.canonical_answer,
                "parameters": spec.parameters,
                "problem_family": spec.family,
                "pack_problem_key": spec.key,
                "provenance": {
                    "origin": spec.origin,
                    "author": "AI Tutor curriculum team",
                    "license": spec.license,
                    "standards_authority": pack.authority.name,
                    "standards_source": pack.curriculum.source_uri,
                    "curriculum_version": pack.curriculum.version,
                },
            }
            if problem is None:
                problem = Problem(primary_skill_id=skill.id, source_type="CURATED")
                session.add(problem)
            problem.problem_type = spec.family
            problem.difficulty = spec.difficulty
            problem.prompt = spec.prompt
            problem.canonical_answer = spec.canonical_answer
            problem.solution = solution
            session.flush()

            metadata = session.scalar(
                select(ProblemContentMetadata).where(
                    ProblemContentMetadata.problem_id == problem.id
                )
            )
            if metadata is None:
                metadata = ProblemContentMetadata(problem_id=problem.id)
                session.add(metadata)
            metadata.curriculum_id = curriculum.id
            metadata.objective = spec.objective
            metadata.evaluation_type = spec.evaluation_type
            metadata.diagnostic_eligible = "diagnostic" in spec.modes
            metadata.guided_eligible = "guided" in spec.modes
            metadata.independent_eligible = "independent" in spec.modes
            metadata.mastery_eligible = "mastery" in spec.modes
            metadata.llm_solution_required = False
            metadata.provenance_json = {
                "source_type": "AI_TUTOR_AUTHORED",
                "pack_problem_key": spec.key,
                "problem_family": spec.family,
            }
            session.flush()
            count += 1
    return count


def load_pack(session: Session, pack: ElementaryPack) -> LoadResult:
    validate_pack(pack)
    with session.begin_nested():
        jurisdiction = _jurisdiction(session, pack.jurisdiction)
        authority = _authority(session, jurisdiction, pack.authority)
        curriculum = _curriculum(session, authority, jurisdiction, pack.curriculum)
        skills = _skills(session, curriculum, pack)

        expectation_pack = ContentPackInput(
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            expectations=tuple(
                ExpectationInput(
                    source_identifier=item.source_identifier,
                    title=item.title,
                    source_uri=item.source_uri,
                    strand=item.strand,
                    description=item.description,
                    provenance_metadata={"authority": pack.authority.name},
                )
                for item in pack.expectations
            ),
            mappings=tuple(
                ExpectationSkillMappingInput(
                    source_identifier=source_identifier,
                    skill_code=skill.code,
                )
                for skill in pack.skills
                for source_identifier in skill.standard_refs
            ),
        )
        expectations = persist_expectation_pack(session, expectation_pack)
        edges = tuple(
            PrerequisiteEdgeInput(
                skill_code=skill.code,
                prerequisite_skill_code=prerequisite,
            )
            for skill in pack.skills
            for prerequisite in skill.prerequisite_codes
        )
        persist_prerequisite_edges(
            session,
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            edges=edges,
        )
        problem_count = _problems(session, curriculum, pack, skills)
        session.flush()
        audit_curriculum_pack_readiness(session, curriculum_id=curriculum.id)
    return LoadResult(
        curriculum_id=str(curriculum.id),
        skill_count=len(skills),
        expectation_count=len(expectations),
        problem_count=problem_count,
    )
