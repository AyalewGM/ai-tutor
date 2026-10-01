from types import SimpleNamespace

from app.services.visualization import visualization_for


def _problem(problem_type: str, prompt: str):
    return SimpleNamespace(problem_type=problem_type, prompt=prompt, solution={})


def test_like_term_visual_groups_by_variable_structure():
    spec = visualization_for(_problem("COMBINE_LIKE_TERMS", "Simplify 5y + 2 - 8y."))
    assert spec is not None
    assert spec["type"] == "algebra_tiles"
    groups = {group["key"]: group["terms"] for group in spec["groups"]}
    assert [term["coefficient"] for term in groups["y^1"]] == [5, -8]
    assert [term["coefficient"] for term in groups["constant^0"]] == [2]
    assert "Only terms in the same group" in spec["aria_label"]


def test_polynomial_subtraction_visual_changes_every_right_hand_sign():
    spec = visualization_for(
        _problem("POLYNOMIAL_ADD_SUBTRACT", "Simplify (6x - 2) - (4x + 5).")
    )
    assert spec is not None
    assert spec["type"] == "polynomial_sign_change"
    assert spec["operation"] == "-"
    assert [term["coefficient"] for term in spec["right_terms"]] == [4, 5]
    assert [term["coefficient"] for term in spec["transformed_right_terms"]] == [-4, -5]
    assert all(term["sign_changed"] for term in spec["transformed_right_terms"])


def test_polynomial_addition_visual_preserves_right_hand_signs():
    spec = visualization_for(
        _problem("POLYNOMIAL_ADD_SUBTRACT", "Simplify (3x + 4) + (2x - 7).")
    )
    assert spec is not None
    assert spec["operation"] == "+"
    assert [term["coefficient"] for term in spec["transformed_right_terms"]] == [2, -7]
    assert not any(term["sign_changed"] for term in spec["transformed_right_terms"])
