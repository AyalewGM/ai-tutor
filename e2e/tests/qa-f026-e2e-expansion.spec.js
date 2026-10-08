/**
 * QA F-026 E2E expansion — independent Quality Engineering coverage.
 *
 * Covers four previously untested learner surfaces, all with synthetic data:
 *   1. Learner scratch pad (ungraded scratch space)
 *   2. Step-work remediation (misconception diagnosis -> correction loop)
 *   3. Photo intake of written work (deterministic stub OCR)
 *   4. Independent-assessment restrictions (assistance gating in DIAGNOSE / MASTERY_CHECK)
 *
 * The photo happy path requires the backend OCR stub:
 *   PHOTO_OCR_PROVIDER=stub
 * (the deterministic StubProvider in app/services/photo_ocr.py). When the
 * provider is disabled, the graceful-degradation test runs instead.
 *
 * Run: cd e2e && E2E_BASE_URL=http://127.0.0.1:3000 npx playwright test qa-f026-e2e-expansion
 */
const { test, expect } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:3000';
const PHOTO_STUB_ENABLED = process.env.E2E_PHOTO_OCR === 'stub';

const PASSWORD = 'SyntheticOnly!12345';
const PARENT_PIN = '4821';

/* ------------------------------------------------------------------ */
/* Solvers: deterministic answers for seeded + generated problems      */
/* ------------------------------------------------------------------ */

const seedAnswers = {
  '3(x+4)': '3x+12',
  '2(x+5)': '2x+10',
  '4(x-3)': '4x-12',
  '5(x+2)': '5x+10',
  '-2(x+6)': '-2x-12',
  'x + 5 = 12': 'x=7',
  '2x + 3 = 11': 'x=4',
  '3(x+4)=24': 'x=4',
  '4(x-2)+3=19': 'x=6',
  '2(x+5)-4=18': 'x=6',
  'Simplify 2(x + 6).': '2x+12',
  'Simplify 5(x + 3).': '5x+15',
};

function solveDistributiveForm(text) {
  // Matches "3(x+4)", "Simplify 2(x + 6).", "-2(x-6)" etc.
  const m = text.match(/(-?\d+)\s*\(\s*x\s*([+-])\s*(\d+)\s*\)/);
  if (!m) return null;
  const a = parseInt(m[1], 10);
  const b = parseInt(m[3], 10) * (m[2] === '-' ? -1 : 1);
  const prod = a * b;
  return `${a}x${prod >= 0 ? '+' : ''}${prod}`;
}

function solveEquation(text) {
  const t = text.replace(/\s+/g, '');
  let m = t.match(/^x([+-])(\d+)=(-?\d+)$/);
  if (m) {
    const b = parseInt(m[2], 10) * (m[1] === '-' ? -1 : 1);
    return `x=${parseInt(m[3], 10) - b}`;
  }
  m = t.match(/^(-?\d+)x([+-])(\d+)=(-?\d+)$/);
  if (m) {
    const a = parseInt(m[1], 10);
    const b = parseInt(m[3], 10) * (m[2] === '-' ? -1 : 1);
    const c = parseInt(m[4], 10);
    const x = (c - b) / a;
    if (Number.isInteger(x)) return `x=${x}`;
    return null;
  }
  m = t.match(/^(-?\d+)\(x([+-])(\d+)\)=(-?\d+)$/);
  if (m) {
    const a = parseInt(m[1], 10);
    const b = parseInt(m[3], 10) * (m[2] === '-' ? -1 : 1);
    const c = parseInt(m[4], 10);
    const x = c / a - b;
    if (Number.isInteger(x)) return `x=${x}`;
    return null;
  }
  return null;
}

function solve(prompt) {
  const text = prompt.trim();
  if (seedAnswers[text]) return seedAnswers[text];
  return solveDistributiveForm(text) || solveEquation(text);
}

