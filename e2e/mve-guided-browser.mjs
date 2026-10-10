/** Standalone component browser check: node e2e/mve-guided-browser.mjs */
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { chromium } from '@playwright/test';
import { createServer } from '../frontend/node_modules/vite/dist/node/index.js';

const frontend = fileURLToPath(new URL('../frontend/', import.meta.url));
const directory = await mkdtemp(path.join(frontend, '.mve-browser-'));
let server, browser;
try {
  await writeFile(path.join(directory, 'index.html'), '<html lang="en"><head><title>MVE test</title></head><body><div id="root"></div><script type="module" src="./entry.tsx"></script></body></html>');
  await writeFile(path.join(directory, 'entry.tsx'), `
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { InteractiveLinearExplorer } from '/src/mve/InteractiveLinearExplorer';
import { InteractiveIntegerNumberLine } from '/src/mve/InteractiveIntegerNumberLine';
import { InteractiveEquationBalance } from '/src/mve/InteractiveEquationBalance';
import '/src/styles.css';
function Harness() {
 const [assessment, setAssessment] = useState(false);
 const [event, setEvent] = useState('');
 return <><button onClick={() => setAssessment(!assessment)}>Toggle assessment</button>
 <InteractiveLinearExplorer independentAssessment={assessment} onMathEvent={e => setEvent(JSON.stringify(e))} />
 <InteractiveIntegerNumberLine independentAssessment={assessment} />
 <InteractiveEquationBalance independentAssessment={assessment} />
 <output aria-label="Last semantic event">{event}</output></>;
}
createRoot(document.getElementById('root')!).render(<Harness />);`);
  server = await createServer({ root: frontend, server: { host: '127.0.0.1', port: 0 } });
  await server.listen();
  const address = server.httpServer.address();
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ reducedMotion: 'reduce' });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`http://127.0.0.1:${address.port}/${path.basename(directory)}/index.html`);
  const slope = page.getByRole('region', { name: 'Guided slope and intercept exploration' });
  await slope.waitFor();
  const rise = page.getByLabel('Rise (signed change in y):');
  await rise.focus();
  await page.keyboard.press('ArrowRight');
  assert.equal(await rise.inputValue(), '3');
  assert.equal(JSON.parse(await page.getByLabel('Last semantic event').textContent()).rise, 3);
  assert.ok((await slope.getByRole('status').first().textContent()).includes('Slope is 1.'));
  const run = page.getByLabel('Run (positive change in x):');
  await run.focus(); await page.keyboard.press('Home');
  assert.equal(await run.inputValue(), '1');
  await page.keyboard.press('ArrowLeft');
  assert.equal(await run.inputValue(), '1');
  await page.getByLabel('Slope as an integer or fraction').fill('2/4');
  await page.getByRole('button', { name: 'Check slope' }).click();
  assert.ok((await slope.getByRole('status').last().textContent()).startsWith('Correct'));
  const balance = page.getByRole('region', { name: 'Guided equation balance exploration' });
  for (let i = 0; i < 4; i++) await balance.getByRole('button', { name: 'Subtract 1 from both sides' }).click();
  await balance.getByRole('button', { name: 'Divide both sides by 2' }).focus();
  await page.keyboard.press('Enter');
  assert.ok((await balance.getByRole('status').first().textContent()).startsWith('x = 3.'));
  await balance.getByRole('button', { name: 'Undo balance step' }).click();
  assert.ok((await balance.getByRole('status').first().textContent()).startsWith('2x = 6.'));
  await page.getByRole('button', { name: 'Toggle assessment' }).click();
  assert.equal(await page.getByRole('slider').count(), 0);
  assert.equal(await slope.count(), 0);
  assert.equal(await balance.count(), 0);
  assert.equal(await page.getByRole('region', { name: 'Guided integer number line exploration' }).count(), 0);
  await page.getByRole('button', { name: 'Toggle assessment' }).click();
  assert.equal(await rise.inputValue(), '2');
  assert.ok((await balance.getByRole('status').first().textContent()).startsWith('2x + 4 = 10.'));
  assert.equal(await page.getByLabel('Slope as an integer or fraction').inputValue(), '');
  const integer = page.getByLabel('Starting integer:');
  await integer.focus(); await page.keyboard.press('ArrowRight');
  assert.equal(await integer.inputValue(), '-1');
  assert.deepEqual(errors, []);
  console.log('PASS: keyboard arrows/Home, run boundary, semantic events, equivalent-fraction practice, reduced-motion mode, assessment unmount and fresh remount for all three activities, plus equal-side operations and undo.');
} finally {
  await browser?.close();
  await server?.close();
  await rm(directory, { recursive: true, force: true });
}
