from app.workspace_api import build_learn_content


def test_guided_interactions_are_allowlisted_for_the_workspace_contract() -> None:
    content = {
        "summary": "Integer addition lesson",
        "examples": [],
        "guided_interactions": [
            "MATH.INT.ADD",
            "MATH.INT.SUB",
            "Signed Number Operations",
        ],
    }

    learn = build_learn_content(content)

    assert learn is not None
    assert learn.guided_interactions == ["MATH.INT.ADD"]


def test_malformed_guided_interactions_fail_closed() -> None:
    content = {
        "summary": "Integer addition lesson",
        "examples": [],
        "guided_interactions": "MATH.INT.ADD",
    }

    learn = build_learn_content(content)

    assert learn is not None
    assert learn.guided_interactions == []