/** The DIST_001 partial-distribution error for a distributive prompt. */
function dist001WrongAnswer(prompt) {
  const m = prompt.match(/(-?\d+)\s*\(\s*x\s*([+-])\s*(\d+)\s*\)/);
  if (!m) return null;
  const a = parseInt(m[1], 10);
  const b = parseInt(m[3], 10) * (m[2] === '-' ? -1 : 1);
  return `${a}x${b >= 0 ? '+' : ''}${b}`;
}

/* ------------------------------------------------------------------ */
/* Shared journey helpers (same contracts as family-pilot.spec.js)      */
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
  const mcpsOption = page.getByRole('option', { name: /MCPS_MATH_8/ });
  await expect(mcpsOption.first()).toBeVisible({ timeout: 10000 });
  await mcpsOption.first().click();
  await page.getByRole('button', { name: 'Add learner' }).click();
  await expect(page.getByText(`QALearner${tag} is ready.`)).toBeVisible();
}

async function startDistributiveSession(page) {
  await expect(page.getByText('Explore Topics')).toBeVisible();
  await page.getByRole('button', { name: /Patterns & algebra/ }).click();
  const skill = page.getByTestId('skill-choice').filter({ hasText: 'Distributive Property' });
  await expect(skill).toHaveCount(1, { timeout: 10000 });
  await skill.click();
  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(page).toHaveURL(/\/learn\/[0-9a-f-]+$/);
  await expect(page.getByText('Current problem')).toBeVisible();
}

async function currentProblemText(page) {
  return ((await page.locator('.problem').textContent()) || '').trim();
}

async function submitStepOrAnswer(page, text) {
  // StepWork remounts per problem (key=problem.id); wait for whichever input
  // the current problem renders instead of racing the remount.
  const stepInput = page.getByLabel('Next work line');
  try {
    await stepInput.waitFor({ state: 'visible', timeout: 8000 });
    await stepInput.fill(text);
    await page.getByRole('button', { name: 'Check step' }).click();
  } catch {
    const answerInput = page.getByLabel('Your answer');
    await answerInput.waitFor({ state: 'visible', timeout: 8000 });
    await answerInput.fill(text);
    await page.getByRole('button', { name: 'Submit answer' }).click();
  }
}

async function solveCurrentProblem(page, prevProblemText = null) {
  // After "Correct. Keep going." the workspace transitions to the next problem.
  // Wait for the problem text to actually change before reading it; otherwise
  // the answer computed for the new problem can be submitted against the old
  // problem_id (or vice versa), poisoning the attempt as a step error.
  if (prevProblemText !== null) {
    try {
      await expect.poll(() => currentProblemText(page), { timeout: 15000 }).not.toBe(prevProblemText);
    } catch {
      // Text did not change; the selector may legitimately re-serve. Proceed.
    }
  }
  const problemText = await currentProblemText(page);
  const answer = solve(problemText);
  expect(answer, `No synthetic solver for problem: "${problemText}"`).toBeTruthy();
  await submitStepOrAnswer(page, answer);
  await expect(page.getByText('Correct. Keep going.')).toBeVisible({ timeout: 15000 });
  return problemText;
}

/** Drive the learner to a distributive prompt, solving others on the way. */
async function reachDistributiveProblem(page, maxSteps = 6) {
  let prev = null;
  for (let i = 0; i < maxSteps; i++) {
    const problemText = await currentProblemText(page);
    if (solveDistributiveForm(problemText)) return problemText;
    prev = await solveCurrentProblem(page, prev);
  }
  throw new Error('Could not reach a distributive problem within step budget');
}

/* ------------------------------------------------------------------ */
/* 1. Scratch pad: ungraded scratch space                              */
/* ------------------------------------------------------------------ */

