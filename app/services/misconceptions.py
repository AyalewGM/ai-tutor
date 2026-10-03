"""Central misconception taxonomy (step-level codes).

Every deterministic step checker emits a small closed set of codes into
``TutorTurn.metadata_json["misconception_code"]``. This module is the single
place that attaches pedagogy to those codes: a catalog name (mirroring the
``misconceptions`` table convention), a Socratic hint for the tutor voice,
and a preferred visual cue for CPA PICTORIAL/CONCRETE presentation.

External spec names map onto these canonical codes: ``ERR_DISTRIBUTIVE_NEG``
is ``DIST_002``, ``ERR_FRACTION_ADD_DENOM`` is ``NUM_003``/``FRAC_001``, and
``ERR_SIGN_FLIP_INEQUALITY``-family errors are ``EQ_001``/``EQ_003``.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MisconceptionProfile:
    """Pedagogical profile for one misconception code.

    ``socratic_hint`` must surface the learner's error as a question — never
    name the correct move. ``visual_cue`` is a ``visualization.py`` spec type
    (``balance_scale``, ``fraction_operation``, ``area_model``,
    ``tape_diagram``, ``number_line``) or None when no honest visual exists.
    """

    name: str
    socratic_hint: str
    visual_cue: str | None = None


TAXONOMY: dict[str, MisconceptionProfile] = {
    "EQ_001": MisconceptionProfile(
        name="Inverse operation applied in the wrong direction",
        socratic_hint="If a term was added to build this side, which operation undoes it — and what must happen on the other side?",
        visual_cue="balance_scale",
    ),
    "EQ_002": MisconceptionProfile(
        name="Operation applied to only one side",
        socratic_hint="You changed one side. What keeps the two pans of a balance level?",
        visual_cue="balance_scale",
    ),
    "EQ_003": MisconceptionProfile(
        name="Coefficient undone by multiplying instead of dividing",
        socratic_hint="3x means three times x. Which operation undoes a multiplication?",
        visual_cue="balance_scale",
    ),
    "EQ_004": MisconceptionProfile(
        name="Coefficient removed by subtraction",
        socratic_hint="Is 3x made by adding 3 to x, or multiplying x by 3? What undoes that operation?",
        visual_cue="balance_scale",
    ),
    "ARITH_001": MisconceptionProfile(
        name="Arithmetic slip after a legal move",
        socratic_hint="Your move was legal — recheck the arithmetic on the side you changed.",
        visual_cue=None,
    ),
    "DIST_001": MisconceptionProfile(
        name="Factor not distributed to every term",
        socratic_hint="How many terms sit inside the parentheses, and how many did the factor reach?",
        visual_cue="area_model",
    ),
    "DIST_002": MisconceptionProfile(
        name="Distributive multiplication drops a negative sign",
        socratic_hint="The factor touches the negative term too. What sign does that product carry?",
        visual_cue="area_model",
    ),
    "ALG_001": MisconceptionProfile(
        name="Unlike terms combined",
        socratic_hint="Which terms share the same variable part — and which ones don't?",
        visual_cue=None,
    ),
    "ALG_002": MisconceptionProfile(
        name="Term sign dropped while rearranging",
        socratic_hint="Each term keeps the sign in front of it. Which sign moved when you rewrote the expression?",
        visual_cue=None,
    ),
    "NUM_003": MisconceptionProfile(
        name="Fractions added straight across denominators",
        socratic_hint="Are the pieces the same size? What denominator would make them match?",
        visual_cue="fraction_operation",
    ),
    "FRAC_001": MisconceptionProfile(
        name="Common denominator found but numerators not scaled",
        socratic_hint="Each numerator must scale by the same factor as its denominator — which one didn't?",
        visual_cue="fraction_operation",
    ),
    "WP_001": MisconceptionProfile(
        name="Numbers placed in the wrong roles",
        socratic_hint="Point to where each number from the story lands in your equation.",
        visual_cue="tape_diagram",
    ),
}


def profile_for(code: str | None) -> MisconceptionProfile | None:
    """Return the pedagogical profile for a checker-emitted code."""
    if not code:
        return None
    return TAXONOMY.get(code)


def socratic_hint(code: str | None) -> str | None:
    """Question-form hint for a code; None when the code is unknown."""
    profile = profile_for(code)
    return profile.socratic_hint if profile else None


def visual_cue(code: str | None) -> str | None:
    """Preferred visualization spec type for a code, if one exists."""
    profile = profile_for(code)
    return profile.visual_cue if profile else None
