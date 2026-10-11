/**
 * Draft-gated Workspace journey for the MTH1W equation-equivalence slice.
 *
 * Run: node e2e/equation-learning-flow-browser.mjs
 */
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { chromium } from '@playwright/test';
import { createServer } from '../frontend/node_modules/vite/dist/node/index.js';

const frontend = fileURLToPath(new URL('../frontend/', import.meta.url));
const directory = await mkdtemp(path.join(frontend, '.equation-flow-browser-'));
let server;
let browser;

try {
  await writeFile(path.join(directory, 'index.html'), '<html lang="en"><head><title>Equation flow integration</title></head><body><div id="root"></div><script type="module" src="./entry.tsx"></script></body></html>');
  await writeFile(path.join(directory, 'entry.tsx'), `
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Workspace from '/src/pages/Workspace';
import '/src/styles.css';

let workspaceState = 'GUIDED_PRACTICE';
const learn = {
  summary: 'Use BEDMAS to read structure, then apply inverse operations to both complete sides.',
  examples: [{
    title: 'Keep equality visible',
    steps: ['Subtract the same expression from both sides.', 'Divide both complete sides by the nonzero coefficient.', 'Verify by substitution.'],
    answer: 'x = -3',
  }],
  key_terms: [{ term: 'equivalent equations', definition: 'Equations with exactly the same solution set.' }],
  watch_out: ['A term never changes sides by magic; apply an inverse operation to both sides.'],
};

function payload() {
  const guided = workspaceState === 'GUIDED_PRACTICE';
  return {
    session_id: '00000000-0000-4000-8000-000000000337',
    state: workspaceState,
    learner: { id: '00000000-0000-4000-8000-000000000001', first_name: 'Synthetic', grade_level: '9', avatar_id: 'avatar-1' },
    curriculum: { id: '00000000-0000-4000-8000-000000000009', code: 'MTH1W', name: 'Grade 9 Mathematics (MTH1W)', jurisdiction: 'Ontario, Canada' },
    focus: {
      primary_skill_id: '00000000-0000-4000-8000-000000000003',
      primary_skill_name: 'Multi-Step Equations with Variables on Both Sides',
      active_skill_id: '00000000-0000-4000-8000-000000000003',
      skill_name: 'Multi-Step Equations with Variables on Both Sides',
      in_remediation: false,
      remediation_reason: null,
      learn: guided ? learn : null,
    },
    problem: {
      id: '00000000-0000-4000-8000-000000000777',
      prompt: 'Solve -7x + 2 = -x + 20. Give an exact value and verify by substitution.',
      difficulty: 4,
      visual: null,
      answer_kind: 'FREE_TEXT',
      choices: null,
      problem_type: 'SOLVE_EQUATION',
      supports_steps: false,
    },
    coaching_message: null,
    allowed_actions: guided ? ['SUBMIT_ANSWER', 'REQUEST_HINT', 'I_DONT_UNDERSTAND'] : ['SUBMIT_ANSWER'],
    evidence: { mastery_score: 0, confidence_score: 0, independent_correct_count: 0, independent_attempt_count: 0, hinted_correct_count: 0, smartscore: 0, streak_count: 0, mastery_level: 'practicing' },
    reviews_due: [],
    awards: [],
    recommended_next: null,
    streak_days: 0,
    growth: null,
    daily_goal: null,
  };
}

window.fetch = async (input) => {
  const url = String(input);
  const body = url.includes('/learner-workspace/sessions/') ? payload() : {};
  return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
};

function Harness() {
  const [revision, setRevision] = useState(0);
  const switchState = () => {
    workspaceState = workspaceState === 'GUIDED_PRACTICE' ? 'INDEPENDENT_PRACTICE' : 'GUIDED_PRACTICE';
    setRevision(value => value + 1);
  };
  return <MemoryRouter initialEntries={['/learn/00000000-0000-4000-8000-000000000337']}>
    <button type="button" onClick={switchState}>Switch workspace state</button>
    <Routes key={revision}><Route path="/learn/:sessionId" element={<Workspace />} /></Routes>
  </MemoryRouter>;
}

createRoot(document.getElementById('root')!).render(<Harness />);
`);

  server = await createServer({
    root: frontend,
    define: {
      'import.meta.env.VITE_ENABLE_DRAFT_MTH1W_EQUATION_FLOW': JSON.stringify('true'),
    },
    server: { host: '127.0.0.1', port: 0 },
  });
  await server.listen();
  const address = server.httpServer.address();
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ reducedMotion: 'reduce' });
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(`http://127.0.0.1:${address.port}/${path.basename(directory)}/index.html`);

  const guided = page.getByRole('region', { name: 'Guided exact equation equivalence exploration' });
  await guided.waitFor();
  assert.match(await guided.textContent(), /does not count toward mastery/);
  assert.match(await guided.textContent(), /−7x \+ 2 = −x \+ 20/);
  await page.getByRole('button', { name: 'Learn the idea first' }).click();
  assert.match(await page.locator('main').textContent(), /BEDMAS/);
  assert.match(await page.locator('main').textContent(), /Answer: x = -3/);

  await guided.getByRole('button', { name: 'Try changing only one side' }).focus();
  await page.keyboard.press('Enter');
  assert.match(await guided.getByRole('status').first().textContent(), /No change made/);
  assert.match(await guided.textContent(), /Support stage:\s*MODELED/);
  await guided.getByRole('button', { name: 'Add x to both sides' }).click();
  await guided.getByRole('button', { name: 'Subtract 2 from both sides' }).click();
  await guided.getByRole('button', { name: 'Multiply both sides by -1\/6' }).click();
  assert.match(await guided.getByRole('img', { name: /Equation balance/ }).getAttribute('aria-label'), /Left side x\. Right side −3/);
  await guided.getByRole('button', { name: 'The same valid operation was applied to both complete sides' }).click();
  assert.match(await guided.textContent(), /INDEPENDENT READINESS/);
  await guided.getByRole('button', { name: 'Multiply both sides by 2\/3' }).click();
  const guidedTextAfterError = await guided.textContent();
  assert.match(guidedTextAfterError, /which reciprocal makes the coefficient of x equal to 1/);
  assert.doesNotMatch(guidedTextAfterError, /The solution is|answer is −6/);
  await guided.getByRole('button', { name: 'Multiply both sides by 3\/2' }).click();
  assert.match(await guided.textContent(), /verify the isolated value by substitution/);
  assert.ok(await guided.getByRole('table', { name: 'Equivalent-equation transformation table' }).isVisible());

  await page.getByRole('button', { name: 'Switch workspace state' }).click();
  await page.getByText('Multi-Step Equations with Variables on Both Sides · Independent Practice').waitFor();
  assert.equal(await guided.count(), 0);
  assert.equal(await page.getByRole('button', { name: 'Learn the idea first' }).count(), 0);
  assert.equal(await page.getByText('Answer: x = -3').count(), 0);
  assert.equal(await page.getByRole('button', { name: 'Hint' }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: "I don't understand" }).isDisabled(), true);

  await page.getByRole('button', { name: 'Switch workspace state' }).click();
  await guided.waitFor();
  assert.match(await guided.textContent(), /Support stage:\s*MODELED/);
  assert.match(await guided.getByRole('status').first().textContent(), /Starting equation/);
  assert.deepEqual(pageErrors, []);
  console.log('PASS: exact MTH1W route, negative/two-sided transformations, targeted misconception recovery, fresh fractional exit, keyboard and reduced-motion access, independent-assessment isolation, and fresh guided remount.');
} finally {
  await browser?.close();
  await server?.close();
  await rm(directory, { recursive: true, force: true });
}