test('scratch pad opens, draws, clears, hides, and never blocks solving', async ({ page }) => {
  await registerFamily(page, 'scratch');
  await startDistributiveSession(page);

  const toggle = page.getByRole('button', { name: 'Scratch pad' });
  await expect(toggle).toBeVisible();
  await toggle.click();

  const panel = page.locator('#scratchpad');
  await expect(panel).toBeVisible();

  // Tools: pen is the default, eraser toggles.
  const pen = page.getByRole('button', { name: 'Pen', exact: true });
  const eraser = page.getByRole('button', { name: 'Eraser', exact: true });
  await expect(pen).toHaveAttribute('aria-pressed', 'true');
  await eraser.click();
  await expect(eraser).toHaveAttribute('aria-pressed', 'true');
  await pen.click();
  await expect(pen).toHaveAttribute('aria-pressed', 'true');

  // Draw a stroke on the canvas and confirm pixels landed.
  const canvas = panel.locator('canvas');
  const box = await canvas.boundingBox();
  expect(box, 'scratch canvas has layout size').toBeTruthy();
  await page.mouse.move(box.x + 20, box.y + 20);
  await page.mouse.down();
  await page.mouse.move(box.x + 120, box.y + 80, { steps: 12 });
  await page.mouse.up();
  const drawnPixels = await canvas.evaluate((el) => {
    const ctx = el.getContext('2d');
    const data = ctx.getImageData(0, 0, el.width, el.height).data;
    let n = 0;
    for (let i = 3; i < data.length; i += 4) if (data[i] > 0) n++;
    return n;
  });
  expect(drawnPixels).toBeGreaterThan(0);

  // Clear removes the stroke.
  await page.getByRole('button', { name: 'Clear scratch pad' }).click();
  const clearedPixels = await canvas.evaluate((el) => {
    const ctx = el.getContext('2d');
    const data = ctx.getImageData(0, 0, el.width, el.height).data;
    let n = 0;
    for (let i = 3; i < data.length; i += 4) if (data[i] > 0) n++;
    return n;
  });
  expect(clearedPixels).toBe(0);

  // Hide collapses back to the toggle.
  await page.getByRole('button', { name: 'Hide scratch pad' }).click();
  await expect(panel).toBeHidden();
  await expect(toggle).toBeVisible();

  // Scratch work never interferes with grading: solve the problem normally.
  await solveCurrentProblem(page);
});

/* ------------------------------------------------------------------ */
/* 2. Step-work remediation: misconception diagnosed, then corrected   */
/* ------------------------------------------------------------------ */

test('step work rejects a DIST_001 partial distribution with specific feedback, then accepts the correction', async ({ page }) => {
  await registerFamily(page, 'remed');
  await startDistributiveSession(page);
  const problemText = await reachDistributiveProblem(page);

  const wrong = dist001WrongAnswer(problemText);
  expect(wrong, `Cannot build DIST_001 error for "${problemText}"`).toBeTruthy();
  const right = solveDistributiveForm(problemText);
  expect(right, `Cannot solve "${problemText}"`).toBeTruthy();
  expect(wrong).not.toBe(right);

  const stepInput = page.getByLabel('Next work line');
  await expect(stepInput).toBeVisible();

  // The classic partial-distribution error: 3(x+4) -> 3x+4.
  await stepInput.fill(wrong);
  await page.getByRole('button', { name: 'Check step' }).click();
  await expect(page.getByLabel('step rejected')).toBeVisible({ timeout: 10000 });
  await expect(page.getByText('Multiply the factor by every term inside the parentheses.')).toBeVisible();

  // The work history records the rejected attempt.
  const workList = page.getByRole('list', { name: 'Your work' });
  await expect(workList).toContainText(wrong.replace(/\s+/g, ''));

  // Correcting the step is accepted and solves the problem.
  await stepInput.fill(right);
  await page.getByRole('button', { name: 'Check step' }).click();
  await expect(page.getByLabel('step accepted')).toBeVisible({ timeout: 10000 });
  await expect(page.getByText('Correct. Keep going.')).toBeVisible({ timeout: 15000 });
});

