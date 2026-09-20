const { test, expect } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:3000';

test('synthetic family browser journey reaches tutoring and parent progress', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  const email = `synthetic-f017-${Date.now()}@example.com`;
  const password = 'SyntheticOnly!12345';

  await page.goto(baseURL);
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByLabel('Display name (registration only)').fill('Synthetic Pilot Parent');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByText('Choose a learner and curriculum, or start learning.')).toBeVisible();

  await page.getByLabel('Learner first name').fill('Synthetic Learner');
  const curriculum = page.getByLabel('Exact curriculum');
  await expect(curriculum.locator('option')).toHaveCount(3, { timeout: 10000 });
  const mcpsOption = curriculum.locator('option').filter({ hasText: 'MCPS_MATH_8' });
  await expect(mcpsOption).toHaveCount(1);
  await curriculum.selectOption(await mcpsOption.getAttribute('value'));
  await page.getByRole('button', { name: 'Add learner' }).click();
  await expect(page.getByText(/Synthetic Learner is ready with MCPS_MATH_8/)).toBeVisible();

  const learner = page.locator('#learner');
  await expect(learner).not.toHaveValue('');
  const skill = page.locator('#skill');
  await expect(skill.locator('option')).toHaveCount(10, { timeout: 10000 });
  const distributiveOption = skill.locator('option').filter({ hasText: 'M8.ALG.DIST · Distributive Property' });
  await expect(distributiveOption).toHaveCount(1);
  await skill.selectOption(await distributiveOption.getAttribute('value'));

  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(page).toHaveURL(/\/learn\/[0-9a-f-]+$/);
  await expect(page.getByRole('heading', { name: 'Current problem' })).toBeVisible();
  await expect(page.getByText('Help can support learning, but assisted success is not counted as independent mastery evidence.')).toBeVisible();

  const sessionUrl = page.url();
  const problemText = (await page.locator('#problem').textContent()) || '';
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
  await expect(page.getByRole('heading', { name: 'Parent Dashboard' })).toBeVisible();
  await expect(page.getByLabel('Child')).toContainText('Synthetic Learner');
  await expect(page.getByText('Progress below distinguishes assisted work from independent evidence.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Learning summary' })).toBeVisible();

  const outsider = await browser.newContext();
  const outsiderPage = await outsider.newPage();
  const outsiderEmail = `synthetic-outsider-${Date.now()}@example.com`;
  await outsiderPage.goto(baseURL);
  await outsiderPage.getByLabel('Email').fill(outsiderEmail);
  await outsiderPage.getByLabel('Password').fill(password);
  await outsiderPage.getByLabel('Display name (registration only)').fill('Synthetic Unrelated Parent');
  await outsiderPage.getByRole('button', { name: 'Create account' }).click();
  await expect(outsiderPage.getByText('Choose a learner and curriculum, or start learning.')).toBeVisible();
  await outsiderPage.goto(sessionUrl);
  await expect(outsiderPage.getByRole('alert')).toContainText('Learner not found');

  await outsider.close();
  await context.close();
});
