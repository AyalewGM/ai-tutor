/**
 * Signed-integer addition: reproducible full student-journey E2E.
 *
 * Covers the W3-G7-SIGNED-NUMBERS slice end to end on MCPS_MATH_7
 * "Signed Number Operations" (M7.NS.RAT):
 *   register -> add learner -> pick skill -> DIAGNOSE -> GUIDED_PRACTICE
 *   -> INDEPENDENT_PRACTICE -> MASTERY_CHECK -> COMPLETE
 *
 * Verified along the way:
 *   - the LearnPanel-hosted GuidedIntegerNumberLine (data-mve-family=
 *     "integer-addition") and the InteractiveIntegerNumberLine mount only in
 *     guided states and never inside assessment states (DIAGNOSE,
 *     INDEPENDENT_PRACTICE, MASTERY_CHECK) — guided-practice isolation;
 *   - the guided widget's deterministic task, Socratic prompts, marker walk,
 *     misconception diagnosis (WRONG_DIRECTION) and correction loop;
 *   - hints are disabled during assessment states;
 *   - a synthetic solver drives the seeded + generated SIGNED_NUMBERS tiers
 *     (add, word, inverse, which_point, subtract, multiply, divide, distance)
 *     so the journey is reproducible on any seeded stack.
 *
 * Prerequisites: the standard seed pipeline (scripts/ops/seed_all_curricula.py,
 * which includes seed_learn_content.py) must have run so M7.NS.RAT carries the
 * INTEGER_OPS lesson that hosts the guided widget.
 *
 * Run: cd e2e && E2E_BASE_URL=http://127.0.0.1:3000 npx playwright test signed-integer-journey
 */
const { test, expect } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:3000';

const PASSWORD = 'SyntheticOnly!12345';
const PARENT_PIN = '4821';
const SKILL_NAME = 'Signed Number Operations';

/* ------------------------------------------------------------------ */
/* Deterministic solvers for every SIGNED_NUMBERS tier                */
/* ------------------------------------------------------------------ */

function solveSignedNumbers(text) {
  const t = text.trim().replace(/\s+/g, ' ');
  let m;
  // add tier: "Evaluate -5 + 3." / "Evaluate -5 + (-3)."
  if ((m = t.match(/^Evaluate (-?\d+) \+ \(?(-?\d+)\)?\.$/))) {
    return String(parseInt(m[1], 10) + parseInt(m[2], 10));
  }
  // subtract tier: "Evaluate 3 - (-4)." / "Evaluate -4 - 9."
  if ((m = t.match(/^Evaluate (-?\d+) - \(?(-?\d+)\)?\.$/))) {
    return String(parseInt(m[1], 10) - parseInt(m[2], 10));
  }
  // multiply tier: "Evaluate (-6) × (-4)." / "Evaluate -6 × 4."
  if ((m = t.match(/^Evaluate \(?(-?\d+)\)? × \(?(-?\d+)\)?\.$/))) {
    return String(parseInt(m[1], 10) * parseInt(m[2], 10));
  }
  // divide tier: "Evaluate (-24) ÷ (-6)." / "Evaluate 24 ÷ -6." is not
  // generated (divisor is parenthesized), but tolerate both forms.
  if ((m = t.match(/^Evaluate \(?(-?\d+)\)? ÷ \(?(-?\d+)\)?\.$/))) {
    return String(parseInt(m[1], 10) / parseInt(m[2], 10));
  }
  // word tier contexts.
  if ((m = t.match(/^The temperature was (-?\d+) degrees and rose by (\d+) degrees\./))) {
    return String(parseInt(m[1], 10) + parseInt(m[2], 10));
  }
  if ((m = t.match(/^The temperature was (-?\d+) degrees and fell by (\d+) degrees\./))) {
    return String(parseInt(m[1], 10) - parseInt(m[2], 10));
  }
  if ((m = t.match(/^A diver was at an elevation of (-?\d+) feet and dove (\d+) feet deeper\./))) {
    return String(parseInt(m[1], 10) - parseInt(m[2], 10));
  }
  if ((m = t.match(/^A hiker was at an elevation of (-?\d+) feet and climbed (\d+) feet\./))) {
    return String(parseInt(m[1], 10) + parseInt(m[2], 10));
  }
  // inverse tier: "What number added to 7 gives 0?"
  if ((m = t.match(/^What number added to (-?\d+) gives 0\?$/))) {
    return String(-parseInt(m[1], 10));
  }
  // distance tier.
  if ((m = t.match(/^Point P is at (-?\d+) and point Q is at (-?\d+) on the number line\. What is the distance between them\?$/))) {
    return String(Math.abs(parseInt(m[2], 10) - parseInt(m[1], 10)));
  }
  // INTEGER_COMPARE companion type.
  if ((m = t.match(/^Which is greater, (-?\d+) or (-?\d+)\?$/))) {
    return String(Math.max(parseInt(m[1], 10), parseInt(m[2], 10)));
  }
  return null;
}

