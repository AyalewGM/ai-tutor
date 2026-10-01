const { test, expect } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:3000';

test('synthetic family browser journey reaches tutoring and parent progress', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  const email = `synthetic-f017-${Date.now()}@example.com`;
  const password = 'SyntheticOnly!12345';
  const parentPin = '4821';

  await page.goto(`${baseURL}/login`);
  await page.getByRole('tab', { name: 'Create account' }).click();
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByLabel('Display name').fill('Synthetic Pilot Parent');
  await page.getByLabel('4-digit parent PIN').fill(parentPin);
  await page.getByLabel('I accept the Terms of Service.').check();
  await page.getByLabel(/I am the parent or guardian/).check();
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/learn/);

  await page.getByLabel('Learner nickname').fill('SyntheticLearner');
  await page.locator('#curriculum').click();
  const mcpsOption = page.getByRole('option', { name: /MCPS_MATH_8/ });
  await expect(mcpsOption.first()).toBeVisible({ timeout: 10000 });
  await mcpsOption.first().click();
  await page.getByRole('button', { name: 'Add learner' }).click();
  await expect(page.getByText('SyntheticLearner is ready.')).toBeVisible();

  const learner = page.locator('#learner');
  await expect(learner).toContainText('SyntheticLearner');

  // F-026 release gate: a learner reaches a chosen skill through the
  // child-friendly Explore Topics path, not an administrative skill selector.
  await expect(page.getByText('Explore Topics')).toBeVisible();
  await page.getByRole('button', { name: /Patterns & algebra/ }).click();
  const distributiveSkill = page.getByTestId('skill-choice').filter({ hasText: 'Distributive Property' });
  await expect(distributiveSkill).toHaveCount(1, { timeout: 10000 });
  await expect(distributiveSkill).toBeVisible();
  await distributiveSkill.click();

  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(page).toHaveURL(/\/learn\/[0-9a-f-]+$/);
  await expect(page.getByText('Current problem')).toBeVisible();
  await expect(page.getByText('Help can support learning, but assisted success is not counted as independent mastery evidence.')).toBeVisible();

  const sessionUrl = page.url();
  const problemText = (await page.locator('.problem').textContent()) || '';
  const knownAnswers = {
    '3(x+4)': '3x+12',
    '2(x+5)': '2x+10',
    '4(x-3)': '4x-12',
    '5(x+2)': '5x+10',
    '-2(x+6)': '-2x-12',
    'x + 5 = 12': 'x=7',
    '2x + 3 = 11': 'x=4',
    '3(x+4)=24': 'x=4',
    '4(x-2)+3=19': 'x=6',
    '2(x+5)-4=18': 'x=6'
  };
  const answer = knownAnswers[problemText.trim()];
  expect(answer, `No synthetic answer fixture for problem: ${problemText}`).toBeTruthy();
  await page.getByLabel('Your answer').fill(answer);
  await page.getByRole('button', { name: 'Submit answer' }).click();
  await expect(page.getByText('Correct. Keep going.')).toBeVisible();

  await page.goto(`${baseURL}/parent`);
  await expect(page.getByRole('heading', { name: 'Family learning overview' })).toBeVisible();
  await page.getByLabel('Parent PIN').fill(parentPin);
  await page.getByRole('button', { name: 'Unlock parent view' }).click();
  await expect(page.getByLabel('Student', { exact: true })).toContainText('SyntheticLearner');
  await expect(page.getByText('Topics mastered')).toBeVisible();

  const outsider = await browser.newContext();
  const outsiderPage = await outsider.newPage();
  const outsiderEmail = `synthetic-outsider-${Date.now()}@example.com`;
  await outsiderPage.goto(`${baseURL}/login`);
  await outsiderPage.getByRole('tab', { name: 'Create account' }).click();
  await outsiderPage.getByLabel('Email').fill(outsiderEmail);
  await outsiderPage.getByLabel('Password').fill(password);
  await outsiderPage.getByLabel('Display name').fill('Synthetic Unrelated Parent');
  await outsiderPage.getByLabel('4-digit parent PIN').fill(parentPin);
  await outsiderPage.getByLabel('I accept the Terms of Service.').check();
  await outsiderPage.getByLabel(/I am the parent or guardian/).check();
  await outsiderPage.getByRole('button', { name: 'Create account' }).click();
  await expect(outsiderPage).toHaveURL(/\/learn/);
  await outsiderPage.goto(sessionUrl);
  await expect(outsiderPage.getByRole('alert')).toContainText('Learner not found');

  await outsider.close();
  await context.close();
});
