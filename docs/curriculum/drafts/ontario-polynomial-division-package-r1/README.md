# Ontario polynomial division learning package R2

This draft turns the exact polynomial/monomial quotient generators from PR #344
into one coherent review package. It is original Mihur content derived from the
question-type handoff in Issue #337; no teacher worksheet wording or identifying
information is stored here.

The package teaches why every term in a grouped polynomial must be divided by
the same nonzero monomial. Learners first inspect a common factor, predict signs
and remaining factor counts, manipulate grouped term cards, explain cancellation,
practice with exact variants, receive response-specific Socratic repair, transfer
the reasoning to a composite-area model, and finish with a fresh hidden variant.

R2 adds the proposed `poly-division-evidence-v1` response contract. Exact
coefficients travel as reduced rational strings; quotient terms are compared in
canonical order; coefficient and exponent explanations are bounded enum evidence;
and every quotient term carries an exact quotient × divisor = original dividend
reconstruction record. The composite-area transfer now has a complete oracle for
both width terms, total width, original-domain restrictions, multiplication
checks, and units. The exponent-addition repair deterministically searches for a
fresh exit with at least one negative result exponent and fails closed if the
bounded search cannot produce one.

These checks are a package-level review model only. They do not replace a
backend-trusted scorer, do not grant partial or mastery credit, and do not write
learner evidence. PR #346 compatibility and acceptance remain owned by Assessment
Backend, Mathematical Review, and Engineering Lead.

The package is `DRAFT_UNVERIFIED` and runtime-disabled. The grouped-term
manipulator is an accessibility/MVE contract, not a routed component. Frontend,
backend scoring, mathematical review, standards review, pedagogical review, and
Muse QA remain independent owner gates.

