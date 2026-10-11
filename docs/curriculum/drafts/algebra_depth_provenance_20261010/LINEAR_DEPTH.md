# Linear modeling — R4 draft pedagogical supplement

Package: `W1-G9-LINEAR-MODELING` (PR #327). Status: `DRAFT_UNVERIFIED`. Runtime off.

## Bounded learning arc

This revision narrows the package to one claim: a constant rate and an initial value describe the same linear relationship in a physical context, table, graph, and equation, subject to a justified domain. Standalone equation solving and two-line intersection are outside this revision.

- **Observe — concrete/visual:** Assemble a fixed loading-time card and one equal time block per crate. Read a table beginning at zero crates.
- **Predict — visual:** Before calculating, predict which table column is constant and where the graph begins; retain both commitments.
- **Manipulate — concrete/visual:** Change the fixed card while holding rate blocks constant, then change rate blocks while holding the fixed card constant. Keyboard actions expose the same state in a labelled table.
- **Explain — visual/symbolic:** Connect the table's value at zero to the graph's vertical intercept and fixed term. Connect equal first differences to graph rise per one-crate run and the coefficient of `n`, with units.
- **Practice — visual/symbolic:** Translate fresh table/context records into rate, initial value, equation, graph description, and feasible domain. Guided answers never award mastery.
- **Diagnose — evidence-routed:** Route only from captured zero-input, difference, graph, and domain responses. Do not infer a misconception from a total score.
- **Transfer — symbolic:** An unfamiliar delivery-cart log supplies table values and capacity but no equation or graph. The learner must produce and reconcile all representations.
- **Verify — symbolic:** Server-controlled fresh records collect rate/intercept units, equation, graph translation, physical domain, and domain justification with no hints or worked answer.

## Observable misconception routes

1. **`SLOPE_INTERCEPT_SWAP`** — learner uses the first nonzero output as rate or writes `rate + initial*n`. Ask for the zero-crate value and all adjacent output changes. Repair with separate fixed-time and per-crate columns; fade after two new tables identify both quantities with units.
2. **`TABLE_GRAPH_DISCONNECT`** — equation is correct but graph description begins at `(0,0)` or uses unequal rises. Ask which table row fixes the starting point and which repeated change fixes a one-unit rise. Repair by matching two table rows to two labelled graph points; fade after two representation translations agree.
3. **`CONTEXT_DOMAIN`** — learner accepts negative/fractional crate counts or values beyond capacity. Ask which inputs correspond to possible cart loads. Repair with a capacity-bounded discrete input list; fade after two new contexts justify both discreteness and bounds.

## Independent assessment contract

`generate_linear_translation` creates a mode-separated, deterministic delivery-log transfer. Its public payload contains only table/context data and six requested response fields. Rate, initial value, equation, graph description, domain, and justification stay in the teacher-only oracle. Backend scoring, browser accessibility, and student-flow integration are not implemented or claimed.
