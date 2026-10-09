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
    version="0.1.0-candidates-r5",
    skills={
        "MATH.ARITHMETIC.ADD_WITHIN_20": CanonicalSkillDefinition(
            code="MATH.ARITHMETIC.ADD_WITHIN_20",
            name="Add within 20",
            description=(
                "Find the sum a+b of two whole-number inputs where a>=0, b>=0, "
                "and a+b lies in the inclusive range 0–20. Include zero, "
                "crossing-ten and non-crossing-ten cases; contextual modeling, "
                "unknown-addend equations and automatic fluency are separate skills."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.ARITHMETIC.SUBTRACT_WITHIN_20": CanonicalSkillDefinition(
            code="MATH.ARITHMETIC.SUBTRACT_WITHIN_20",
            name="Subtract within 20",
            description=(
                "Find the nonnegative difference a-b of two whole-number inputs "
                "where 0<=b<=a<=20. Include zero results, crossing-ten and "
                "non-crossing-ten cases; contextual modeling, unknown-subtrahend "
                "equations and automatic fluency are separate skills."
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
        "MATH.NUMBER_SENSE.COUNT_FORWARD_BY_ONE_TO_120": CanonicalSkillDefinition(
            code="MATH.NUMBER_SENSE.COUNT_FORWARD_BY_ONE_TO_120",
            name="Count forward by ones to 120",
            description=(
                "Continue a forward-by-one whole-number sequence from a starting "
                "value in 0–119, producing one or more successors without exceeding "
                "120, including sequences that cross from 99 to 100. Backward counting, "
                "skip counting, collection counting and magnitude comparison are "
                "separate skills."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.NUMBER_SENSE.COMPARE_WHOLE_NUMBERS_TO_120": CanonicalSkillDefinition(
            code="MATH.NUMBER_SENSE.COMPARE_WHOLE_NUMBERS_TO_120",
            name="Compare whole numbers to 120",
            description=(
                "Compare two whole numbers in the inclusive range 0–120 by magnitude "
                "and represent the relationship with <, =, or >. Include zero, equal "
                "cases and pairs around 99, 100 and 120. Sequence production, ordering lists "
                "and place-value explanation are separate skills."
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
