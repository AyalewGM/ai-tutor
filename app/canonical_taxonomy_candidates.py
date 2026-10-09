"""Independent draft mathematical skill candidates for #282 review.

These definitions are manually authored; they are NOT synthesized from
problem generators or curriculum pack mappings. No review is implied.
"""
from app.canonical_skill_taxonomy import (
    CanonicalSkillDefinition,
    CanonicalTaxonomy,
    SkillReviewState,
)

CANDIDATE_TAXONOMY = CanonicalTaxonomy(
    version="0.1.0-candidates-r3",
    skills={
        "MATH.ARITHMETIC.ADD_SUB_WITHIN_20": CanonicalSkillDefinition(
            code="MATH.ARITHMETIC.ADD_SUB_WITHIN_20",
            name="Add and subtract within 20",
            description=(
                "Find a sum or nonnegative difference of two whole-number inputs, "
                "where each input and the result lie in the inclusive range 0–20. "
                "Addition and subtraction require separate demonstrations."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.ARITHMETIC.WORD_PROBLEM_WITHIN_20": CanonicalSkillDefinition(
            code="MATH.ARITHMETIC.WORD_PROBLEM_WITHIN_20",
            name="One-step addition and subtraction word problems within 20",
            description=(
                "Model and solve a one-operation join, separate, part-whole, or "
                "comparison story. The unknown may be the result, change, start, part, "
                "whole, difference, larger quantity, or smaller quantity. Every modeled "
                "quantity, including an inferred answer, lies in the inclusive range 0–20. "
                "Each structure and unknown role requires distinct assessment evidence."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120": CanonicalSkillDefinition(
            code="MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120",
            name="Count and compare whole numbers to 120",
            description=(
                "Draft composite placeholder pending Architecture decomposition: "
                "continue a forward-by-one whole-number sequence from an arbitrary "
                "starting value through at most 120, and independently compare two "
                "whole-number magnitudes in 0–120. Store evidence separately and do "
                "not infer either component from the other."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.PLACE_VALUE.TENS_ONES": CanonicalSkillDefinition(
            code="MATH.PLACE_VALUE.TENS_ONES",
            name="Understand tens and ones",
            description=(
                "For each two-digit number 10–99, identify its tens and ones digits, "
                "their values, and the corresponding groups of ten and units. "
                "Show that ten ones form one ten, including zero-ones cases."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
    },
)