/* ------------------------------------------------------------------ */
/* 3. Photo intake of written work                                     */
/* ------------------------------------------------------------------ */

// Minimal valid 1x1 PNG; content is irrelevant under the deterministic stub.
const TINY_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  'base64',
);

test('photo intake degrades gracefully when the OCR provider is disabled', async ({ page }) => {
  test.skip(PHOTO_STUB_ENABLED, 'provider enabled: covered by the stub happy-path test');
  await registerFamily(page, 'photod');
  await startDistributiveSession(page);
  await reachDistributiveProblem(page);

  // Bypass the file-chooser button; set files directly on the hidden input.
  await page.getByLabel('Photo of written work').setInputFiles({
    name: 'work.png',
    mimeType: 'image/png',
    buffer: TINY_PNG,
  });

  // Disabled provider -> 503 "Photo intake is not enabled" -> surfaced in the
  // workspace error alert; the session remains usable.
  await expect(page.getByRole('alert')).toContainText('Photo intake is not enabled', { timeout: 15000 });
  await expect(page.getByLabel('Next work line')).toBeVisible();
});

test('photo intake with stub OCR: scan review appears and checked lines flow to step work', async ({ page }) => {
  test.skip(!PHOTO_STUB_ENABLED, 'requires PHOTO_OCR_PROVIDER=stub (E2E_PHOTO_OCR=stub)');
  await registerFamily(page, 'photoh');
  await startDistributiveSession(page);
  await reachDistributiveProblem(page);

  // Bypass the file-chooser button; set files directly on the hidden input.
  await page.getByLabel('Photo of written work').setInputFiles({
    name: 'work.png',
    mimeType: 'image/png',
    buffer: TINY_PNG,
  });

  // Deterministic stub returns two lines; the second needs review.
  const review = page.getByTestId('scan-review');
  await expect(review).toBeVisible({ timeout: 15000 });
  await expect(review.getByRole('textbox', { name: 'Scanned line 1' })).toHaveValue('3x + 12 = 30');
  await expect(review.getByRole('textbox', { name: 'Scanned line 2' })).toHaveValue('3x = 18');

  // Confirming submits each line through the deterministic step checker.
  // MathText renders via KaTeX with split text nodes, so compare with
  // whitespace normalized.
  await review.getByRole('button', { name: 'Check these steps' }).click();
  const workList = page.getByRole('list', { name: 'Your work' });
  await expect(workList).toContainText(/3x.*12.*30/, { timeout: 15000 });
  const workText = (await workList.textContent()) || '';
  const normalized = workText.replace(/\s+/g, '');
  expect(normalized).toContain('3x+12=30');
  expect(normalized).toContain('3x=18');
  await expect(review).toBeHidden();
});

/* ------------------------------------------------------------------ */
/* 4. Independent-assessment restrictions                              */
/*                                                                     */
/* Architectural rule under test: guided assistance must not be        */
/* available during assessment states (DIAGNOSE, MASTERY_CHECK), and   */
/* learn content is hidden there so worked examples cannot contaminate */
/* evidence. app/services/hint_policy.py :: ASSESSMENT_STATES          */
/* ------------------------------------------------------------------ */

test('diagnose state restricts guided assistance; guided practice restores it', async ({ page }) => {
  await registerFamily(page, 'assess');
  await startDistributiveSession(page);

  // New sessions open in DIAGNOSE, an assessment state. The state badge and
  // the "Skill · State" label both render the state name; match precisely.
  await expect(page.getByText('Diagnose', { exact: true })).toBeVisible({ timeout: 10000 });
  await expect(page.getByRole('button', { name: 'Hint' })).toBeDisabled();
  await expect(page.getByRole('button', { name: "I don't understand" })).toBeDisabled();

  // One correct independent answer moves to GUIDED_PRACTICE: help returns.
  // (The "Learn the idea first" panel is skill-content dependent — the seeded
  // distributive skill ships no learn_content — so only the hint gating, which
  // is state-driven, is asserted here.)
  await solveCurrentProblem(page);
  await expect(page.getByText(/· Guided Practice/)).toBeVisible({ timeout: 10000 });
  await expect(page.getByRole('button', { name: 'Hint' })).toBeEnabled();
  await expect(page.getByRole('button', { name: "I don't understand" })).toBeEnabled();
});