/**
 * which_point tier ("...which letter marks the value of a + (b)?"): the
 * correct option is the lettered marker sitting at position a+b. Marker
 * letters and tick labels share x-coordinates in the rendered RadicalLine
 * SVG, so positions can be recovered without inspecting the visual params.
 */
async function solveWhichPoint(page, promptText) {
  const m = promptText.match(/which letter marks the value of (-?\d+) \+ \(?(-?\d+)\)?\?/);
  if (!m) return null;
  const target = parseInt(m[1], 10) + parseInt(m[2], 10);
  const positions = await page.locator('.problem-wrap svg.visual').first().evaluate((svg) => {
    const ticks = new Map();
    svg.querySelectorAll('.viz-tick-label').forEach((el) => {
      ticks.set(parseFloat(el.getAttribute('x')), Number(el.textContent));
    });
    const byLetter = {};
    svg.querySelectorAll('text.viz-label').forEach((el) => {
      byLetter[el.textContent.trim()] = ticks.get(parseFloat(el.getAttribute('x')));
    });
    return byLetter;
  });
  return Object.keys(positions).find((letter) => positions[letter] === target) ?? null;
}

/* ------------------------------------------------------------------ */
/* Journey helpers (same contracts as qa-f026-e2e-expansion.spec.js)  */
/* ------------------------------------------------------------------ */

async function registerFamily(page, tag) {
  const email = `synthetic-qa-${tag}-${Date.now()}@example.com`;
  await page.goto(`${baseURL}/login`);
  await page.getByRole('tab', { name: 'Create account' }).click();
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(PASSWORD);
  await page.getByLabel('Display name').fill(`Synthetic QA ${tag}`);
  await page.getByLabel('4-digit parent PIN').fill(PARENT_PIN);
  await page.getByLabel('I accept the Terms of Service.').check();
  await page.getByLabel(/I am the parent or guardian/).check();
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/learn/);

  await page.getByLabel('Learner nickname').fill(`QALearner${tag}`);
  await page.locator('#curriculum').click();
  const grade7 = page.getByRole('option', { name: /MCPS_MATH_7/ });
  await expect(grade7.first()).toBeVisible({ timeout: 10000 });
  await grade7.first().click();
  await page.getByRole('button', { name: 'Add learner' }).click();
  await expect(page.getByText(`QALearner${tag} is ready.`)).toBeVisible();
}

async function startSignedNumbersSession(page) {
  const learner = page.locator('#learner');
  await learner.click();
  await page.getByRole('option', { name: /QALearner/ }).click();
  await expect(learner).toContainText('QALearner');
  await expect(page.getByText('Explore Topics')).toBeVisible();
  await page.getByRole('button', { name: 'Numbers & operations', exact: true }).click();
  const skill = page.getByTestId('skill-choice').filter({ hasText: SKILL_NAME });
  await expect(skill).toHaveCount(1, { timeout: 10000 });
  await skill.click();
  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(page).toHaveURL(/\/learn\/[0-9a-f-]+$/);
  await expect(page.getByText('Current problem')).toBeVisible();
}

async function currentProblemText(page) {
  return ((await page.locator('.problem').textContent()) || '').trim();
}

async function currentStateLabel(page) {
  // Read the "Skill · State" paragraph element directly — regexing all of
  // main's textContent can absorb the next element's text when the following
  // prompt starts with a letter (SIGNED_NUMBERS prompts do).
  const el = page.locator('p', { hasText: `${SKILL_NAME} · ` }).first();
  if (!(await el.count())) return '';
  const text = (await el.textContent()) || '';
  const m = text.match(/·\s*([A-Za-z ]+?)\s*$/);
  return m ? m[1].trim() : '';
}

/** Settled "Skill · State" read; see qa-f026 for why polling is needed. */
async function settledStateLabel(page) {
  let prev = null;
  let stable = 0;
  const deadline = Date.now() + 12000;
  while (Date.now() < deadline) {
    const curr = await currentStateLabel(page);
    if (curr !== '' && curr === prev) {
      stable += 1;
      if (stable >= 2) return curr;
    } else {
      stable = 0;
    }
    prev = curr;
    await page.waitForTimeout(250);
  }
  return (await currentStateLabel(page)) || prev || '';
}

