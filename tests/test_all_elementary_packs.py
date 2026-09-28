import json
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.elementary_pack import parse_pack
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_all_elementary_packs import seed

_MISCONCEPTION_CATALOG = (
    Path(__file__).parents[1] / "docs/curriculum/misconceptions/grades_1_2.json"
)

_PACK_DIR = __import__("pathlib").Path(__file__).parents[1] / "docs/curriculum/packs"
_EXPECTED_PACKS = [
    ("md-grade1-mccrs-2026_27.json", "MD", "1", 8),
    ("md-grade2-mccrs-2026_27.json", "MD", "2", 9),
    ("md-grade3-mccrs-2026_27.json", "MD", "3", 4),
    ("md-grade4-mccrs-2026_27.json", "MD", "4", 3),
    ("md-grade5-mccrs-2026_27.json", "MD", "5", 3),
    ("dc-grade1-ccss-2024_25.json", "DC", "1", 8),
    ("dc-grade2-ccss-2024_25.json", "DC", "2", 9),
    ("dc-grade3-ccss-2024_25.json", "DC", "3", 4),
    ("dc-grade4-ccss-2024_25.json", "DC", "4", 3),
    ("dc-grade5-ccss-2024_25.json", "DC", "5", 3),
    ("va-grade1-sol-2024_25.json", "VA", "1", 8),
    ("va-grade2-sol-2024_25.json", "VA", "2", 9),
    ("va-grade3-sol-2024_25.json", "VA", "3", 4),
    ("va-grade4-sol-2024_25.json", "VA", "4", 3),
    ("va-grade5-sol-2024_25.json", "VA", "5", 3),
]


def test_all_packs_parse_and_validate():
    for filename, _, _, expected_skills in _EXPECTED_PACKS:
        pack = parse_pack(_PACK_DIR / filename)
        assert pack.schema_version == 1
        assert len(pack.skills) == expected_skills
        assert all(
            len(skill.problems) >= pack.readiness.minimum_curated_per_skill
            for skill in pack.skills
        )


def test_seed_all_packs_is_idempotent_and_complete():
    first = seed()
    second = seed()
    assert len(first) == len(_EXPECTED_PACKS)
    assert first == second

    loaded_ids = {r["curriculum_id"] for r in first}
    with SessionLocal() as db:
        for filename, jurisdiction, grade, _ in _EXPECTED_PACKS:
            pack = parse_pack(_PACK_DIR / filename)
            curriculum = db.scalar(
                select(Curriculum).where(
                    Curriculum.code == pack.curriculum.code,
                    Curriculum.version == pack.curriculum.version,
                )
            )
            assert curriculum is not None
            assert str(curriculum.id) in loaded_ids
            assert curriculum.grade_level == grade
            assert curriculum.jurisdiction == pack.jurisdiction.name

        skills = list(
            db.scalars(select(Skill).where(Skill.curriculum_id.in_(loaded_ids)))
        )
        assert len(skills) == sum(expected for _, _, _, expected in _EXPECTED_PACKS)

        problems = list(
            db.scalars(
                select(Problem).where(
                    Problem.primary_skill_id.in_({skill.id for skill in skills}),
                    Problem.source_type == "CURATED",
                )
            )
        )
        expected_problems = sum(
            sum(
                len(parse_pack(_PACK_DIR / filename).skills[i].problems)
                for i in range(expected)
            )
            for filename, _, _, expected in _EXPECTED_PACKS
        )
        assert len(problems) == expected_problems
        assert all("pack_problem_key" in (p.solution or {}) for p in problems)

        mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.skill_id.in_({skill.id for skill in skills})
                )
            )
        )
        assert len(mappings) == len(skills)

        canonical_codes = {
            db.get(CanonicalSkill, m.canonical_skill_id).code for m in mappings
        }
        assert canonical_codes

        edges = list(
            db.scalars(
                select(SkillPrerequisite).where(
                    SkillPrerequisite.skill_id.in_({skill.id for skill in skills})
                )
            )
        )
        for edge in edges:
            skill = db.get(Skill, edge.skill_id)
            prereq = db.get(Skill, edge.prerequisite_skill_id)
            assert skill is not None
            assert prereq is not None
            assert skill.curriculum_id == prereq.curriculum_id


def test_canonical_skills_are_reused_across_jurisdictions():
    seed()
    with SessionLocal() as db:
        equal_groups_canonical = db.scalar(
            select(CanonicalSkill).where(
                CanonicalSkill.code == "MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS"
            )
        )
        assert equal_groups_canonical is not None
        mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.canonical_skill_id == equal_groups_canonical.id
                )
            )
        )
        skill_ids = {m.skill_id for m in mappings}
        skills = list(db.scalars(select(Skill).where(Skill.id.in_(skill_ids))))
        jurisdictions = {
            db.get(Curriculum, skill.curriculum_id).jurisdiction for skill in skills
        }
        assert len(jurisdictions) >= 2
        assert len({skill.curriculum_id for skill in skills}) == len(skills)


def test_skill_codes_are_unique_per_curriculum():
    seed()
    with SessionLocal() as db:
        curricula = list(db.scalars(select(Curriculum)))
        for curriculum in curricula:
            skill_codes = list(
                db.scalars(
                    select(Skill.code).where(Skill.curriculum_id == curriculum.id)
                )
            )
            assert len(skill_codes) == len(set(skill_codes))


def test_grades_1_2_misconception_catalog_is_valid():
    catalog = json.loads(_MISCONCEPTION_CATALOG.read_text())
    assert catalog["version"]
    assert catalog["catalog"]
    for canonical_code, entry in catalog["catalog"].items():
        assert canonical_code.startswith("MATH.ELEMENTARY.")
        for m in entry["misconceptions"]:
            assert m["code"]
            assert m["name"]
            assert m["diagnostic_pattern"]
            assert m["remediation"]


def test_grades_1_2_misconceptions_map_to_loaded_canonical_skills():
    seed()
    catalog = json.loads(_MISCONCEPTION_CATALOG.read_text())
    canonical_codes = set(catalog["catalog"].keys())
    with SessionLocal() as db:
        loaded_codes = set(
            db.scalars(select(CanonicalSkill.code).where(CanonicalSkill.code.in_(canonical_codes)))
        )
        assert loaded_codes == canonical_codes
