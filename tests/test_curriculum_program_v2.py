"""V2 program planner tests (offline, no model/network, no learner DB)."""
import pytest

from scripts.curriculum_program_v2 import (
    connect, import_manifest, next_task, parse_goal, register_goal, transition,
)


def sample_manifest():
    return {
        "verification_state": "SOURCE_REVIEWED",
        "reviewer_identity": "Independent Standards Review",
        "review_evidence_url": "https://github.com/AyalewGM/ai-tutor/issues/278",
        "expectations": [
            {"grade": 9, "course_code": "MTH1W", "expectation_code": "C1.5",
             "source_version": "2021",
             "official_source_url": "https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w/c/c1"}
        ],
    }


def test_full_ontario_goal_is_program_not_fake_12_course_list(tmp_path):
    with connect(tmp_path / "v2.db") as db:
        goal = register_goal(db, "I want full Ontario mathematics curriculum, grades 1-12")
        assert goal["goal"]["grades"] == list(range(1, 13))
        assert goal["state"] == "AWAITING_OFFICIAL_SOURCE_INVENTORY"
        assert goal["work_items"] == 0
        assert next_task(db, goal["program_id"]) is None


def test_source_review_and_durable_idempotent_import(tmp_path):
    path = tmp_path / "v2.db"
    with connect(path) as db:
        program = register_goal(db, "Ontario mathematics Grades 9-12")
        with pytest.raises(PermissionError):
            import_manifest(db, program["program_id"],
                            {**sample_manifest(), "verification_state": "UNVERIFIED"})
        first = import_manifest(db, program["program_id"], sample_manifest())
        second = import_manifest(db, program["program_id"], sample_manifest())
        assert first["total"] == second["total"] == 1
    with connect(path) as db:
        task = next_task(db, program["program_id"])
        assert task["expectation_code"] == "C1.5"
        assert task["grade"] == 9


def test_review_cannot_skip_implementation_or_self_release(tmp_path):
    with connect(tmp_path / "v2.db") as db:
        program = register_goal(db, "Ontario mathematics Grades 9-12")
        import_manifest(db, program["program_id"], sample_manifest())
        task_id = next_task(db, program["program_id"])["id"]
        evidence = "https://github.com/AyalewGM/ai-tutor/pull/484"
        with pytest.raises(ValueError):
            transition(db, task_id, "APPROVED", "author", evidence, 0)
        first = transition(db, task_id, "IN_PROGRESS", "content-owner", evidence, 0)
        assert first["content_runtime_activated"] is False
        with pytest.raises(ValueError):
            transition(db, task_id, "REVIEW_REQUIRED", "content-owner", evidence, 0)
        transition(db, task_id, "REVIEW_REQUIRED", "content-owner", evidence, 1)
        approved = transition(db, task_id, "APPROVED", "reviewer", evidence, 2)
        assert approved["content_runtime_activated"] is False
        with pytest.raises(ValueError):
            transition(db, task_id, "IN_PROGRESS", "author", evidence, 3)
        count = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        assert count == 3


@pytest.mark.parametrize("text", [
    "Ontario math grades 0-12",
    "Ontario math grades 12-1",
    "Maryland mathematics grades 1-12",
    "Ontario mathematics grades 1-20",
])
def test_unrecognized_or_impossible_scope_fails_closed(text):
    with pytest.raises(ValueError):
        parse_goal(text)


def test_no_extraneous_grades_or_dishonest_source_state(tmp_path):
    with connect(tmp_path / "v2.db") as db:
        program = register_goal(db, "Ontario mathematics Grades 9-9")
        manifest = sample_manifest()
        manifest["expectations"][0]["grade"] = 10
        with pytest.raises(ValueError):
            import_manifest(db, program["program_id"], manifest)
