# ADR-015: Escalation Policy Audit Against Tutoring Research

Status: Accepted
Date: 2026-09-30

## Context

ADR-013 set the pilot escalation thresholds as hypotheses. This record audits the
three adaptive systems against the intelligent-tutoring literature and records
what was confirmed, changed, or deferred.

## The systems audited

1. **Step ladder** (`stepwork.py`): each wrong work line is flagged immediately;
   invalid 1 → generic retry, invalid 2 → targeted misconception feedback,
   invalid ≥3 → reveal one legal next line (invalid count resets on any
   accepted line, so each reveal must be re-earned).
2. **Hint ladder** (`hint_policy.py`): four rungs — directional cue → concept +
   focused question → partial scaffold → modeled step. Explicit request moves up
   one rung; confident misconception (≥0.75) emits a capped just-in-time cue;
   ≥2 failed attempts on a problem trigger the next rung. Hints are disabled in
   assessment states; levels 3–4 mark the attempt as assisted.
3. **Intervention policy** (`intervention_policy.py` pilot-v1): ≥2 independent
   failures on *distinct* target-skill problems → declared prerequisite edge →
   ≥2 independent prerequisite failures (post-mastery) → remediation switch;
   return requires fresh independent success.

## Evidence

- Corbett & Anderson (LISP tutor); Mathan & Koedinger (2002, 2005): immediate
  error flagging improves learning *rate* and, when paired with error-correction
  guidance, transfer and retention. The delayed-feedback critique is not
  supported empirically in this setting.
- Koedinger & Aleven (2007, "the assistance dilemma"): giving vs. withholding
  help has no universal optimum; graduated ladders that raise specificity on
  continued need are the field's standard compromise.
- Aleven & Koedinger (2000); Baker, Corbett, Koedinger & Wagner (2004); Baker
  et al. (2008): students commonly drill straight to bottom-out hints; "gaming
  the system" correlates with substantially worse posttest performance,
  independent of prior knowledge.
- Shih, Koedinger & Scheines (2008): bottom-out hints function as worked
  examples and are not inherently abusive — deliberate, effortful use predicts
  learning. The harmful pattern is rapid drilling *without intervening
  problem-solving*.
- Renkl & Atkinson (2003); Renkl, Atkinson & Grosse (2004): faded worked-out
  steps plus self-explanation prompts produce medium-to-large transfer gains
  and fewer unproductive learning events than example–problem pairs.
- Beck & Gong (2013); early-detection follow-up (AIED 2020): learners who do
  not master a skill quickly are likely to wheel-spin indefinitely; the two
  trajectories are distinguishable within the first ~3–5 practice
  opportunities.
- Aleven et al. (2016, "Help Tutor"): meta-level feedback on help-seeking
  durably improves how students use help, even after the coaching is removed.

## Judgments

- **Immediate flagging of wrong steps: kept.** Matches the strongest evidence
  (learning rate, transfer).
- **Four-rung ladder ordering: kept.** It is the standard assistance-dilemma
  compromise; levels 3–4 already carry an assisted-evidence penalty, so bottom-
  out help cannot inflate mastery.
- **Intervention thresholds (2 + 2 independent failures): kept.** On the early
  side of the 3–5-opportunity detection window, which is the safe direction
  against wheel-spinning, and each failure must be on a distinct problem —
  retries on one problem cannot manufacture breadth.
- **Hint click-through: changed.** Explicit requests previously escalated one
  rung unconditionally — four clicks reached the modeled step in seconds.
  `select_hint` now accepts `attempt_since_last_hint`; a request with no
  intervening answer or work step returns the *same* rung with trigger
  `REPEAT_LEVEL` instead of escalating. This targets exactly the harmful
  pattern Shih et al. separate from legitimate worked-example use.
- **Reveal cadence: kept, plus a self-explanation cue.** Revealing one legal
  line (not the answer) already mirrors step-fading, and the streak reset means
  each reveal must be re-earned. Reveal feedback now asks the learner to say
  *why* the line preserves equality — the cheapest evidence-backed upgrade in
  the literature (fading + self-explanation prompts).
- **Assessment states keep hints disabled.** Non-negotiable for evidence
  integrity.

## Deferred (documented, not built)

- **Wheel-spinning detector.** Beck & Gong show non-mastery after ~10 attempts
  is a stable failure signal; a per-skill stall indicator for parents/educators
  (distinct from prerequisite remediation, which needs a declared edge) is a
  candidate follow-up. It requires a parent-facing surface decision first.
- **Response-time-based help-abuse detection** (Shih et al.'s model) — needs
  client timing telemetry we deliberately do not collect under the data
  minimization rules.
- **Adaptive hint cadence by prior knowledge** — literature suggests the
  immediate/delayed and scaffold depth optima depend on skill level; we do not
  yet have the volume to fit this, so fixed thresholds + evidence penalties
  remain the honest choice.

## Consequences

- `hint_api` computes `attempt_since_last_hint` from persisted `Attempt` and
  student `TutorTurn` rows; nothing is client-reported.
- `REPEAT_LEVEL` is a new hint trigger, persisted on `HintEvent` like the rest.
- The pilot demo now survives the classic abuse case: rapid hint clicks cannot
  reach the bottom-out rung.
