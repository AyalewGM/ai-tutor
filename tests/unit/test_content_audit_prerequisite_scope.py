"""Exercise the real persisted-record audit with ORM objects and no database."""
import unittest
import uuid

from app.content_audit import audit_curriculum_isolation
from app.content_models import CurriculumExpectation, ExpectationSkillMapping, ProblemContentMetadata
from app.content_validation import ContentValidationError
from app.models import Curriculum, Skill, SkillPrerequisite


class MemoryAuditSession:
    """Only the read operations used by the isolation audit; never opens a DB."""

    def __init__(self, curricula, skills, edges):
        self.records = {
            Curriculum: curricula,
            Skill: skills,
            SkillPrerequisite: edges,
            CurriculumExpectation: [],
            ExpectationSkillMapping: [],
            ProblemContentMetadata: [],
        }

    def get(self, model, record_id):
        return next((row for row in self.records[model] if row.id == record_id), None)

    def scalars(self, statement):
        model = statement.column_descriptions[0]["entity"]
        rows = self.records[model]
        # The audit's initial skill/expectation reads select one curriculum.
        criterion = statement.whereclause
        if criterion is not None:
            rows = [row for row in rows if row.curriculum_id == criterion.right.value]
        return ScalarRows(rows)


class ScalarRows:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class PrerequisiteScopeAuditTests(unittest.TestCase):
    def setUp(self):
        self.authority = uuid.uuid4()
        self.audited = self.curriculum(grade="9")
        self.selected_skill = self.skill(self.audited)

    def curriculum(self, *, grade="8", **changes):
        values = dict(id=uuid.uuid4(), code=f"TEST-{grade}", name="Synthetic curriculum",
                      active=True, jurisdiction="Ontario", authority_id=self.authority,
                      version="2026", grade_level=grade)
        values.update(changes)
        return Curriculum(**values)

    def skill(self, curriculum):
        return Skill(id=uuid.uuid4(), curriculum_id=curriculum.id, code="TEST.SKILL",
                     name="Synthetic skill", difficulty_level=1)

    def audit_edge(self, other_curriculum, *, incoming=False, touching=True):
        other_skill = self.skill(other_curriculum)
        endpoint = self.selected_skill if touching else self.skill(other_curriculum)
        skill, prerequisite = (other_skill, endpoint) if incoming else (endpoint, other_skill)
        session = MemoryAuditSession(
            [self.audited, other_curriculum], [self.selected_skill, other_skill, endpoint],
            [SkillPrerequisite(skill_id=skill.id, prerequisite_skill_id=prerequisite.id)],
        )
        audit_curriculum_isolation(session, curriculum_id=self.audited.id)

    def test_cross_grade_same_scope_is_allowed_in_both_directions(self):
        for incoming in (False, True):
            with self.subTest(incoming=incoming):
                self.audit_edge(self.curriculum(), incoming=incoming)

    def test_same_curriculum_is_allowed(self):
        self.audit_edge(self.audited)

    def test_matching_unspecified_authorities_are_preserved(self):
        self.audited.authority_id = None
        self.audit_edge(self.curriculum(authority_id=None))

    def test_different_authority_is_rejected_in_both_directions(self):
        for incoming in (False, True):
            with self.subTest(incoming=incoming):
                with self.assertRaisesRegex(ContentValidationError, "authority boundaries"):
                    self.audit_edge(self.curriculum(authority_id=uuid.uuid4()), incoming=incoming)

    def test_missing_authority_cannot_match_known_authority(self):
        for incoming in (False, True):
            with self.subTest(incoming=incoming):
                with self.assertRaisesRegex(ContentValidationError, "authority boundaries"):
                    self.audit_edge(self.curriculum(authority_id=None), incoming=incoming)

    def test_different_version_is_rejected_in_both_directions(self):
        for incoming in (False, True):
            with self.subTest(incoming=incoming):
                with self.assertRaisesRegex(ContentValidationError, "version boundaries"):
                    self.audit_edge(self.curriculum(version="2025"), incoming=incoming)

    def test_different_jurisdiction_is_still_rejected(self):
        for incoming in (False, True):
            with self.subTest(incoming=incoming):
                with self.assertRaisesRegex(ContentValidationError, "jurisdiction boundaries"):
                    self.audit_edge(self.curriculum(jurisdiction="Maryland"), incoming=incoming)

    def test_unrelated_edges_are_ignored(self):
        self.audit_edge(self.curriculum(authority_id=uuid.uuid4(), version="2025"), touching=False)
