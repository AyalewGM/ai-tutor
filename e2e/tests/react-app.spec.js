const { test, expect } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:3000';

const knownAnswers = {
  '3(x+4)': '3x+12',
  '2(x+5)': '2x+10',
  '4(x-3)': '4x-12',
  '5(x+2)': '5x+10',
  '-2(x+6)': '-2x-12',
  'Simplify 2(x + 6).': '2x+12',
  'Simplify 5(x + 3).': '5x+15',
};

function solve(prompt) {
  const text = prompt.trim();
  if (knownAnswers[text]) return knownAnswers[text];
  // Generated SIMPLIFY_EXPRESSION variants: a(x+b) / a(x-b) / -a(x+b)
  const match = text.match(/^Simplify\s+(-?\d+)\(x\s*([+-])\s*(\d+)\)\.?$/);
  if (match) {
    const a = parseInt(match[1], 10);
    const b = parseInt(match[3], 10) * (match[2] === '-' ? -1 : 1);
    const prod = a * b;
    return `${a}x${prod >= 0 ? '+' : ''}${prod}`;
  }
  return null;
}

test('react learner journey: register, practice, earn badge, view badges and skill map', async ({ page }) => {
  const email = `synthetic-react-${Date.now()}@example.com`;
  const password = 'SyntheticOnly!12345';

  await page.goto(`${baseURL}/app/login`);
  await page.getByRole('tab', { name: 'Create account' }).click();
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByLabel('Display name').fill('Synthetic React Parent');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/app\/learn/);

  await page.getByLabel('Learner first name').fill('React Learner');
  const curriculum = page.locator('#curriculum');
  await expect(curriculum.locator('option').filter({ hasText: 'MCPS_MATH_8' })).toHaveCount(1, { timeout: 10000 });
  const mcpsOption = curriculum.locator('option').filter({ hasText: 'MCPS_MATH_8' });
  await curriculum.selectOption(await mcpsOption.getAttribute('value'));
  await page.getByRole('button', { name: 'Add learner' }).click();
  await expect(page.getByText('React Learner is ready.')).toBeVisible();

  // F-022: parent dashboard uses the same authorized family data and keeps
  // independent evidence visibly separate from assisted success.
  await page.getByRole('link', { name: 'Parent' }).click();
  await expect(page).toHaveURL(/\/app\/parent$/);
  await expect(page.getByRole('heading', { name: 'Family learning overview' })).toBeVisible();
  await expect(page.getByLabel('Learner', { exact: true })).toContainText('React Learner');
  await expect(page.getByText('Assisted success is shown separately')).toBeVisible();
  await page.getByRole('link', { name: 'Practice' }).click();

  const learner = page.locator('#learner');
  const learnerOption = learner.locator('option').filter({ hasText: 'React Learner' });
  await learner.selectOption(await learnerOption.getAttribute('value'));
  const skill = page.locator('#skill');
  await expect(skill.locator('option')).not.toHaveCount(1, { timeout: 10000 });
  const distOption = skill.locator('option').filter({ hasText: 'M8.ALG.DIST · Distributive Property' });
  await skill.selectOption(await distOption.getAttribute('value'));

  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(page).toHaveURL(/\/app\/learn\/[0-9a-f-]+$/);
  await expect(page.getByRole('heading', { name: 'Current problem' })).toBeVisible();

  const prompt = (await page.locator('.problem').textContent()) || '';
  const answer = solve(prompt);
  expect(answer, `No synthetic answer for problem: ${prompt}`).toBeTruthy();
  await page.getByLabel('Your answer').fill(answer);
  await page.getByRole('button', { name: 'Submit answer' }).click();
  await expect(page.getByText('Correct. Keep going.')).toBeVisible();

  // First correct answer mints the First Steps badge and shows the toast.
  await expect(page.locator('.badge-toast')).toContainText('First Steps');
  await expect(page.locator('.badge-shelf')).toContainText('First Steps');

  // Badge collection page shows earned vs locked badges.
  await page.getByRole('link', { name: 'View all' }).click();
  await expect(page).toHaveURL(/\/badges$/);
  await expect(page.getByRole('heading', { name: 'Badge collection' })).toBeVisible();
  const firstSteps = page.locator('.badge-card', { hasText: 'First Steps' });
  await expect(firstSteps).not.toHaveClass(/locked/);
  const locked = page.locator('.badge-card.locked');
  await expect(locked.first()).toBeVisible();

  // Skill map renders the full curriculum grid with an active tile.
  await page.getByRole('link', { name: 'Back to practice' }).click();
  await page.getByRole('link', { name: 'Skill map' }).click();
  await expect(page).toHaveURL(/\/map$/);
  await expect(page.getByRole('heading', { name: 'Skill map' })).toBeVisible();
  await expect(page.locator('.map-tile').first()).toBeVisible();
  expect(await page.locator('.map-tile').count()).toBeGreaterThanOrEqual(9);
  await expect(page.locator('.map-tile.active')).toHaveCount(1);
  await expect(page.locator('.map-tile.active')).toContainText('Distributive Property');
});