async function submitCurrentProblem(page, prevProblemText = null) {
  if (prevProblemText !== null) {
    try {
      await expect.poll(() => currentProblemText(page), { timeout: 15000 }).not.toBe(prevProblemText);
    } catch {
      // Identical prompt text may legitimately be re-served; proceed.
    }
  }
  const promptText = await currentProblemText(page);

  // On the final mastery-check solve the app replaces the problem card with
  // the completion screen, so accept either signal.
  const accepted = page
    .getByText('Correct. Keep going.')
    .or(page.getByRole('heading', { name: 'Skill complete' }));

  // Multiple-choice tier: pick the marker letter for a+b.
  const radios = page.getByRole('radio');
  if (await radios.count()) {
    const letter = await solveWhichPoint(page, promptText);
    expect(letter, `Cannot map which_point markers for: "${promptText}"`).toBeTruthy();
    await page.getByRole('radio', { name: letter, exact: true }).click();
    await page.getByRole('button', { name: 'Submit answer' }).click();
    await expect(accepted).toBeVisible({ timeout: 15000 });
    return promptText;
  }

  const answer = solveSignedNumbers(promptText);
  expect(answer, `No synthetic solver for problem: "${promptText}"`).toBeTruthy();
  await page.getByLabel('Your answer').fill(answer);
  await page.getByRole('button', { name: 'Submit answer' }).click();
  await expect(accepted).toBeVisible({ timeout: 15000 });
  return promptText;
}

/* ------------------------------------------------------------------ */
/* Widget locators                                                    */
/* ------------------------------------------------------------------ */

const guidedWidget = (page) => page.locator('section[data-mve-family="integer-addition"]');
const interactiveExplorer = (page) =>
  page.getByRole('region', { name: 'Guided integer number line exploration' });
const learnToggle = (page) => page.getByRole('button', { name: 'Learn the idea first' });

/** learnOpen persists across state changes — only open the panel once. */
async function openLearnPanel(page) {
  const toggle = learnToggle(page);
  await expect(toggle).toBeVisible();
  if ((await toggle.getAttribute('aria-expanded')) !== 'true') await toggle.click();
}

/** Parse "Find {a} + ({b})." out of the guided widget's practice line. */
async function guidedTask(page) {
  const text = (await guidedWidget(page)
    .getByText(/Worked practice, separate from independent assessment:/)
    .textContent()) || '';
  const m = text.match(/Find (-?\d+) \+ \((-?\d+)\)/);
  expect(m, `Guided task prompt missing/unexpected: "${text}"`).toBeTruthy();
  const a = parseInt(m[1], 10);
  const b = parseInt(m[2], 10);
  return { a, b, answer: a + b };
}

/* ------------------------------------------------------------------ */
/* 1. Guided practice integration + assessment isolation              */
/* ------------------------------------------------------------------ */

