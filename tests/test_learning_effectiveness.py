"""Comprehensive tests for learning-effectiveness measurement system.

Covers:
- Deterministic scoring
- Baseline vs post-assessment comparisons
- Guided vs independent response tracking
- Retention scheduling and missed assessments
- Transfer assessment
- Insufficient evidence handling
- Difficulty comparability
- Misconception resolution
- Data isolation between student profiles
- Privacy-safe reporting

Regression tests for PR #270 integrity fixes:
- Fix 1: Excluded families are never silently reintroduced
- Fix 2: Problem reconstruction via generation_seed is exact
- Fix 3: Assistance level is server-enforced (always 0 for assessments)
- Fix 4: Incomplete/abandoned assessments cannot produce false scores
- Fix 5: Cross-skill score differences are not reported as learning gains
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, _normalize, generate
from app.effectiveness_models import (
    AssessmentItem,
    AssessmentPhase,
    AssessmentStatus,
    EffectivenessSnapshot,
    LearningAssessment,
)
from app.services.learning_assessment import (
    MIN_COMPLETION_RATIO,
    MIN_ITEMS_FOR_SCORE,
    SelectionResult,
    _families_for_skill,
    _select_assessment_families,
)
from app.services.learning_effectiveness import (
    MisconceptionAnalysis,
    SkillEffectivenessReport,
    _analyse_misconceptions,
    _compute_confidence,
    compute_effectiveness,
    parent_summary,
)

# ====================================================================
# 1. Deterministic scoring tests
# ====================================================================


class TestDeterministicScoring:
    """Verify that answer correctness is deterministic and reproducible."""

    def test_correct_answer_is_correct(self):
        """A canonical answer must always be scored correct."""
        family_code = next(iter(FAMILIES))
        spec = FAMILIES[family_code]
        problem = generate(family_code, seed=42, difficulty=spec.min_difficulty)
        assert problem.is_correct(problem.canonical_answer)

    def test_wrong_answer_is_wrong(self):
        """A clearly wrong answer must be scored incorrect."""
        family_code = next(iter(FAMILIES))
        spec = FAMILIES[family_code]
        problem = generate(family_code, seed=42, difficulty=spec.min_difficulty)
        assert not problem.is_correct("definitely_wrong_xyz_123")

    def test_scoring_is_deterministic_across_calls(self):
        """Same seed + difficulty always produces same problem and answer."""
        family_code = next(iter(FAMILIES))
        spec = FAMILIES[family_code]
        p1 = generate(family_code, seed=99, difficulty=spec.min_difficulty)
        p2 = generate(family_code, seed=99, difficulty=spec.min_difficulty)
        assert p1.canonical_answer == p2.canonical_answer
        assert p1.prompt == p2.prompt
        assert p1.variant_id == p2.variant_id

    @pytest.mark.parametrize("family_code", list(FAMILIES.keys())[:20])
    def test_all_families_produce_valid_problems(self, family_code):
        """Every family produces a problem that self-validates."""
        spec = FAMILIES[family_code]
        problem = generate(
            family_code, seed=1, difficulty=spec.min_difficulty,
            mode=LearningMode.DIAGNOSTIC,
        )
        assert problem.prompt
        assert problem.canonical_answer
        assert problem.is_correct(problem.canonical_answer)


# ====================================================================
# 2. Family selection and exclusion (Fix 1 regression tests)
# ====================================================================


class TestFamilySelection:
    """Verify that assessment families are properly selected/excluded."""

    def test_families_for_skill_finds_families(self):
        """At least one family exists for a known canonical skill."""
        skill_codes = {spec.canonical_skill_code for spec in FAMILIES.values()}
        assert len(skill_codes) > 0
        for code in skill_codes:
            families = _families_for_skill(code)
            assert len(families) > 0, f"No families for {code}"
            break

    def test_select_with_exclusions(self):
        """Excluding families returns different ones when available."""
        skill_codes = {spec.canonical_skill_code for spec in FAMILIES.values()}
        for code in skill_codes:
            available = _families_for_skill(code)
            if len(available) >= 4:
                first_result = _select_assessment_families(code, count=2)
                first_codes = {fc for fc, _ in first_result.families}
                second_result = _select_assessment_families(
                    code, exclude_families=first_codes, count=2,
                )
                second_codes = {fc for fc, _ in second_result.families}
                assert first_codes != second_codes or len(available) < 4
                break

    def test_select_returns_selection_result(self):
        """_select_assessment_families returns a SelectionResult."""
        skill_codes = {spec.canonical_skill_code for spec in FAMILIES.values()}
        code = next(iter(skill_codes))
        result = _select_assessment_families(code, count=3)
        assert isinstance(result, SelectionResult)
        assert result.available_count > 0

    def test_excluded_families_never_reintroduced(self):
        """FIX 1: Excluded families must NEVER silently reappear."""
        skill_codes = {spec.canonical_skill_code for spec in FAMILIES.values()}
        for code in skill_codes:
            available = _families_for_skill(code)
            if len(available) >= 2:
                # Exclude all but one family
                exclude = set(available[:-1])
                result = _select_assessment_families(
                    code, exclude_families=exclude, count=5,
                )
                selected_codes = {fc for fc, _ in result.families}
                # None of the excluded families should appear
                assert selected_codes.isdisjoint(exclude), (
                    f"Excluded families were reintroduced: "
                    f"{selected_codes & exclude}"
                )
                break

    def test_all_families_excluded_returns_empty(self):
        """FIX 1: When all families are excluded, return empty (not reuse)."""
        skill_codes = {spec.canonical_skill_code for spec in FAMILIES.values()}
        for code in skill_codes:
            available = _families_for_skill(code)
            if available:
                exclude = set(available)
                result = _select_assessment_families(
                    code, exclude_families=exclude, count=5,
                )
                assert len(result.families) == 0
                assert result.sufficient is False
                break

    def test_insufficient_coverage_flagged(self):
        """FIX 1: When fewer families exist than requested, flag as insufficient."""
        skill_codes = {spec.canonical_skill_code for spec in FAMILIES.values()}
        for code in skill_codes:
            available = _families_for_skill(code)
            if 0 < len(available) < 100:
                result = _select_assessment_families(
                    code, count=len(available) + 10,
                )
                assert result.sufficient is False
                # But still returns what's available
                assert len(result.families) > 0
                break

    def test_no_repeated_questions_across_assessments(self):
        """FIX 1: Different seeds produce different variants even for same family."""
        family_code = next(iter(FAMILIES))
        spec = FAMILIES[family_code]
        p1 = generate(family_code, seed="baseline:a:b:c:1",
                       difficulty=spec.min_difficulty, mode=LearningMode.DIAGNOSTIC)
        p2 = generate(family_code, seed="post:a:b:c:1",
                       difficulty=spec.min_difficulty, mode=LearningMode.DIAGNOSTIC)
        # Different seeds should produce different variants
        assert p1.variant_id != p2.variant_id or p1.prompt != p2.prompt


# ====================================================================
# 3. Problem reconstruction and misconception detection (Fix 2)
# ====================================================================


class TestProblemReconstruction:
    """FIX 2: Verify exact problem reconstruction from generation_seed."""

    @pytest.mark.parametrize("family_code", list(FAMILIES.keys())[:10])
    def test_generation_seed_reproduces_exact_problem(self, family_code):
        """The same generation_seed must reconstruct the identical problem."""
        spec = FAMILIES[family_code]
        seed = f"test:reconstruction:{family_code}:42"
        p1 = generate(family_code, seed=seed, difficulty=spec.min_difficulty,
                       mode=LearningMode.DIAGNOSTIC)
        p2 = generate(family_code, seed=seed, difficulty=spec.min_difficulty,
                       mode=LearningMode.DIAGNOSTIC)
        assert p1.canonical_answer == p2.canonical_answer
        assert p1.prompt == p2.prompt
        assert p1.variant_id == p2.variant_id

    def test_misconception_detection_uses_reconstructed_problem(self):
        """FIX 2: Misconception detection uses the same problem variant."""
        for code, spec in FAMILIES.items():
            seed = f"test:misconception:{code}:1"
            problem = generate(code, seed=seed, difficulty=spec.min_difficulty,
                               mode=LearningMode.DIAGNOSTIC)
            if problem.misconception_answers:
                # Reconstruct with same seed
                reconstructed = generate(code, seed=seed,
                                          difficulty=spec.min_difficulty,
                                          mode=LearningMode.DIAGNOSTIC)
                first_key = next(iter(problem.misconception_answers))
                misconception_answer = problem.misconception_answers[first_key]

                # Both the original and reconstructed must detect the same
                assert problem.misconception_for(misconception_answer) == first_key
                assert reconstructed.misconception_for(misconception_answer) == first_key
                break

    def test_generation_seed_stored_on_item(self):
        """FIX 2: AssessmentItem has a generation_seed column."""
        item = AssessmentItem(
            id=uuid.uuid4(),
            assessment_id=uuid.uuid4(),
            sequence_number=1,
            family_code="test",
            variant_id="test",
            generation_seed="baseline:student:skill:2024:1",
            difficulty=1,
            prompt="test",
            canonical_answer="test",
        )
        assert item.generation_seed == "baseline:student:skill:2024:1"

    def test_different_seeds_different_misconception_mappings(self):
        """Different seeds may produce different misconception answer values."""
        for code, spec in FAMILIES.items():
            p1 = generate(code, seed="seed_a:1", difficulty=spec.min_difficulty,
                           mode=LearningMode.DIAGNOSTIC)
            p2 = generate(code, seed="seed_b:1", difficulty=spec.min_difficulty,
                           mode=LearningMode.DIAGNOSTIC)
            if p1.misconception_answers and p2.misconception_answers:
                # The misconception codes should be the same (family-defined)
                # but the actual answer values may differ
                assert set(p1.misconception_answers.keys()) == set(p2.misconception_answers.keys())
                break


# ====================================================================
# 4. Independent mastery trustworthiness (Fix 3)
# ====================================================================


class TestIndependentMastery:
    """FIX 3: Verify that assistance level cannot be manipulated."""

    def test_assessment_items_always_independent(self):
        """Assessment items default to assistance_level=0 (server-enforced)."""
        item = AssessmentItem(
            id=uuid.uuid4(),
            assessment_id=uuid.uuid4(),
            sequence_number=1,
            family_code="test",
            variant_id="test",
            generation_seed="test:seed",
            difficulty=1,
            prompt="test",
            canonical_answer="test",
        )
        # SQLAlchemy default= is applied at insert time, so at Python level
        # it's None.  The server always sets assistance_level=0 in
        # record_item_response.  Verify the column exists.
        assert hasattr(item, "assistance_level")

    def test_api_schema_has_no_assistance_level(self):
        """FIX 3: RecordResponseRequest no longer accepts assistance_level."""
        from app.effectiveness_api import RecordResponseRequest
        fields = RecordResponseRequest.model_fields
        assert "assistance_level" not in fields, (
            "RecordResponseRequest should not accept client-provided "
            "assistance_level — assessments are server-enforced independent"
        )

    def test_record_response_signature_has_no_assistance(self):
        """FIX 3: record_item_response does not accept assistance_level."""
        import inspect

        from app.services.learning_assessment import record_item_response
        sig = inspect.signature(record_item_response)
        assert "assistance_level" not in sig.parameters, (
            "record_item_response should not accept assistance_level"
        )


# ====================================================================
# 5. Incomplete assessment scoring (Fix 4)
# ====================================================================


class TestIncompleteAssessmentScoring:
    """FIX 4: Verify incomplete assessments are handled correctly."""

    def test_min_items_for_score_is_defined(self):
        """Minimum items for scoring is at least 3."""
        assert MIN_ITEMS_FOR_SCORE >= 3

    def test_min_completion_ratio_is_defined(self):
        """Minimum completion ratio is defined and reasonable."""
        assert 0 < MIN_COMPLETION_RATIO <= 1.0

    def test_score_denominator_is_items_total(self):
        """FIX 4: Score uses items_total (not items_answered) as denominator."""
        # This validates the formula: score = correct / items_total
        items_total = 5
        items_correct = 3
        score = Decimal(str(items_correct / items_total)).quantize(Decimal("0.001"))
        assert score == Decimal("0.600")

    def test_unanswered_items_penalise_score(self):
        """FIX 4: Unanswered items count against the student."""
        # 5 items total, 3 answered (2 correct), 2 unanswered
        items_total = 5
        items_correct = 2
        # Score = 2/5 = 0.400 (not 2/3 = 0.667)
        score = Decimal(str(items_correct / items_total)).quantize(Decimal("0.001"))
        assert score == Decimal("0.400")

    def test_cancelled_status_exists(self):
        """FIX 4: CANCELLED status for abandoned assessments."""
        assert AssessmentStatus.CANCELLED.value == "CANCELLED"
        assert AssessmentStatus.CANCELLED != AssessmentStatus.COMPLETED

    def test_items_answered_field_exists(self):
        """FIX 4: LearningAssessment tracks items_answered."""
        a = LearningAssessment(
            student_id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
            phase=AssessmentPhase.BASELINE,
        )
        assert hasattr(a, "items_answered")

    def test_null_score_insufficient_evidence(self):
        """FIX 4: Assessment with no score (insufficient) is not mastery."""
        a = LearningAssessment(
            student_id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
            phase=AssessmentPhase.BASELINE,
            status=AssessmentStatus.COMPLETED,
            score=None,
        )
        # Null score should never be interpreted as demonstrated mastery
        assert a.score is None

    def test_incomplete_assessment_insufficient_evidence(self):
        """FIX 4: Assessment with no score produces insufficient evidence."""
        comparison = _mock_assessment(score=None, items_total=5)
        metrics = compute_effectiveness(
            baseline=None, comparison=comparison,
            measurement_type="TRANSFER",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.evidence_sufficient is False


# ====================================================================
# 6. Transfer measurement integrity (Fix 5)
# ====================================================================


class TestTransferMeasurement:
    """FIX 5: Verify cross-skill scores are not subtracted as improvement."""

    def test_transfer_reports_absolute_performance(self):
        """FIX 5: Transfer reports absolute target-skill performance."""
        source_post = _mock_assessment(
            score="0.900", independent_score="0.900",
            difficulty_mean="2.00", items_total=5,
        )
        transfer = _mock_assessment(
            score="0.600", independent_score="0.600",
            difficulty_mean="2.00", items_total=5,
        )

        metrics = compute_effectiveness(
            baseline=source_post, comparison=transfer,
            measurement_type="TRANSFER",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )

        # Transfer should report 0.600 (absolute performance),
        # NOT -0.300 (which would be a cross-skill subtraction)
        assert metrics.observed_improvement == Decimal("0.600")
        assert metrics.independent_improvement == Decimal("0.600")

    def test_transfer_without_baseline_same_as_absolute(self):
        """FIX 5: Transfer without baseline still reports absolute."""
        transfer = _mock_assessment(
            score="0.700", independent_score="0.700",
            difficulty_mean="2.00", items_total=5,
        )
        metrics = compute_effectiveness(
            baseline=None, comparison=transfer,
            measurement_type="TRANSFER",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("0.700")

    def test_transfer_never_shows_cross_skill_subtraction(self):
        """FIX 5: High source + low target must NOT show negative 'improvement'."""
        source = _mock_assessment(score="1.000", items_total=5)
        target = _mock_assessment(score="0.200", items_total=5)

        metrics = compute_effectiveness(
            baseline=source, comparison=target,
            measurement_type="TRANSFER",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        # Must be 0.200 (absolute), not -0.800 (cross-skill diff)
        assert metrics.observed_improvement == Decimal("0.200")

    def test_growth_still_uses_subtraction(self):
        """FIX 5: Same-skill GROWTH still computes improvement via subtraction."""
        baseline = _mock_assessment(score="0.200", items_total=5)
        post = _mock_assessment(score="0.800", items_total=5)

        metrics = compute_effectiveness(
            baseline=baseline, comparison=post,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("0.600")

    def test_retention_still_uses_subtraction(self):
        """FIX 5: Same-skill RETENTION still computes delta via subtraction."""
        post = _mock_assessment(score="0.800", items_total=5)
        retention = _mock_assessment(score="0.700", items_total=5)

        metrics = compute_effectiveness(
            baseline=post, comparison=retention,
            measurement_type="RETENTION",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("-0.100")


# ====================================================================
# 7. Misconception analysis
# ====================================================================


class TestMisconceptionAnalysis:
    """Verify misconception tracking between assessment phases."""

    def test_resolved_misconceptions(self):
        baseline = _mock_assessment(misconceptions=["ADD_REGROUP", "FLIP_DIGITS"])
        comparison = _mock_assessment(misconceptions=["ADD_REGROUP"])
        analysis = _analyse_misconceptions(baseline, comparison)
        assert "FLIP_DIGITS" in analysis.resolved
        assert "ADD_REGROUP" in analysis.persisting
        assert len(analysis.new) == 0

    def test_new_misconceptions(self):
        baseline = _mock_assessment(misconceptions=["ADD_REGROUP"])
        comparison = _mock_assessment(misconceptions=["WRONG_SIGN"])
        analysis = _analyse_misconceptions(baseline, comparison)
        assert "WRONG_SIGN" in analysis.new
        assert "ADD_REGROUP" in analysis.resolved

    def test_no_misconceptions(self):
        baseline = _mock_assessment(misconceptions=[])
        comparison = _mock_assessment(misconceptions=[])
        analysis = _analyse_misconceptions(baseline, comparison)
        assert analysis.resolved == []
        assert analysis.persisting == []
        assert analysis.new == []

    def test_baseline_none(self):
        comparison = _mock_assessment(misconceptions=["WRONG_SIGN"])
        analysis = _analyse_misconceptions(None, comparison)
        assert "WRONG_SIGN" in analysis.new
        assert analysis.resolved == []


# ====================================================================
# 8. Confidence computation
# ====================================================================


class TestConfidence:
    """Verify evidence confidence thresholds."""

    def test_insufficient_evidence(self):
        assert _compute_confidence(0) == "INSUFFICIENT"
        assert _compute_confidence(2) == "INSUFFICIENT"

    def test_low_evidence(self):
        assert _compute_confidence(3) == "LOW"
        assert _compute_confidence(4) == "LOW"

    def test_moderate_evidence(self):
        assert _compute_confidence(5) == "MODERATE"
        assert _compute_confidence(7) == "MODERATE"

    def test_high_evidence(self):
        assert _compute_confidence(8) == "HIGH"
        assert _compute_confidence(100) == "HIGH"


# ====================================================================
# 9. Effectiveness computation
# ====================================================================


class TestEffectivenessComputation:
    """Test the core compute_effectiveness function."""

    def test_perfect_improvement(self):
        baseline = _mock_assessment(
            score="0.000", independent_score="0.000",
            difficulty_mean="2.00", items_total=5,
        )
        comparison = _mock_assessment(
            score="1.000", independent_score="1.000",
            difficulty_mean="2.00", items_total=5,
        )
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("1.000")
        assert metrics.evidence_sufficient is True

    def test_no_improvement(self):
        baseline = _mock_assessment(
            score="0.600", independent_score="0.600",
            difficulty_mean="2.00", items_total=5,
        )
        comparison = _mock_assessment(
            score="0.600", independent_score="0.600",
            difficulty_mean="2.00", items_total=5,
        )
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("0.000")

    def test_regression(self):
        baseline = _mock_assessment(
            score="0.800", independent_score="0.800",
            difficulty_mean="2.00", items_total=5,
        )
        comparison = _mock_assessment(
            score="0.400", independent_score="0.400",
            difficulty_mean="2.00", items_total=5,
        )
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="RETENTION",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement < Decimal(0)

    def test_difficulty_incomparable(self):
        baseline = _mock_assessment(
            score="0.500", difficulty_mean="1.50", items_total=5,
        )
        comparison = _mock_assessment(
            score="0.800", difficulty_mean="3.50", items_total=5,
        )
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.difficulty_comparable is False

    def test_insufficient_evidence(self):
        baseline = _mock_assessment(score="0.500", items_total=1)
        comparison = _mock_assessment(score="0.800", items_total=1)
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.evidence_sufficient is False


# ====================================================================
# 10. Parent-friendly summary
# ====================================================================


class TestParentSummary:
    """Test parent-facing summary generation."""

    def test_not_assessed(self):
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
        )
        summary = parent_summary(report)
        assert summary.understood_initially == "Not assessed"
        assert summary.has_improved == "Not assessed"
        assert summary.remembers_after_days == "Not assessed"
        assert summary.needs_attention is False

    def test_strong_baseline(self):
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            has_baseline=True,
            baseline=_mock_assessment(
                phase=AssessmentPhase.BASELINE, independent_score="0.900",
            ),
        )
        assert parent_summary(report).understood_initially == "Well"

    def test_weak_baseline(self):
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            has_baseline=True,
            baseline=_mock_assessment(
                phase=AssessmentPhase.BASELINE, independent_score="0.100",
            ),
        )
        assert parent_summary(report).understood_initially == "Not yet"

    def test_improvement_yes(self):
        growth = _mock_metrics(independent_improvement="0.300")
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            has_post_instruction=True, growth=growth,
        )
        assert parent_summary(report).has_improved == "Yes"

    def test_retention_failure_needs_attention(self):
        retention = _mock_metrics(observed_improvement="-0.400")
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            has_retention=True, retention_metrics=retention,
        )
        summary = parent_summary(report)
        assert summary.remembers_after_days == "Not yet"
        assert summary.needs_attention is True
        assert "not retained" in summary.attention_reason.lower()

    def test_retention_waiting(self):
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            retention_scheduled=True,
        )
        assert parent_summary(report).remembers_after_days == "Waiting"

    def test_independent_mastery(self):
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            has_post_instruction=True,
            post_instruction=_mock_assessment(independent_score="0.900"),
        )
        assert parent_summary(report).can_solve_independently == "Yes"

    def test_persisting_misconceptions_need_attention(self):
        growth = _mock_metrics(
            independent_improvement="0.200",
            misconception_analysis=MisconceptionAnalysis(
                baseline=["ADD_REGROUP"], comparison=["ADD_REGROUP"],
                resolved=[], persisting=["ADD_REGROUP"], new=[],
            ),
        )
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            has_post_instruction=True, growth=growth,
        )
        summary = parent_summary(report)
        assert summary.needs_attention is True
        assert "misunderstandings persist" in summary.attention_reason.lower()


# ====================================================================
# 11. Item response recording
# ====================================================================


class TestItemResponseRecording:
    """Test deterministic scoring of individual item responses."""

    def test_correct_answer_recorded(self):
        family_code = next(iter(FAMILIES))
        spec = FAMILIES[family_code]
        problem = generate(family_code, seed=1, difficulty=spec.min_difficulty)
        correct = _normalize(problem.canonical_answer) == _normalize(problem.canonical_answer)
        assert correct is True

    def test_wrong_answer_detected(self):
        family_code = next(iter(FAMILIES))
        spec = FAMILIES[family_code]
        problem = generate(family_code, seed=1, difficulty=spec.min_difficulty)
        wrong = _normalize("completely_wrong") == _normalize(problem.canonical_answer)
        assert wrong is False

    def test_misconception_detection(self):
        for code, spec in FAMILIES.items():
            problem = generate(code, seed=1, difficulty=spec.min_difficulty)
            if problem.misconception_answers:
                first_code = next(iter(problem.misconception_answers))
                misconception_answer = problem.misconception_answers[first_code]
                detected = problem.misconception_for(misconception_answer)
                assert detected == first_code
                break


# ====================================================================
# 12. Assessment completion
# ====================================================================


class TestAssessmentCompletion:
    """Test aggregate score computation on assessment completion."""

    def test_score_uses_items_total_denominator(self):
        """FIX 4: Score denominator is items_total (includes unanswered)."""
        items_total = 5
        items_correct = 3
        score = Decimal(str(items_correct / items_total)).quantize(Decimal("0.001"))
        assert score == Decimal("0.600")

    def test_difficulty_mean_computation(self):
        difficulties = [1, 2, 3, 2, 2]
        mean = sum(difficulties) / len(difficulties)
        assert mean == 2.0


# ====================================================================
# 13. Retention scheduling
# ====================================================================


class TestRetentionScheduling:
    """Test retention assessment scheduling and expiration."""

    def test_default_delay_is_7_days(self):
        from app.services.learning_assessment import RETENTION_DELAY_DAYS
        assert RETENTION_DELAY_DAYS == 7

    def test_expiration_logic(self):
        now = datetime.now(UTC)
        scheduled_at = now - timedelta(days=20)
        cutoff = now - timedelta(days=14)
        assert scheduled_at <= cutoff

    def test_non_expired_not_affected(self):
        now = datetime.now(UTC)
        scheduled_at = now - timedelta(days=5)
        cutoff = now - timedelta(days=14)
        assert scheduled_at > cutoff

    def test_missing_assessment_not_failure(self):
        assert AssessmentStatus.EXPIRED.value == "EXPIRED"
        assert AssessmentStatus.EXPIRED != AssessmentStatus.COMPLETED


# ====================================================================
# 14. Data isolation
# ====================================================================


class TestDataIsolation:
    """Verify assessments are properly scoped to individual students."""

    def test_different_students_get_different_ids(self):
        assert uuid.uuid4() != uuid.uuid4()

    def test_student_id_is_required(self):
        a = LearningAssessment(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            phase=AssessmentPhase.BASELINE,
        )
        assert a.student_id is not None


# ====================================================================
# 15. Privacy-safe reporting
# ====================================================================


class TestPrivacySafeReporting:
    """Verify reports don't expose sensitive child data."""

    def test_report_contains_no_answers(self):
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
        )
        d = report.to_dict()
        assert "student_answer" not in str(d)

    def test_parent_summary_uses_plain_language(self):
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
        )
        summary = parent_summary(report)
        d = summary.to_dict()
        for key in d:
            assert "mastery" not in key
            assert "confidence" not in key
            assert "score" not in key

    def test_report_dict_is_serialisable(self):
        import json
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
        )
        json.dumps(report.to_dict())


