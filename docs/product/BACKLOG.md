# Product Backlog

Prioritization considers learning impact, evidence from product research, MVP fit, dependency readiness, and implementation cost.

## Implemented

### F-001 Prerequisite-Aware Adaptive Linear Equations — DONE
Expand the current distributive-property vertical slice into a small MCPS Grade 8 linear-equation skill/prerequisite graph. Detect prerequisite gaps, enter targeted remediation, verify independent understanding, and resume the original goal.

### F-002 Diagnostic Placement and Readiness — DONE
Use a short adaptive diagnostic to estimate starting mastery and choose the appropriate entry skill/difficulty rather than beginning every learner at the same place.

### F-003 Graduated Hint Ladder and Productive Struggle — DONE
Standardize hint levels across skills and ensure the tutor asks focused questions before revealing worked steps. Track assistance as learning evidence.

### F-004 Independent Mastery Gate — DONE
Separate assisted success from mastery. Require independent problems and a short mastery check before marking a skill mastered.

### F-005 Student Tutor Workspace — DONE
Create the first usable React/Next.js learner interface for session start, problem display, typed responses, tutor messages, hint requests, and progress state.

### F-006 Progress and Learning Explanation — DONE
Expose mastery, evidence confidence, active misconceptions, improvement, and recommended next work in language useful to a parent and student.

### F-007 Spaced Review / Retention — DONE
Schedule review after apparent mastery and lower confidence/mastery when retention evidence shows forgetting. Expanding review intervals (1/3/7/14/30 days), confidence-scaled forgetting decay, review demotion to REVIEW_DUE, and review-due session interception before new instruction.

### F-010 Broader Misconception Catalog — DONE
Ordered misconception-rule registry replacing single hardcoded detection. Fourteen codes shipped across all four seeded curricula: DIST_001–002 (distribution), ALG_001–002 (like-terms and constant signs), EQ_001–003 (inverse operations), REL_001–002 (linear relations), NUM_001–003 (integers and fractions), FIN_001–002 (percent), each with a remediation_strategy that constrains LLM tutoring language. Further rule coverage remains an ongoing content task.

### F-011 Difficulty-Aware Mastery and Adaptive Progression — DONE
Mastery evidence is scaled by problem difficulty relative to learner level (harder success = stronger evidence; easy failure = stronger negative evidence). `current_difficulty` now increases on successful independent progression (cap 10) and decreases when the engine triggers remediation (floor 1), keyed on the pre-focus-policy transition so detours still register struggle.

### F-012 Retention Visibility — DONE
Read-only `reviews_due` projection surfaces due/relearning skills with projected decayed mastery to the parent dashboard (`ChildDashboardOut.reviews_due`) and learner workspace (`LearnerWorkspaceOut.reviews_due`). New `spaced_review_pass_rate` KPI in telemetry.

## P2 — Content intake and richer math interaction (remaining)

### F-008 Worksheet / Photo Problem Intake — NOT IMPLEMENTED
Accept a worksheet or problem image, extract the problem, map it to a curriculum skill, and enter the normal tutoring workflow without allowing OCR confidence problems to silently become authoritative truth.

### F-009 Mathematical Visualization — NOT IMPLEMENTED
Introduce graphs/visual representations where they materially improve conceptual understanding, especially linear functions and coordinate relationships. Likely requires a backend render spec on problems plus frontend rendering.

## Deferred until after private MVP validation
- gamification system;
- native mobile applications;
- voice-first tutoring;
- school/district roster and LMS integration;
- multi-subject expansion;
- agentic pedagogy that can override deterministic learning controls.
