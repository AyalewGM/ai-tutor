# Quadratic patterns — R4 draft pedagogical supplement

Source package: `W2-G9-QUADRATIC-PATTERNS`, PR #328. Status: `DRAFT_UNVERIFIED`; runtime off.

## Bounded learning arc

This revision is limited to recognizing, predicting, representing, and explaining quadratic growth from a tile pattern and table. Factoring, roots, and the quadratic formula belong to separately mapped and reviewed objectives.

- **Observe — concrete/visual:** Build stages 0–3 of a growing tile design and record counts in a table.
- **Predict — visual:** Predict the next border and stage-4 count before extending the table; retain the prediction and explanation.
- **Manipulate — concrete/visual:** Add the next L-shaped/bordered tile layer with keyboard controls; a numbered row/column inventory provides the nonvisual equivalent.
- **Explain — visual/symbolic:** Build the first-difference row, then its difference row. Explain that changing first differences and constant nonzero second differences distinguish the pattern from linear growth.
- **Practice — visual/symbolic:** Use fresh tile tables with different positive leading coefficients. Reconstruct both difference rows before writing a rule.
- **Diagnose — evidence-routed:** Route from the learner's difference rows, stage prediction, and rule—not from correct/incorrect alone.
- **Transfer — symbolic:** An unfamiliar tile-count log omits stage 4 and the rule. Infer the next first difference, predict the count, write a rule, and justify quadratic growth.
- **Verify — symbolic:** Server-controlled fresh tables collect both difference rows, prediction, symbolic rule, and explanation without tiles, hints, linked examples, or guided mastery credit.

## Observable misconception routes

1. **`FIRST_VS_SECOND_DIFFERENCES`** — learner calls the table linear after seeing that counts increase. Ask for every adjacent change and then the changes of those changes. Repair by pairing each added border with the growing first difference; fade after two fresh tables classify growth with evidence.
2. **`CONSTANT_DIFFERENCE_EXTENDED`** — learner repeats the last first difference to predict stage 4. Ask how much consecutive first differences themselves change. Repair by extending the second-difference row first; fade after two correct unseen predictions.
3. **`RULE_WITHOUT_TABLE_CHECK`** — a proposed rule matches one stage but not all supplied stages. Ask the learner to substitute stages 0, 1, and 2. Repair with a table-rule reconciliation checklist; fade after two rules reproduce every supplied value and the unseen prediction.

## Independent assessment contract

`generate_quadratic_pattern` creates mode-separated deterministic tile-count logs. Public parameters contain only stages 0–3 and their counts. First/second differences, stage-4 prediction, coefficients, symbolic rule, and explanation remain teacher-only. The implementation is an offline content oracle, not backend scoring or a wired manipulative.