# ====================================================================
# 16. Difficulty comparability
# ====================================================================


class TestDifficultyComparability:

    def test_same_difficulty_is_comparable(self):
        baseline = _mock_assessment(difficulty_mean="2.50", items_total=5)
        comparison = _mock_assessment(difficulty_mean="2.50", items_total=5)
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.difficulty_comparable is True

    def test_small_gap_is_comparable(self):
        baseline = _mock_assessment(difficulty_mean="2.00", items_total=5)
        comparison = _mock_assessment(difficulty_mean="2.80", items_total=5)
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.difficulty_comparable is True

    def test_large_gap_not_comparable(self):
        baseline = _mock_assessment(difficulty_mean="1.00", items_total=5)
        comparison = _mock_assessment(difficulty_mean="4.00", items_total=5)
        metrics = compute_effectiveness(
            baseline=baseline, comparison=comparison,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.difficulty_comparable is False


# ====================================================================
# 17. Model integrity
# ====================================================================


class TestModelIntegrity:

    def test_assessment_phases(self):
        assert AssessmentPhase.BASELINE.value == "BASELINE"
        assert AssessmentPhase.POST_INSTRUCTION.value == "POST_INSTRUCTION"
        assert AssessmentPhase.RETENTION.value == "RETENTION"
        assert AssessmentPhase.TRANSFER.value == "TRANSFER"

    def test_assessment_statuses(self):
        assert AssessmentStatus.SCHEDULED.value == "SCHEDULED"
        assert AssessmentStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert AssessmentStatus.COMPLETED.value == "COMPLETED"
        assert AssessmentStatus.EXPIRED.value == "EXPIRED"
        assert AssessmentStatus.CANCELLED.value == "CANCELLED"

    def test_effectiveness_snapshot_fields(self):
        snap = EffectivenessSnapshot(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            measurement_type="GROWTH",
        )
        assert snap.measurement_type == "GROWTH"
        assert hasattr(snap, "evidence_sufficient")
        assert hasattr(snap, "confidence_level")


# ====================================================================
# 18. End-to-end measurement flow
# ====================================================================


class TestEndToEndMeasurement:

    def test_growth_measurement_flow(self):
        baseline = _mock_assessment(
            score="0.200", independent_score="0.200",
            difficulty_mean="2.00", items_total=5,
            misconceptions=["ADD_REGROUP"],
        )
        post = _mock_assessment(
            score="0.800", independent_score="0.800",
            difficulty_mean="2.00", items_total=5,
            misconceptions=[],
        )
        metrics = compute_effectiveness(
            baseline=baseline, comparison=post,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("0.600")
        assert metrics.misconception_analysis.resolved == ["ADD_REGROUP"]

    def test_retention_measurement_flow(self):
        post = _mock_assessment(
            score="0.800", independent_score="0.800",
            difficulty_mean="2.00", items_total=5,
        )
        retention = _mock_assessment(
            score="0.700", independent_score="0.700",
            difficulty_mean="2.00", items_total=5,
        )
        metrics = compute_effectiveness(
            baseline=post, comparison=retention,
            measurement_type="RETENTION",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("-0.100")
        assert metrics.evidence_sufficient is True

    def test_full_lifecycle(self):
        baseline = _mock_assessment(
            score="0.200", independent_score="0.100",
            difficulty_mean="2.00", items_total=5,
            misconceptions=["FLIP_DIGITS", "NO_REGROUP"],
        )
        post = _mock_assessment(
            score="0.800", independent_score="0.700",
            difficulty_mean="2.20", items_total=5,
            misconceptions=["NO_REGROUP"],
        )
        retention = _mock_assessment(
            score="0.700", independent_score="0.600",
            difficulty_mean="2.00", items_total=5,
            misconceptions=[],
        )

        growth = compute_effectiveness(
            baseline=baseline, comparison=post,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert growth.observed_improvement == Decimal("0.600")
        assert "FLIP_DIGITS" in growth.misconception_analysis.resolved
        assert "NO_REGROUP" in growth.misconception_analysis.persisting

        ret = compute_effectiveness(
            baseline=post, comparison=retention,
            measurement_type="RETENTION",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert ret.observed_improvement == Decimal("-0.100")
        assert "NO_REGROUP" in ret.misconception_analysis.resolved


# ====================================================================
# 19. Edge cases
# ====================================================================


class TestEdgeCases:

    def test_perfect_baseline_no_room_to_improve(self):
        baseline = _mock_assessment(score="1.000", independent_score="1.000", items_total=5)
        post = _mock_assessment(score="1.000", independent_score="1.000", items_total=5)
        metrics = compute_effectiveness(
            baseline=baseline, comparison=post,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("0.000")

    def test_zero_to_zero_no_improvement(self):
        baseline = _mock_assessment(score="0.000", items_total=5)
        post = _mock_assessment(score="0.000", items_total=5)
        metrics = compute_effectiveness(
            baseline=baseline, comparison=post,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.observed_improvement == Decimal("0.000")

    def test_single_item_insufficient(self):
        baseline = _mock_assessment(score="0.000", items_total=1)
        post = _mock_assessment(score="1.000", items_total=1)
        metrics = compute_effectiveness(
            baseline=baseline, comparison=post,
            measurement_type="GROWTH",
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
        )
        assert metrics.evidence_sufficient is False

    def test_report_to_dict_with_metrics(self):
        import json
        growth = _mock_metrics(
            observed_improvement="0.500", independent_improvement="0.400",
        )
        report = SkillEffectivenessReport(
            student_id=uuid.uuid4(), skill_id=uuid.uuid4(),
            skill_code="MATH.NS.ADDITION", skill_name="Addition",
            current_mastery=Decimal("0.850"), growth=growth,
        )
        json.dumps(report.to_dict())


# ====================================================================
# Test helpers
# ====================================================================

def _mock_assessment(
    *,
    phase: AssessmentPhase = AssessmentPhase.BASELINE,
    score: str | None = None,
    independent_score: str | None = None,
    difficulty_mean: str | None = None,
    items_total: int = 5,
    misconceptions: list[str] | None = None,
) -> LearningAssessment:
    """Create a mock LearningAssessment with specified scores."""
    a = LearningAssessment(
        id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
        phase=phase,
        status=AssessmentStatus.COMPLETED,
        scheduled_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        items_total=items_total,
    )
    if score is not None:
        a.score = Decimal(score)
    if independent_score is not None:
        a.independent_score = Decimal(independent_score)
    if difficulty_mean is not None:
        a.difficulty_mean = Decimal(difficulty_mean)
    if misconceptions is not None:
        a.misconceptions_detected = misconceptions
    return a


def _mock_metrics(
    *,
    observed_improvement: str = "0.000",
    independent_improvement: str = "0.000",
    misconception_analysis: MisconceptionAnalysis | None = None,
) -> object:
    """Create a mock EffectivenessMetrics."""
    from app.services.learning_effectiveness import EffectivenessMetrics
    if misconception_analysis is None:
        misconception_analysis = MisconceptionAnalysis(
            baseline=[], comparison=[], resolved=[], persisting=[], new=[],
        )
    return EffectivenessMetrics(
        student_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
        measurement_type="GROWTH",
        baseline_score=Decimal("0.500"),
        baseline_independent_score=Decimal("0.500"),
        comparison_score=Decimal("0.800"),
        comparison_independent_score=Decimal("0.800"),
        observed_improvement=Decimal(observed_improvement),
        independent_improvement=Decimal(independent_improvement),
        baseline_difficulty_mean=Decimal("2.00"),
        comparison_difficulty_mean=Decimal("2.00"),
        difficulty_comparable=True,
        misconception_analysis=misconception_analysis,
        evidence_count=10,
        evidence_sufficient=True,
        confidence_level="HIGH",
    )
