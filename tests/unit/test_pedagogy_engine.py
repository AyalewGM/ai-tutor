from app.services import misconceptions, pedagogy_engine, stepwork


def _step(status: str, code: str | None = None) -> dict:
    return {"step_status": status, "misconception_code": code}


def test_two_consecutive_invalid_steps_downgrade_to_pictorial() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state(
        [_step("invalid", "EQ_001"), _step("invalid", "EQ_001")]
    )
    assert state.cpa_level == "PICTORIAL"
    assert state.cpa_changed
    assert state.misconception_tag == "EQ_001"


def test_pictorial_escalates_to_concrete_on_further_failures() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state(
        [_step("invalid"), _step("invalid"), _step("invalid"), _step("invalid")],
        prior_cpa="PICTORIAL",
    )
    assert state.cpa_level == "CONCRETE"


def test_single_invalid_does_not_downgrade() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state([_step("invalid")])
    assert state.cpa_level == "ABSTRACT"
    assert not state.cpa_changed


def test_valid_streak_recovers_one_level() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state(
        [_step("invalid"), _step("invalid"), _step("valid"), _step("valid")],
        prior_cpa="PICTORIAL",
    )
    assert state.cpa_level == "ABSTRACT"


def test_solved_promotes_from_pictorial() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state(
        [_step("valid"), _step("solved")], prior_cpa="PICTORIAL"
    )
    assert state.cpa_level == "ABSTRACT"


def test_tag_clears_after_recovery() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state(
        [_step("invalid", "DIST_002"), _step("valid")]
    )
    assert state.misconception_tag is None


def test_reverse_socratic_triggers_after_three_valid_steps() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state(
        [_step("valid"), _step("valid"), _step("valid")]
    )
    assert state.trigger_reverse_socratic


def test_reverse_socratic_needs_three_and_not_when_pending() -> None:
    assert not pedagogy_engine.evaluate_pedagogical_state(
        [_step("valid"), _step("valid")]
    ).trigger_reverse_socratic
    assert not pedagogy_engine.evaluate_pedagogical_state(
        [_step("valid")] * 4, challenge_pending=True
    ).trigger_reverse_socratic


def test_no_challenge_after_problem_solved() -> None:
    state = pedagogy_engine.evaluate_pedagogical_state(
        [_step("valid"), _step("valid"), _step("solved")]
    )
    assert not state.trigger_reverse_socratic


def test_craft_flawed_step_moves_constant_without_sign_flip() -> None:
    assert pedagogy_engine.craft_flawed_step("3x + 12 = 30") == ("3x = 42", "EQ_001")
    assert pedagogy_engine.craft_flawed_step("3x - 5 = 16") == ("3x = 11", "EQ_001")


def test_craft_flawed_step_multiplies_instead_of_dividing() -> None:
    assert pedagogy_engine.craft_flawed_step("3x = 18") == ("x = 54", "EQ_003")


def test_craft_flawed_step_returns_none_when_nothing_to_corrupt() -> None:
    assert pedagogy_engine.craft_flawed_step("x = 6") is None
    assert pedagogy_engine.craft_flawed_step("2 + 2") is None


def test_planted_lines_are_detected_by_the_real_classifier() -> None:
    # The flawed lines we present must carry the authentic misconception code,
    # so a learner who copies one is classified honestly.
    for line, code in (("3x + 12 = 30", "3x = 42"), ("3x = 18", "x = 54")):
        flawed, _ = pedagogy_engine.craft_flawed_step(line)
        result = stepwork.check_step(line, [line], flawed, 0)
        assert result.status == "invalid"
        assert result.misconception_code is not None


def test_line_matches_equivalent_equations() -> None:
    assert pedagogy_engine.line_matches("x = 36", "x=36")
    assert not pedagogy_engine.line_matches("x = 36", "x = 4")


def test_every_emitted_code_has_a_taxonomy_profile() -> None:
    for code in stepwork._ERROR_FEEDBACK:
        profile = misconceptions.profile_for(code)
        assert profile is not None, code
        assert profile.socratic_hint


def test_visual_cues_reference_real_renderer_types() -> None:
    known = {
        "balance_scale",
        "area_model",
        "fraction_operation",
        "tape_diagram",
        "number_line",
    }
    for code, profile in misconceptions.TAXONOMY.items():
        assert profile.visual_cue is None or profile.visual_cue in known, code
