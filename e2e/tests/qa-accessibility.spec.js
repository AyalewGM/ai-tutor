/**
 * QA accessibility regression — non-MVE learner interfaces.
 *
 * 1. MarbleBag color-encoding (WCAG 1.4.1): the marble-bag visual must encode
 *    marble color identity in text (a legend mapping swatches to color names),
 *    not in hue alone. Regression test for the color-only encoding defect.
 * 2. Learner workspace keyboard/a11y smoke: key controls are keyboard
 *    reachable with accessible names; the problem visual exposes its name.
 *
 * Deterministic synthetic data only. The marble problem is seeded by
 * scripts/seed_sprint1.py ("Marble Bag Probability (QA)" skill) and is always
 * served first for a fresh learner (unseen seeded problems take priority
 * over generation in problem selection).
 *
 * Run: cd e2e && E2E_BASE_URL=http://127.0.0.1:3000 npx playwright test qa-accessibility
 */
const { test, expect } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:3000';

const PASSWORD = 'SyntheticOnly!12345';
const PARENT_PIN = '4821';

async function registerFamily(page, tag) {
  const email = `synthetic-a11y-${tag}-${Date.now()}@example.com`;
  await page.goto(`${baseURL}/login`);
  await page.getByRole('tab', { name: 'Create account' }).click();
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(PASSWORD);
  await page.getByLabel('Display name').fill(`Synthetic A11y ${tag}`);
  await page.getByLabel('4-digit parent PIN').fill(PARENT_PIN);
  await page.getByLabel('I accept the Terms of Service.').check();
  await page.getByLabel(/I am the parent or guardian/).check();
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/learn/);

  await page.getByLabel('Learner nickname').fill(`A11yLearner${tag}`);
  await page.locator('#curriculum').click();
  const mcpsOption = page.getByRole('option', { name: /MCPS_MATH_8/ });
  await expect(mcpsOption.first()).toBeVisible({ timeout: 10000 });
  await mcpsOption.first().click();
  await page.getByRole('button', { name: 'Add learner' }).click();
  await expect(page.getByText(`A11yLearner${tag} is ready.`)).toBeVisible();
}

async function startMarbleSession(page) {
  await expect(page.getByText('Explore Topics')).toBeVisible();
  const skill = page.getByTestId('skill-choice').filter({ hasText: 'Marble Bag Probability' });
  await expect(skill).toHaveCount(1, { timeout: 10000 });
  await skill.click();
  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(page).toHaveURL(/\/learn\/[0-9a-f-]+$/);
  await expect(page.getByText('Current problem')).toBeVisible();
}

/* ------------------------------------------------------------------ */
/* 1. MarbleBag: color identity must not be encoded by hue alone        */
/* ------------------------------------------------------------------ */

test('marble bag visual names each color in text, not color alone', async ({ page }) => {
  await registerFamily(page, 'marble');
  await startMarbleSession(page);

  // The seeded marble problem is served first; its visual must be present.
  const visual = page.locator('svg.visual').first();
  await expect(visual).toBeVisible({ timeout: 15000 });
  await expect(visual).toHaveAttribute('aria-label', /blue.*red/i);

  // WCAG 1.4.1: every distinct marble color has a *text* label in the
  // legend. A colorblind learner can map "blue" from the prompt to the
  // right marbles without distinguishing hues.
  // (Legend text is CSS-capitalized; match case-insensitively.)
  const legendBlue = visual.getByText(/^blue$/i);
  const legendRed = visual.getByText(/^red$/i);
  await expect(legendBlue).toHaveCount(1);
  await expect(legendRed).toHaveCount(1);

  // The legend labels are real text nodes paired with their swatches —
  // not tooltips, not aria-only content.
  await expect(legendBlue).toBeVisible();
  await expect(legendRed).toBeVisible();

  // Sanity: the marbles themselves still render (8 circles for 8 marbles).
  // Legend swatches add 2 more circles (one per distinct color).
  await expect(visual.locator('circle')).toHaveCount(10);
});

/* ------------------------------------------------------------------ */
/* 2. Learner workspace keyboard / accessible-name smoke                */
/* ------------------------------------------------------------------ */

test('learner workspace controls are keyboard reachable with accessible names', async ({ page }) => {
  await registerFamily(page, 'kbd');
  await startMarbleSession(page);
  await expect(page.getByText('Current problem')).toBeVisible();

  // The problem's text input (answer or step-work) must expose a
  // non-empty accessible name, be focusable, and Tab must move focus to
  // another interactive element rather than losing it to <body>.
  const answerInput = page.locator('main').getByRole('textbox').first();
  await answerInput.waitFor({ state: 'visible', timeout: 15000 });
  const accessibleName =
    (await answerInput.getAttribute('aria-label')) ||
    (await answerInput.getAttribute('placeholder')) ||
    '';
  expect(accessibleName.trim().length).toBeGreaterThan(0);
  await answerInput.focus();
  await expect(answerInput).toBeFocused();
  await page.keyboard.press('Tab');
  const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
  expect(['BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'A']).toContain(focusedTag);

  // The submit control exposes its accessible name.
  const submit = page.getByRole('button', { name: /^(Submit answer|Check step)$/ });
  await expect(submit.first()).toBeVisible();

  // Hint control exposes its name to assistive tech even when disabled
  // (assessment states disable it; it must not vanish).
  const hintButton = page.getByRole('button', { name: 'Hint' });
  await expect(hintButton).toBeVisible();
});
