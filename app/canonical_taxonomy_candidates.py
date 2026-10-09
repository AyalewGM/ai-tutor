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
    version="0.1.0-candidates",
    skills={
        "MATH.ARITHMETIC.ADD_SUB_WITHIN_20": CanonicalSkillDefinition(
            code="MATH.ARITHMETIC.ADD_SUB_WITHIN_20",
            name="Add and subtract within 20",
            description=(
                "Compute sums and differences of nonnegative whole numbers "
                "with results and operands within 20."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.ARITHMETIC.WORD_PROBLEM_WITHIN_20": CanonicalSkillDefinition(
            code="MATH.ARITHMETIC.WORD_PROBLEM_WITHIN_20",
            name="One-step addition and subtraction word problems within 20",
            description=(
                "Represent and solve one-step joining, separating, combining "
                "or comparing situations with whole-number quantities within 20."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120": CanonicalSkillDefinition(
            code="MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120",
            name="Count and compare whole numbers to 120",
            description=(
                "Count whole numbers up to 120 and compare quantities "
                "using order and magnitude."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
        "MATH.PLACE_VALUE.TENS_ONES": CanonicalSkillDefinition(
            code="MATH.PLACE_VALUE.TENS_ONES",
            name="Understand tens and ones",
            description=(
                "Represent two-digit whole numbers as groups of tens and "
                "individual ones and interpret each digit's place value."
            ),
            review_state=SkillReviewState.DRAFT,
        ),
    },
)
