# F-002 Product Research: Adaptive Diagnostic Placement

## Product question

How should the tutor determine where a learner should start without forcing a long placement exam or trusting the learner's selected grade/topic?

## Competitive findings

### ALEKS
ALEKS begins courses with an adaptive Initial Knowledge Check of roughly 25-30 questions. Each question depends on prior responses, and the resulting knowledge state distinguishes mastered topics from topics the learner is not yet ready for.

Source: https://www.aleks.com/highered/math/New_IM_HE_Math_Quick_Start_Guide.pdf

### IXL
IXL's diagnostic estimates working grade/strand levels and initially represents uncertain results as ranges. As evidence accumulates, the range narrows to a pinpointed level. IXL also recommends small recurring diagnostic samples so the model stays current rather than treating placement as a one-time event. IXL documents use of item difficulty and response patterns in its adaptive assessment design.

Sources:
- https://blog.ixl.com/2021/01/28/common-questions-about-the-ixl-real-time-diagnostic/
- https://www.ixl.com/materials/us/research/IXL_Design_Principles.pdf

### Synthesis Tutor
Synthesis positions adaptation around surfacing mistakes and filling knowledge gaps during instruction. This supports integrating diagnosis with tutoring rather than making all diagnosis a separate experience.

Source: https://www.synthesis.com/tutor

## Product interpretation

We should not copy a long benchmark diagnostic. Our initial product has a narrower curriculum graph and can exploit prerequisite relationships directly.

Recommended approach:

1. Start from the learner's declared course/grade and selected learning goal.
2. Probe the target skill with a small number of strategically selected items.
3. If evidence is weak or errors indicate prerequisite gaps, traverse downward through the prerequisite graph.
4. Maintain mastery and confidence separately.
5. Stop probing a branch when the system has sufficient evidence to classify it as ready or not ready.
6. Produce a diagnostic placement result containing the recommended starting skill plus evidence and unresolved uncertainty.
7. Continue recalibrating mastery/confidence during normal tutor sessions; diagnostic placement is not permanent.

## Differentiation

The diagnostic should answer more than "what grade level is this learner?" It should answer:

- What is the learner trying to learn now?
- Which prerequisite is the deepest meaningful gap blocking that goal?
- Which skills are already sufficiently ready and should not be repeated?
- How confident is the system in each conclusion?
- What is the smallest next learning action that improves readiness for the goal?

This aligns diagnostic placement with our core differentiator: curriculum-aware mastery, misconception diagnosis, prerequisite remediation, and next-best-learning action.

## Product constraints for V1

- Grade 8 algebra graph only.
- No LLM authority over placement or mastery.
- Diagnostic answers are unassisted; tutoring/hints are disabled during diagnostic items.
- Prefer fewer questions when confidence is already sufficient.
- Do not label a child globally as a grade-level number in V1; report skill readiness and learning gaps instead.
- Store the evidence behind every placement recommendation.

## Recommended F-002 outcome

Given a target skill such as Multi-Step Equations, the diagnostic should return:

- target skill;
- recommended starting skill;
- readiness state for evaluated prerequisite skills;
- mastery/confidence evidence;
- reason for placement;
- next recommended problem/learning action.

The first implementation should use deterministic rules on the existing skill graph. More advanced methods such as IRT/Bayesian knowledge tracing can be evaluated after sufficient real student data exists.
