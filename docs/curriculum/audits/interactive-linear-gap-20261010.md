# Guided linear visualization follow-up

Extends PR #329 as one visualization bundle. Existing `algebra_functions.py`
contains linear evaluation, slope-from-table and model families. `ProblemVisual`
has a static linear renderer, but the inspected main branch and open MVE PRs
have no interactive slope/intercept controller. Content PRs #317 and #327 contain
draft linear teaching packages; this implementation does not import or activate them.

## Implementation

- Exact reduced rational slope and value table; bounded integer rise [-6,6],
  positive run [1,6], intercept [-4,4]. No floating-point grading.
- Three keyboard-native sliders connect the existing graph, equation and table.
- Optional labeled rise/run triangle in the shared renderer; default visuals unchanged.
- Explain horizontal/negative slopes, intercept shifts, and why vertical lines are
  excluded from y = mx + b. Four separate deterministic practice items accept
  mathematically equivalent fractions, including negative denominators.
- Assessment guard removes the complete stateful activity. Only guided/remediation
  states and known slope/intercept skill names select this activity in Workspace.
- Strict allowlisted semantic events; no identifiers, persistence or mastery writes.
- Fix deduplication of line-clipping endpoints when a corner belongs to two edges.

## Executed verification

`npm run test:mve`: 25 passing tests, including exhaustive checks of all 702 bounded
linear models and 882 integer models. Real React SSR, SVG output, labels, live status,
actual handler behavior, equivalent-answer checks, invalid events, assessment guards,
and graph-corner regression are exercised. `npm run build` passes TypeScript and Vite.

`e2e/mve-guided-browser.mjs` adds a standalone real-browser component harness using
existing Vite and Playwright dependencies. It checks keyboard boundaries, semantic
events, practice, reduced-motion mode, and assessment unmount/reset for both explorers.
Run after installing the frontend and e2e dependencies and Playwright Chromium:

    node e2e/mve-guided-browser.mjs

Browser execution remains BLOCKED locally: Playwright's Chromium download returned
invalid/truncated archives. The harness is syntax-checked, not claimed as passed.
Full application E2E, screen-reader testing and independent pedagogical review remain
outstanding. These changes do not establish complete curriculum coverage.