test('signed-integer guided practice mounts only in guided states and never scores mastery', async ({ page }) => {
  await registerFamily(page, 'intw');
  await startSignedNumbersSession(page);

  // DIAGNOSE is an assessment state: no learn panel, no guided widgets,
  // no hints — independent evidence only.
  await expect(page.getByText(`${SKILL_NAME} · Diagnose`)).toBeVisible({ timeout: 10000 });
  await expect(guidedWidget(page)).toHaveCount(0);
  await expect(interactiveExplorer(page)).toHaveCount(0);
  await expect(learnToggle(page)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Hint' })).toBeDisabled();
  await expect(page.getByRole('button', { name: "I don't understand" })).toBeDisabled();

  // One independent correct answer opens GUIDED_PRACTICE.
  const first = await submitCurrentProblem(page);
  await expect(page.getByText(`${SKILL_NAME} · Guided Practice`)).toBeVisible({ timeout: 10000 });
  await expect(page.getByRole('button', { name: 'Hint' })).toBeEnabled();

  // The standalone exploration mounts directly; the reviewed guided widget
  // lives inside the collapsible learn panel.
  await expect(interactiveExplorer(page)).toBeVisible();
  await openLearnPanel(page);
  await expect(guidedWidget(page)).toBeVisible();

  // Deterministic task: walk the marker to the sum, check direction sense.
  const { a, b, answer } = await guidedTask(page);
  const steps = Math.abs(b);
  const direction = b > 0 ? 'right' : 'left';
  const moveButton = guidedWidget(page).getByRole('button', {
    name: b > 0 ? 'Move right 1' : 'Move left 1',
  });
  for (let i = 0; i < steps; i++) await moveButton.click();
  await expect(guidedWidget(page).getByRole('status').first()).toContainText(
    `You are at ${answer}, ${steps} units ${direction} of your start at ${a}.`,
  );

  // Socratic scaffold unfolds one question at a time.
  await guidedWidget(page).getByRole('button', { name: 'Ask a guiding question' }).click();
  await expect(guidedWidget(page).getByText(`Where would you mark ${a} on a number line?`)).toBeVisible();

  // WRONG_DIRECTION misconception: a - b instead of a + b is diagnosed, not
  // merely marked wrong; the marker-vs-answer cross-check fires too.
  await guidedWidget(page).getByLabel('What is the sum?').fill(String(a - b));
  await guidedWidget(page).getByRole('button', { name: 'Check my reasoning' }).click();
  await expect(guidedWidget(page).getByRole('status').last()).toContainText(
    `Does adding ${b} mean moving right or left?`,
  );

  // Correcting to the real sum confirms both the arithmetic and the walk.
  await guidedWidget(page).getByLabel('What is the sum?').fill(String(answer));
  await guidedWidget(page).getByRole('button', { name: 'Check my reasoning' }).click();
  await expect(guidedWidget(page).getByRole('status').last()).toContainText(
    'Your sum is correct, and your marker walk confirms it.',
  );

  // "Try another task" serves a mathematically distinct seeded variant.
  const firstPrompt = await guidedWidget(page)
    .getByText(/Worked practice, separate from independent assessment:/)
    .textContent();
  await guidedWidget(page).getByRole('button', { name: 'Try another task' }).click();
  const secondTask = await guidedTask(page);
  expect(secondTask.a !== a || secondTask.b !== b).toBeTruthy();
  const secondPrompt = await guidedWidget(page)
    .getByText(/Worked practice, separate from independent assessment:/)
    .textContent();
  expect(secondPrompt).not.toBe(firstPrompt);

  // Solving on, the state machine reaches INDEPENDENT_PRACTICE — still not an
  // ASSESSMENT_STATE, so the lesson stays available, but both guided widgets
  // are gated to GUIDED_PRACTICE/REMEDIATION and must unmount.
  let prev = first;
  for (let i = 0; i < 6; i++) {
    if ((await settledStateLabel(page)) === 'Independent Practice') break;
    prev = await submitCurrentProblem(page, prev);
  }
  await expect(page.getByText(`${SKILL_NAME} · Independent Practice`)).toBeVisible({ timeout: 10000 });
  await expect(interactiveExplorer(page)).toHaveCount(0);
  await expect(guidedWidget(page)).toHaveCount(0);
  // The learn panel still exists in independent practice (lesson review is
  // allowed); opening it must reveal the lesson but never the guided widget.
  await openLearnPanel(page);
  await expect(page.getByText('Key words')).toBeVisible();
  await expect(guidedWidget(page)).toHaveCount(0);
});

/* ------------------------------------------------------------------ */
/* 2. Full journey to mastery with isolation at every transition      */
/* ------------------------------------------------------------------ */

test('signed-integer journey reaches mastery check and completes on independent evidence', async ({ page }) => {
  test.setTimeout(300000);
  await registerFamily(page, 'intm');
  await startSignedNumbersSession(page);

  const widgetSeen = { guided: false, explorer: false };
  const seen = [];
  let sawMasteryCheck = false;
  let completed = false;
  let prev = null;

  for (let i = 0; i < 22; i++) {
    const state = await settledStateLabel(page);
    seen.push(state);
    const mainText = (await page.locator('main').textContent()) || '';
    if (/Skill complete/.test(mainText)) {
      completed = true;
      break;
    }
    if (state === 'Mastery Check') {
      sawMasteryCheck = true;
      // Assessment isolation at the gate: no learn panel, no guided widgets,
      // no hints — the mastery decision rests on independent work only.
      await expect(guidedWidget(page)).toHaveCount(0);
      await expect(interactiveExplorer(page)).toHaveCount(0);
      await expect(learnToggle(page)).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'Hint' })).toBeDisabled();
      await expect(page.getByRole('button', { name: "I don't understand" })).toBeDisabled();
      prev = await submitCurrentProblem(page, prev);
      continue;
    }
    if (state === 'Guided Practice' && !widgetSeen.guided) {
      // Confirm both integer widgets are live at least once mid-journey.
      await expect(interactiveExplorer(page)).toBeVisible();
      await openLearnPanel(page);
      await expect(guidedWidget(page)).toBeVisible();
      widgetSeen.guided = true;
      widgetSeen.explorer = true;
    }
    if (state === 'Independent Practice' || state === 'Diagnose') {
      await expect(guidedWidget(page)).toHaveCount(0);
      await expect(interactiveExplorer(page)).toHaveCount(0);
    }
    prev = await submitCurrentProblem(page, prev);
  }

  expect(sawMasteryCheck, `Never reached Mastery Check. States: ${seen.join(' -> ')}`).toBe(true);
  expect(widgetSeen.guided, 'Guided integer widget never mounted in guided states').toBe(true);
  await expect(page.getByRole('heading', { name: 'Skill complete' })).toBeVisible({ timeout: 15000 });
});
