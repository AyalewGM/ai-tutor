# F-003 Product Research: Graduated Hints and Productive Struggle

## Product question

How should the tutor help a learner who is stuck without either withholding useful support or giving away the mathematics too early?

## Competitive findings

### Khanmigo
Khan Academy describes Khanmigo as a tutor that guides learners through questions, hints, scaffolding, and step-by-step reasoning rather than simply providing answers. Its student experience is intentionally designed to keep the cognitive work with the learner and maintain productive struggle.

Sources:
- https://www.khanacademy.org/khan-labs
- https://www.khanacademy.org/khan-for-educators/k4e-us-demo/xb78db74671c953a7%3Aget-to-know-khan-academy/xb78db74671c953a7%3Aexplore-the-student-experience/v/working-through-content
- https://www.khanacademy.org/khan-for-educators/k4e-us-demo/xb78db74671c953a7%3Aget-to-know-khan-academy/xb78db74671c953a7%3Aexplore-the-student-experience/v/getting-help-with-tutor-me

### Carnegie Learning MATHia
MATHia commonly exposes three hint levels. Learners are encouraged to try independently before asking for help and can progressively request deeper hints. The system also provides just-in-time hints when it recognizes a common mistake. A final "bottom-out" hint can reveal the blocked step after lighter support is insufficient.

Carnegie Learning explicitly distinguishes productive struggle from unproductive flailing. It also avoids treating ordinary help-seeking as equivalent to failure; stronger assistance such as a bottom-out hint carries different learning evidence than lighter hints.

Sources:
- https://support.carnegielearning.com/help-center/math/mathia/getting-started-in-mathia/article/getting-started-mathia-students/
- https://support.carnegielearning.com/help-center/math/educators/mathia/mathia-faqs/article/when-and-why-do-skills-move/
- https://www.carnegielearning.com/blog/mathia-ai

## Product interpretation

Our hint system should not be a free-form chat feature. It should be a controlled pedagogical intervention tied to:

- current tutor state;
- problem and skill;
- misconception evidence;
- prior attempts on the same problem;
- hint history on the same problem;
- whether the learner explicitly requested help;
- whether the learner is in a protected assessment mode.

## Recommended V1 ladder

### Level 0 — Independent attempt
No hint. The learner owns the entire step.

### Level 1 — Directional cue
Direct attention to the relevant object or operation without stating the mathematical rule or completed step.

Example: "Look at the number immediately outside the parentheses. What parts of the expression does it affect?"

### Level 2 — Conceptual cue
Name the governing concept or likely misconception and ask a focused question.

Example: "The distributive property means the outside factor applies to every term. Which term has not been multiplied yet?"

### Level 3 — Partial scaffold
Expose structure or part of the next step while preserving meaningful learner work.

Example: `3(x+4) = 3x + ___`

### Level 4 — Bottom-out/model
Demonstrate the blocked step after lighter support has failed, then require the learner to continue or solve a near-transfer problem.

Example: `3(x+4) = 3x + 12`. The learner must still continue the equation or solve a fresh equivalent problem.

## Escalation rules

1. Practice begins at Level 0.
2. An explicit help request advances by at most one level.
3. A confidently recognized misconception may trigger a just-in-time Level 1 or 2 hint.
4. Repeated failure on the same problem escalates gradually rather than immediately showing the solution.
5. Level 4 is a last instructional resort, not a convenience shortcut.
6. Diagnostic and mastery-check modes remain protected from hints.
7. Level 3/4 success is assisted evidence and cannot itself establish independent mastery.
8. A new problem should reset the hint ladder to Level 0.

## Differentiation

The product should know not only *what explanation to generate*, but *how much information is pedagogically appropriate right now*. This makes hint depth part of the deterministic learning policy rather than an uncontrolled property of an LLM response.

## Measurement

Persist enough data to study later:
- help-request rate;
- highest hint level per problem;
- misconception-triggered vs learner-requested hints;
- success after each hint level;
- transfer success on the next independent problem;
- time/attempts before bottom-out support.

These measures can eventually inform an optimized help policy, but V1 should remain transparent and deterministic.
