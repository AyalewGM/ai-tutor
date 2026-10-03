import json

from app.services import chat_cpa


def _block(payload: dict) -> str:
    return "```json:cpa\n" + json.dumps(payload) + "\n```"


_VALID_BALANCE = {
    "type": "BALANCE_SCALE",
    "title": "Unbalanced",
    "balanceScale": {
        "leftExpr": "2x",
        "rightExpr": "11",
        "leftValue": 8,
        "rightValue": 11,
    },
}
_VALID_BARS = {
    "type": "FRACTION_BARS",
    "fractionBars": [{"numerator": 2, "denominator": 4, "label": "2/4"}],
}


def test_valid_block_survives_and_prose_is_untouched() -> None:
    message = f"Good question.\n\n{_block(_VALID_BALANCE)}"
    out = chat_cpa.sanitize_cpa_blocks(message, canonical_answer="x=4")
    assert out == message


def test_malformed_block_is_stripped_cleanly() -> None:
    message = "Look here.\n\n```json:cpa\n{not json\n```\n\nTry again."
    out = chat_cpa.sanitize_cpa_blocks(message)
    assert "json:cpa" not in out
    assert "{not json" not in out
    assert "Look here." in out and "Try again." in out


def test_only_first_valid_block_survives() -> None:
    message = (
        f"Text.\n\n{_block({'type': 'UNKNOWN'})}\n"
        f"{_block(_VALID_BALANCE)}\n{_block(_VALID_BARS)}"
    )
    out = chat_cpa.sanitize_cpa_blocks(message)
    assert out.count("```json:cpa") == 1
    assert "BALANCE_SCALE" in out  # first *valid* wins


def test_balance_scale_revealing_solution_is_stripped() -> None:
    leaky = {
        "type": "BALANCE_SCALE",
        "balanceScale": {"leftExpr": "x", "rightExpr": "4", "leftValue": 4, "rightValue": 4},
    }
    message = f"See?\n\n{_block(leaky)}"
    out = chat_cpa.sanitize_cpa_blocks(message, canonical_answer="x=4")
    assert "json:cpa" not in out


def test_fraction_bar_showing_simplified_form_is_not_a_leak() -> None:
    # A '1/2' bar inside an equivalence visual is content, not the answer —
    # the guard only applies to solved-equation balance scales.
    message = _block(_VALID_BARS)
    out = chat_cpa.sanitize_cpa_blocks(message, canonical_answer="1/2")
    assert "json:cpa" in out


def test_tagged_block_variant_is_sanitized_too() -> None:
    message = "<cpa_visual>\n" + json.dumps(_VALID_BALANCE) + "\n</cpa_visual>"
    assert "cpa_visual" in chat_cpa.sanitize_cpa_blocks(message)
    bad = "<cpa_visual>\n{bad\n</cpa_visual>"
    assert "cpa_visual" not in chat_cpa.sanitize_cpa_blocks(bad)


def test_plain_message_passes_through() -> None:
    assert chat_cpa.sanitize_cpa_blocks("just words") == "just words"


def test_text_reveals_answer_flags_solved_form() -> None:
    assert chat_cpa.text_reveals_answer("So x = 4 is the answer.", "x = 4")
    assert chat_cpa.text_reveals_answer("that gives x=4", "x=4")
    assert chat_cpa.text_reveals_answer("x = -4", "x = -4")


def test_text_reveals_answer_ignores_non_leaks() -> None:
    # The value appearing in working is not the solved form.
    assert not chat_cpa.text_reveals_answer("What is 8 divided by 4?", "x = 4")
    assert not chat_cpa.text_reveals_answer("check: 2x = 8", "x = 4")
    # Bare numeric canonicals are skipped entirely — too many false hits.
    assert not chat_cpa.text_reveals_answer("the answer is 8", "8")
    # A solved form inside a stripped CPA block doesn't count as prose.
    leaky = _block(
        {
            "type": "BALANCE_SCALE",
            "balanceScale": {"leftExpr": "x = 4", "rightExpr": "4"},
        }
    )
    assert not chat_cpa.text_reveals_answer(f"Look: {leaky}", "x = 4")


def test_field_hardening_rejects_unsafe_values() -> None:
    bad_color = {
        "type": "FRACTION_BARS",
        "fractionBars": [{"numerator": 1, "denominator": 2, "color": "url(evil)"}],
    }
    assert "json:cpa" not in chat_cpa.sanitize_cpa_blocks(_block(bad_color))

    bad_den = {
        "type": "FRACTION_BARS",
        "fractionBars": [{"numerator": 1, "denominator": 5000}],
    }
    assert "json:cpa" not in chat_cpa.sanitize_cpa_blocks(_block(bad_den))

    long_label = {
        "type": "FRACTION_BARS",
        "fractionBars": [{"numerator": 1, "denominator": 2, "label": "x" * 100}],
    }
    assert "json:cpa" not in chat_cpa.sanitize_cpa_blocks(_block(long_label))

    huge_scale = {
        "type": "BALANCE_SCALE",
        "balanceScale": {"leftExpr": "2x", "rightExpr": "11", "leftValue": 1e12},
    }
    assert "json:cpa" not in chat_cpa.sanitize_cpa_blocks(_block(huge_scale))


def test_hardening_still_accepts_contract_colors() -> None:
    payload = {
        "type": "FRACTION_BARS",
        "title": "Equivalence",
        "fractionBars": [
            {"numerator": 2, "denominator": 4, "label": "2/4", "color": "bg-indigo-500"},
            {"numerator": 1, "denominator": 2, "color": "#10b981"},
        ],
    }
    assert "json:cpa" in chat_cpa.sanitize_cpa_blocks(_block(payload))
