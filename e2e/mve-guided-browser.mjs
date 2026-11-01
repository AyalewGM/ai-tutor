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
import React, { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { InteractiveLinearExplorer } from '/src/mve/InteractiveLinearExplorer';
import { InteractiveIntegerNumberLine } from '/src/mve/InteractiveIntegerNumberLine';
import { InteractiveEquationBalance } from '/src/mve/InteractiveEquationBalance';
import { InteractiveDotPlotExplorer } from '/src/mve/InteractiveDotPlotExplorer';
import { InteractiveProbabilityTree } from '/src/mve/InteractiveProbabilityTree';
import { InteractivePolynomialDivision } from '/src/mve/InteractivePolynomialDivision';
import ExactRationalEntry from '/src/components/ExactRationalEntry';
import '/src/styles.css';
function RationalEntryHarness() {
 const [value, setValue] = useState('');
 const [answerKind, setAnswerKind] = useState<'RATIONAL' | 'VARIABLE_VALUE'>('RATIONAL');
 const [disabled, setDisabled] = useState(false);
 const answerRef = useRef<HTMLInputElement>(null);
 function insertToken(token: string) {
  const input = answerRef.current;
  const start = input?.selectionStart ?? value.length;
  const end = input?.selectionEnd ?? start;
  const from = token === '\b' && start === end ? Math.max(0, start - 1) : start;
  const next = value.slice(0, from) + (token === '\b' ? '' : token) + value.slice(end);
  const cursor = from + (token === '\b' ? 0 : token.length);
  setValue(next);
  requestAnimationFrame(() => {
   input?.focus();
   input?.setSelectionRange(cursor, cursor);
  });
 }
 return <section aria-label="Exact rational entry browser checks">
  <button type="button" onClick={() => { setAnswerKind('VARIABLE_VALUE'); setValue(''); }}>Use variable-value input</button>
  <button type="button" onClick={() => { setAnswerKind('RATIONAL'); setValue(''); }}>Use rational input</button>
  <button type="button" onClick={() => setDisabled(value => !value)}>Toggle entry disabled</button>
  <ExactRationalEntry ref={answerRef} answerKind={answerKind} value={value}
   onValueChange={setValue} onKey={insertToken} disabled={disabled} />
  <output aria-label="Exact entry value">{value}</output>
 </section>;
}
function Harness() {
 const [assessment, setAssessment] = useState(false);
 const [event, setEvent] = useState('');
 return <><button onClick={() => setAssessment(!assessment)}>Toggle assessment</button>
 <InteractiveLinearExplorer independentAssessment={assessment} onMathEvent={e => setEvent(JSON.stringify(e))} />
 <InteractiveIntegerNumberLine independentAssessment={assessment} />
 <InteractiveEquationBalance independentAssessment={assessment} />
 <InteractiveDotPlotExplorer independentAssessment={assessment} />
 <InteractiveProbabilityTree independentAssessment={assessment} onMathEvent={e => setEvent(JSON.stringify(e))} />
 <InteractivePolynomialDivision independentAssessment={assessment} onMathEvent={e => setEvent(JSON.stringify(e))} />
 <output aria-label="Last semantic event">{event}</output>
 <RationalEntryHarness /></>;
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
  const data = page.getByRole('region', { name: 'Guided dot plot exploration' });
  await data.getByLabel('Observation value:').focus();
  await page.keyboard.press('End');
  assert.ok((await data.getByRole('status').first().textContent()).includes('mean 24/5; median 3; range 10'));
  await data.getByRole('button', { name: 'Add another observation at this value' }).click();
  assert.equal(await data.getByRole('button', { name: 'Add another observation at this value' }).isDisabled(), true);
  const probability = page.getByRole('region', { name: 'Guided probability tree exploration' });
  // Prediction must be recorded before any manipulation or tree reveal.
  assert.equal(await probability.getByLabel('First event total outcomes:').isDisabled(), true);
  assert.equal(await probability.getByRole('img', { name: /Independent probability tree/ }).count(), 0);
  await probability.getByRole('combobox').first().selectOption('increase');
  await probability.getByRole('button', { name: 'Lock prediction' }).click();
  assert.equal(await probability.getByLabel('First event total outcomes:').isEnabled(), true);
  await probability.getByLabel('First event favorable outcomes:').focus();
  await page.keyboard.press('ArrowRight');
  assert.equal(await probability.getByLabel('First event total outcomes:').inputValue(), '8');
  assert.equal(await probability.getByLabel('First event favorable outcomes:').inputValue(), '4');
  const probabilityEvent = JSON.parse(await page.getByLabel('Last semantic event').textContent());
  assert.equal(probabilityEvent.first_total, 8);
  assert.equal(probabilityEvent.first_favorable, 4);
  await probability.getByRole('combobox').last().selectOption('add');
  await probability.getByRole('button', { name: 'Check explanation' }).click();
  assert.ok((await probability.getByText(/Adding stage probabilities mixes separate stages/).count()) > 0);
  await probability.getByLabel('Repair probability').fill('1/8');
  await probability.getByLabel('Reasoning choice').selectOption('multiply');
  await probability.getByRole('button', { name: 'Check repair' }).click();
  await probability.getByText(/Scaffold faded/).waitFor();
  assert.equal(await probability.getByRole('region', { name: 'Misconception repair' }).count(), 0);
  assert.ok((await probability.getByText(/Scaffold faded/).count()) > 0);
  assert.equal(await probability.getByRole('region', { name: 'Probability model transfer' }).count(), 1);
  await probability.getByLabel('Probability practice answer').fill('1/5');
  await probability.getByRole('button', { name: 'Check probability' }).click();
  const probabilityPracticeFeedback = probability.locator('[id$="-feedback"]');
  await probabilityPracticeFeedback.getByText(/^Correct/).waitFor();
  assert.ok((await probabilityPracticeFeedback.textContent()).startsWith('Correct'));
  const polynomial = page.getByRole('region', { name: 'Guided polynomial division exploration' });
  await polynomial.getByRole('button', { name: /Term 1/ }).click();
  await polynomial.getByRole('button', { name: /Term 2/ }).click();
  assert.equal(JSON.parse(await page.getByLabel('Last semantic event').textContent()).divided_terms, 2);
  await polynomial.getByLabel('Prediction before quotient reveal').fill('Coefficients divide, exponents subtract, and original restrictions stay visible.');
  await polynomial.getByLabel('Prediction coefficient evidence').selectOption('PREDICT_DIVIDE_EACH_DIVIDEND_COEFFICIENT');
  await polynomial.getByLabel('Prediction exponent evidence').selectOption('PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS');
  await polynomial.getByLabel('Prediction domain evidence').selectOption('PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO');
  for (const [label, value] of [
    ['Quotient term 1 coefficient', '3'],
    ['Quotient term 1 x exponent', '2'],
    ['Quotient term 1 y exponent', '1'],
    ['Quotient term 2 coefficient', '-2'],
    ['Quotient term 2 x exponent', '1'],
    ['Quotient term 2 y exponent', '0'],
    ['Reconstruction product 1 coefficient', '6'],
    ['Reconstruction product 1 x exponent', '3'],
    ['Reconstruction product 1 y exponent', '2'],
    ['Reconstruction product 2 coefficient', '-4'],
    ['Reconstruction product 2 x exponent', '2'],
    ['Reconstruction product 2 y exponent', '1'],
    ['Fresh quotient term 1 coefficient', '3'],
    ['Fresh quotient term 1 x exponent', '-1'],
    ['Fresh quotient term 1 y exponent', '0'],
    ['Fresh quotient term 2 coefficient', '5'],
    ['Fresh quotient term 2 x exponent', '-2'],
    ['Fresh quotient term 2 y exponent', '1'],
  ]) await polynomial.getByLabel(label, { exact: true }).fill(value);
  await polynomial.getByLabel('Dividend coefficient divided by divisor coefficient').check();
  await polynomial.getByLabel('Dividend exponent minus divisor exponent').check();
  await polynomial.getByLabel('x not equal to 0').check();
  await polynomial.getByLabel('y not equal to 0').check();
  await polynomial.getByLabel('Explanation of polynomial division reasoning').fill('Multiply to reconstruct the dividend, subtract exponents, and keep original nonzero restrictions.');
  await polynomial.getByLabel('Explanation reconstruction evidence').selectOption('EXPLAIN_QUOTIENT_TIMES_DIVISOR_REBUILDS_DIVIDEND');
  await polynomial.getByLabel('Explanation exponent evidence').selectOption('PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS');
  await polynomial.getByLabel('Explanation domain evidence').selectOption('PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO');
  await polynomial.getByRole('button', { name: 'Check polynomial division' }).click();
  assert.ok((await polynomial.getByRole('status').last().textContent()).startsWith('Correct'));
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
  assert.equal(await data.count(), 0);
  assert.equal(await polynomial.count(), 0);
  assert.equal(await probability.count(), 0);
  assert.equal(await page.getByRole('region', { name: 'Guided integer number line exploration' }).count(), 0);
  await page.getByRole('button', { name: 'Toggle assessment' }).click();
  assert.equal(await rise.inputValue(), '2');
  assert.equal(await data.getByLabel('Observation value:').inputValue(), '5');
  assert.equal(await probability.getByLabel('First event total outcomes:').inputValue(), '8');
  assert.equal(await probability.getByLabel('First event total outcomes:').isDisabled(), true);
  assert.ok((await balance.getByRole('status').first().textContent()).startsWith('2x + 4 = 10.'));
  assert.equal(await page.getByLabel('Slope as an integer or fraction').inputValue(), '');
  const integer = page.getByLabel('Starting integer:');
  await integer.focus(); await page.keyboard.press('ArrowRight');
  assert.equal(await integer.inputValue(), '-1');
  // Exact-rational input: real keyboard, caret insertion, focus restoration,
  // touch keypad restrictions, variable identity and server-owned disable.
  const exact = page.getByRole('region', { name: 'Exact rational entry browser checks' });
  const rationalInput = exact.getByRole('textbox', { name: 'Exact rational number' });
  const exactKeys = exact.getByRole('group', { name: 'Exact rational keypad' });
  await rationalInput.fill('1/2');
  await rationalInput.focus();
  await page.keyboard.press('End');
  await exactKeys.getByRole('button', { name: '3', exact: true }).click();
  assert.equal(await rationalInput.inputValue(), '1/23');
  await page.waitForFunction(() => document.activeElement?.getAttribute('aria-label') === 'Exact rational number');
  await exactKeys.getByRole('button', { name: 'backspace' }).click();
  assert.equal(await rationalInput.inputValue(), '1/2');
  await exact.getByRole('button', { name: 'Use variable-value input' }).click();
  const variableInput = exact.getByRole('textbox', { name: 'Exact variable value' });
  await variableInput.fill('n=-5/6');
  assert.equal(await variableInput.inputValue(), 'n=-5/6');
  for (const notAllowed of ['x', 'y', '.', '^', '+', '×', '÷', '=']) {
    assert.equal(await exactKeys.getByRole('button', { name: notAllowed, exact: true }).count(), 0);
  }
  assert.ok((await exact.getByText(/Use your keyboard for the variable and equals sign/).count()) > 0);
  await exact.getByRole('button', { name: 'Toggle entry disabled' }).click();
  assert.equal(await variableInput.isDisabled(), true);
  assert.equal(await exactKeys.getByRole('button', { name: '7', exact: true }).isDisabled(), true);
  assert.deepEqual(errors, []);
  console.log('PASS: exact-rational keyboard/caret/focus/disabled contract, keyboard arrows/Home, run boundary, semantic events, equivalent-fraction practice, grouped-term polynomial division, reduced-motion mode, assessment unmount and fresh remount for all six activities, plus equal-side operations and undo.');
} finally {
  await browser?.close();
  await server?.close();
  await rm(directory, { recursive: true, force: true });
}