test('assisted success is recorded separately from independent mastery evidence', async ({ page }) => {
  await registerFamily(page, 'assist');
  await startDistributiveSession(page);

  // Reach guided practice where hints are allowed.
  const firstProblem = await solveCurrentProblem(page);
  await expect(page.getByText(/Guided Practice/)).toBeVisible({ timeout: 10000 });

  const independentValue = page.getByText('Independent correct').locator('..').locator('p.mt-1');
  const assistedValue = page.getByText('Assisted successes').locator('..').locator('p.mt-1');
  const independentBefore = await independentValue.textContent();
  const assistedBefore = await assistedValue.textContent();

  // Take a hint, then answer correctly: the success must count as assisted.
  // The hint message replaces the "Correct. Keep going." status text.
  const statusPara = page.locator('p[aria-live="polite"]');
  await page.getByRole('button', { name: 'Hint' }).click();
  await expect(statusPara).not.toHaveText('Correct. Keep going.', { timeout: 10000 });
  await solveCurrentProblem(page, firstProblem);

  // The progress panel refreshes asynchronously after submit; wait for the
  // assisted counter to move, then assert independent evidence did not.
  await expect(assistedValue).not.toHaveText(assistedBefore ?? '', { timeout: 15000 });
  await expect(independentValue).toHaveText(independentBefore ?? '');
});

/** Read the "Skill · State" label, e.g. "Mastery Check". */
async function currentStateLabel(page) {
  const mainText = (await page.locator('main').textContent()) || '';
  const m = mainText.match(/Distributive Property · ([A-Za-z ]+)/);
  return m ? m[1].trim() : '';
}

/**
 * The state label can show a stale value briefly after a solve while the
 * workspace reloads; poll until it is non-empty and stable across reads so
 * MASTERY_CHECK is never missed or misread.
 */
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

test('mastery check re-imposes assessment restrictions and completes on independent evidence', async ({ page }) => {
  test.setTimeout(300000);
  await registerFamily(page, 'mastery');
  await startDistributiveSession(page);

  // Drive independent correct answers until the state machine opens the check.
  // The state is read at the top of each iteration, after the previous solve
  // has confirmed the next problem loaded — so MASTERY_CHECK is observed
  // before it can be solved through, and we never attempt to solve on the
  // completion screen.
  // BKT-lite needs roughly a dozen correct for the 0.85 gate; budget generously
  // and record the trajectory for failure evidence.
  const seen = [];
  let sawMasteryCheck = false;
  let prev = null;
  for (let i = 0; i < 22; i++) {
    const state = await settledStateLabel(page);
    seen.push(state);
    if (state === 'Mastery Check') {
      sawMasteryCheck = true;
      break;
    }
    const mainText = (await page.locator('main').textContent()) || '';
    if (/Skill complete/.test(mainText)) break;
    prev = await solveCurrentProblem(page, prev);
  }
  expect(sawMasteryCheck, `state machine never opened MASTERY_CHECK; trajectory: ${[...new Set(seen)].join(' -> ')}`).toBe(true);

  // Assessment restrictions are back: no hints.
  await expect(page.getByRole('button', { name: 'Hint' })).toBeDisabled();
  await expect(page.getByRole('button', { name: "I don't understand" })).toBeDisabled();

  // Solving the check independently completes the skill.
  await solveCurrentProblem(page);
  await expect(page.getByText('Skill complete')).toBeVisible({ timeout: 15000 });
  await expect(page.getByText('You answered correctly and independently in the mastery check.')).toBeVisible();
});
