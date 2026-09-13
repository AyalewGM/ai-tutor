# Product Research Cycle 1 — Adaptive Math Tutoring

Date: 2026-09-13

## Research question

What should an adaptive AI math tutor do beyond generic chat in order to improve independent learning and curriculum mastery?

## Sources reviewed

### Khan Academy / Khanmigo
Sources:
- https://www.khanacademy.org/khan-for-educators/k4e-us-demo/xb78db74671c953a7%3Aget-to-know-khan-academy/xb78db74671c953a7%3Aexplore-the-student-experience/v/getting-help-with-tutor-me
- https://www.khanacademy.org/khan-for-educators/k4e-us-demo/xb78db74671c953a7%3Aget-to-know-khan-academy/xb78db74671c953a7%3Aexplore-the-student-experience/v/working-through-content

Observed product principles:
- tutoring is context-aware to the lesson/problem;
- guiding questions and scaffolding are preferred to answer disclosure;
- the tutor is designed to preserve the student's cognitive work;
- hints and step-by-step guidance are integrated into vetted learning content rather than detached free-form chat.

### ALEKS
Sources:
- https://www.aleks.com/index
- https://www.aleks.com/highered/Transition_Guide_to_ALEKS.pdf

Observed product principles:
- maintain an explicit representation of student knowledge state;
- identify prerequisite gaps;
- recommend topics the student is currently ready to learn;
- use a continuous mastery/retention cycle rather than only percent-correct scoring.

### IXL
Sources:
- https://www.ixl.com/materials/us/research/IXL_Design_Principles.pdf
- https://blog.ixl.com/2024/07/31/reach-new-heights-with-the-ixl-levelup-math-benchmark-assessment/

Observed product principles:
- proficiency is modeled continuously rather than as raw percent correct;
- item difficulty, response patterns, and learning trajectory affect proficiency;
- adaptive diagnostic information feeds personalized recommendations;
- practice and diagnostic evidence are connected.

### Synthesis Tutor
Source:
- https://www.synthesis.com/tutor

Observed product principles:
- continuous micro-assessments occur inside lessons;
- wrong answers trigger adaptation and gap filling;
- progression depends on demonstrated understanding;
- parent progress reporting is part of the product experience;
- AI is not given sole ownership of pedagogy.

### Open-source reference: ArvindAkula/ai_math_tutor
Source:
- https://github.com/ArvindAkula/ai_math_tutor

Observed implementation ideas:
- step-by-step explanations;
- quizzes and immediate feedback;
- progress tracking and adaptive learning paths;
- symbolic math computation;
- visualization support;
- React frontend, FastAPI math engine, PostgreSQL, Redis, authentication, and deployment infrastructure.

This repository is useful as an implementation reference, but our primary differentiation should remain curriculum-aware mastery, misconception diagnosis, prerequisite remediation, and explicit independent-mastery evidence rather than broad mathematical feature coverage alone.

## Product conclusions

The strongest common pattern is not “better chat.” It is a controlled learning loop:

1. establish current knowledge state;
2. select an appropriate next skill/problem;
3. preserve productive struggle with graduated hints;
4. diagnose the underlying misconception or prerequisite gap;
5. remediate the gap;
6. require independent evidence before mastery;
7. revisit knowledge later for retention;
8. expose understandable progress to the parent/student.

## Differentiation hypothesis

Our platform should combine:
- curriculum graph;
- explicit prerequisite graph;
- misconception model;
- assistance-aware mastery;
- independent mastery checks;
- next-best-learning-action selection;
- constrained LLM tutoring language;
- transparent parent progress explanations.

The application, not the LLM, should own progression and mastery decisions.

## Recommendation for next vertical slice

Build **Prerequisite-Aware Adaptive Linear Equations** for MCPS Grade 8.

The feature should extend the current distributive-property slice into a small skill graph and prove that the system can detect a prerequisite gap, temporarily remediate it, verify independent understanding, and resume the original learning goal.
