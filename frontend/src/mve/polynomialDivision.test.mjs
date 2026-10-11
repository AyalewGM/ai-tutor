import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
function load(path, imports = {}) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  const js = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021,
    jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true,
  } }).outputText;
  const module = { exports: {} };
  new Function("require", "module", "exports", js)(name => imports[name] ?? require(name), module, module.exports);
  return module.exports;
}

const math = load('./polynomialDivision.ts');
const events = load('./interactions.ts');
const imports = { './polynomialDivision': math };
const { InteractivePolynomialDivision: Component } = load('./InteractivePolynomialDivision.tsx', imports);

test('exact term division, reconstruction, rational reduction and negative exponents', () => {
  const quotient = math.quotientFor(math.POLYNOMIAL_DIVISION_EXAMPLE);
  assert.equal(math.formatTerm(quotient[0]), '3x^2y');
  assert.equal(math.formatTerm(quotient[1]), '-2x');
  for (const record of math.reconstructionFor(math.POLYNOMIAL_DIVISION_EXAMPLE)) {
    assert.deepEqual(math.multiplyTerms(record.quotient_term, record.divisor_term), record.product_term);
  }
  assert.deepEqual(math.divideTerm(
    { coefficient: math.rational(6), x_exponent: 1, y_exponent: 0 },
    { coefficient: math.rational(4), x_exponent: 0, y_exponent: 0 },
  ).coefficient, { numerator: 3, denominator: 2 });
  assert.equal(math.formatTerm(math.quotientFor(math.POLYNOMIAL_DIVISION_FRESH_EXIT)[0]), '3x^-1');
  assert.throws(() => math.divideTerm(
    { coefficient: math.rational(1), x_exponent: 0, y_exponent: 0 },
    { coefficient: math.rational(0), x_exponent: 0, y_exponent: 0 },
  ));
});

test('diagnosis follows accepted evidence contract dimensions', () => {
  const response = {
    divided_term_indexes: [0, 1],
    coefficient_reason: math.CORRECT_COEFFICIENT_REASON,
    exponent_reason: math.CORRECT_EXPONENT_REASON,
    domain_restrictions: ['x', 'y'],
  };
  assert.equal(math.diagnosePolynomialDivision(response), 'NO_REMEDIATION');
  assert.equal(math.polynomialPracticeFeedback(response).correct, true);
  assert.equal(math.diagnosePolynomialDivision({ ...response, divided_term_indexes: [0] }), 'POLY.DIV.ONE_TERM_ONLY');
  assert.equal(math.diagnosePolynomialDivision({ ...response, coefficient_reason: 'DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT' }), 'POLY.DIV.COEFFICIENT_RECIPROCAL');
  assert.equal(math.diagnosePolynomialDivision({ ...response, exponent_reason: 'DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT' }), 'POLY.DIV.ADD_EXPONENTS');
  assert.equal(math.diagnosePolynomialDivision({ ...response, domain_restrictions: ['x'] }), 'POLY.DIV.DOMAIN_OMITTED');
  assert.equal(math.diagnosePolynomialDivision({ ...response, divided_term_indexes: [-1, 99] }), 'POLY.DIV.ONE_TERM_ONLY');
  assert.equal(math.diagnosePolynomialDivision({ ...response, divided_term_indexes: [0, 0] }), 'POLY.DIV.ONE_TERM_ONLY');
  assert.equal(math.diagnosePolynomialDivision({ ...response, domain_restrictions: ['y', 'x'] }), 'NO_REMEDIATION');
  assert.equal(math.diagnosePolynomialDivision({ ...response, domain_restrictions: ['x', 'x'] }), 'POLY.DIV.DOMAIN_OMITTED');
});

test('full learner attempt requires produced quotient, reconstruction, explanation and fresh transfer', () => {
  const attempt = {
    divided_term_indexes: [0, 1],
    prediction: 'Coefficients divide, exponents subtract, and x and y stay nonzero.',
    prediction_evidence: {
      coefficient: 'PREDICT_DIVIDE_EACH_DIVIDEND_COEFFICIENT',
      exponent: 'PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS',
      domain: 'PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO',
    },
    quotient_terms: [
      { coefficient: '3', x_exponent: '2', y_exponent: '1' },
      { coefficient: '-2', x_exponent: '1', y_exponent: '0' },
    ],
    coefficient_reason: math.CORRECT_COEFFICIENT_REASON,
    exponent_reason: math.CORRECT_EXPONENT_REASON,
    domain_restrictions: ['x', 'y'],
    reconstruction: [
      { product_coefficient: '6', product_x_exponent: '3', product_y_exponent: '2' },
      { product_coefficient: '-4', product_x_exponent: '2', product_y_exponent: '1' },
    ],
    explanation: 'Multiply to reconstruct the dividend, subtract exponents, and keep original nonzero restrictions.',
    explanation_evidence: {
      reconstruction: 'EXPLAIN_QUOTIENT_TIMES_DIVISOR_REBUILDS_DIVIDEND',
      exponent: 'PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS',
      domain: 'PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO',
    },
    transfer_terms: [
      { coefficient: '3', x_exponent: '-1', y_exponent: '0' },
      { coefficient: '5', x_exponent: '-2', y_exponent: '1' },
    ],
  };
  assert.equal(math.evaluateLearnerPolynomialAttempt(attempt).correct, true);
  assert.equal(math.evaluateLearnerPolynomialAttempt({
    ...attempt,
    quotient_terms: [...attempt.quotient_terms].reverse(),
    reconstruction: [...attempt.reconstruction].reverse(),
    transfer_terms: [...attempt.transfer_terms].reverse(),
    domain_restrictions: ['y', 'x'],
  }).correct, true);
  assert.equal(math.evaluateLearnerPolynomialAttempt({
    ...attempt,
    prediction: 'Coefficients divide, exponents subtract, and x and y stay nonzero.',
    prediction_evidence: { ...attempt.prediction_evidence, exponent: 'PREDICT_ADD_LIKE_BASE_EXPONENTS' },
  }).diagnosis, 'POLY.DIV.PREDICTION_REASONING');
  assert.equal(math.evaluateLearnerPolynomialAttempt({ ...attempt, quotient_terms: [{ coefficient: '3', x_exponent: '2', y_exponent: '1' }] }).diagnosis, 'POLY.DIV.QUOTIENT_RECORD');
  assert.equal(math.evaluateLearnerPolynomialAttempt({ ...attempt, reconstruction: [{ product_coefficient: '6', product_x_exponent: '3', product_y_exponent: '2' }] }).diagnosis, 'POLY.DIV.RECONSTRUCTION_RECORD');
  assert.equal(math.evaluateLearnerPolynomialAttempt({
    ...attempt,
    explanation: 'Multiply to reconstruct the dividend, subtract exponents, and keep original nonzero restrictions.',
    explanation_evidence: { ...attempt.explanation_evidence, reconstruction: 'EXPLAIN_QUOTIENT_PLUS_DIVISOR_REBUILDS_DIVIDEND' },
  }).diagnosis, 'POLY.DIV.EXPLANATION_REASONING');
  assert.equal(math.evaluateLearnerPolynomialAttempt({ ...attempt, transfer_terms: [
    { coefficient: '3', x_exponent: '1', y_exponent: '0' },
    { coefficient: '5', x_exponent: '2', y_exponent: '1' },
  ] }).diagnosis, 'POLY.DIV.FRESH_EXIT_UNVERIFIED');
  assert.equal(math.evaluateLearnerPolynomialAttempt({ ...attempt, quotient_terms: [
    attempt.quotient_terms[0],
    attempt.quotient_terms[0],
  ] }).diagnosis, 'POLY.DIV.QUOTIENT_RECORD');
  assert.equal(math.evaluateLearnerPolynomialAttempt({ ...attempt, reconstruction: [
    attempt.reconstruction[0],
    attempt.reconstruction[0],
  ] }).diagnosis, 'POLY.DIV.RECONSTRUCTION_RECORD');
  assert.equal(math.evaluateLearnerPolynomialAttempt({ ...attempt, quotient_terms: [
    { coefficient: '3', x_exponent: '9007199254740992', y_exponent: '1' },
    attempt.quotient_terms[1],
  ] }).diagnosis, 'POLY.DIV.QUOTIENT_RECORD');
});

test('socratic repair requires misconception evidence and a different repair exit', () => {
  const repairTerms = [
    { coefficient: '-3', x_exponent: '2', y_exponent: '0' },
    { coefficient: '5', x_exponent: '0', y_exponent: '2' },
  ];
  const weak = math.evaluateSocraticRepair('POLY.DIV.ADD_EXPONENTS', 'REPAIR_MULTIPLY_THEN_ADD', repairTerms);
  assert.equal(weak.correct, false);
  assert.equal(weak.scaffold, 'RESTORE');
  const repaired = math.evaluateSocraticRepair(
    'POLY.DIV.ADD_EXPONENTS',
    'REPAIR_CANCEL_THEN_SUBTRACT',
    repairTerms,
  );
  assert.equal(repaired.correct, true);
  assert.equal(repaired.scaffold, 'FADE');
});

test('semantic event validation rejects PII, extra fields and impossible states', () => {
  const event = {
    schema_version: 1,
    type: 'POLYNOMIAL_DIVISION_MANIPULATED',
    divided_terms: 2,
    coefficient_reason: math.CORRECT_COEFFICIENT_REASON,
    exponent_reason: math.CORRECT_EXPONENT_REASON,
    domain_x: true,
    domain_y: true,
  };
  assert.equal(events.isMathInteractionEvent(event), true);
  assert.equal(events.isMathInteractionEvent({ ...event, student_id: 'child-1' }), false);
  assert.equal(events.isMathInteractionEvent({ ...event, divided_terms: 5 }), false);
  assert.equal(events.isMathInteractionEvent({ ...event, domain_x: 'yes' }), false);
});

test('guided component renders full sequence and fails closed in assessment', () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false }));
  for (const term of [
    'Guided polynomial division exploration',
    'Observe',
    'Manipulate',
    'Explain',
    'Practice',
    'Transfer',
    'Multiplication reconstruction',
    'Prediction before quotient reveal',
    'Prediction evidence',
    'Explanation evidence',
    'Fresh quotient term 1',
    'Scaffold state',
    'x not equal to 0',
    'aria-live="polite"',
    'focus-visible:outline',
  ]) assert.ok(html.includes(term), term);
  assert.equal(html.includes('Quotient card'), false);
  assert.equal(html.includes('3x^2y times 2xy reconstructs 6x^3y^2'), false);
  assert.equal(html.includes('Your repair answer must include'), false);
  for (const mode of [true, undefined, null]) {
    assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: mode })), '');
  }
  assert.equal(
    math.POLYNOMIAL_DIVISION_ROUTE_STATUS,
    'DEFAULT_OFF_PENDING_APPROVED_SERVER_CAPABILITY',
  );
  for (const state of [
    'GUIDED_PRACTICE',
    'REMEDIATION',
    'INDEPENDENT_PRACTICE',
    'MASTERY_CHECK',
    'COMPLETE',
  ]) {
    for (const identity of [
      undefined,
      null,
      '',
      'Dividing a Polynomial by a Monomial',
      'Polynomial division',
      'Divide a Polynomial by a Polynomial',
      'MATH.POLY.DIVIDE_POLYNOMIAL_BY_MONOMIAL',
      { capability: 'POLYNOMIAL_DIVISION' },
    ]) {
      assert.equal(math.showPolynomialDivisionExploration(state, identity), false);
    }
  }
  const workspaceSource = readFileSync(
    new URL('../pages/Workspace.tsx', import.meta.url),
    'utf8',
  );
  assert.ok(workspaceSource.includes(
    'showPolynomialDivisionExploration(workspace.state, undefined)',
  ));
  assert.equal(
    workspaceSource.includes(
      'showPolynomialDivisionExploration(workspace.state, workspace.focus.skill_name)',
    ),
    false,
  );
  assert.ok(workspaceSource.includes('InteractiveFractionBars'));
  assert.ok(workspaceSource.includes('fractionComparisonTarget'));
});

test('handlers emit bounded events, diagnose repairs and reset', () => {
  let state = [], cursor = 0; const emitted = [];
  const hooked = load('./InteractivePolynomialDivision.tsx', { ...imports, react: {
    useId: () => 'poly',
    useMemo: value => value(),
    useState: initial => { const i = cursor++; if (!(i in state)) state[i] = typeof initial === 'function' ? initial() : initial; return [state[i], value => { state[i] = typeof value === 'function' ? value(state[i]) : value; }]; },
  }});
  function render() { cursor = 0; const wrapper = hooked.InteractivePolynomialDivision({ independentAssessment: false, onMathEvent: e => emitted.push(e) }); return wrapper.type(wrapper.props); }
  function nodes(node) {
    if (!node || typeof node !== 'object') return [];
    const expanded = typeof node.type === 'function' ? node.type(node.props) : null;
    return [node, ...nodes(expanded), ...React.Children.toArray(node.props?.children).flatMap(nodes)];
  }
  const buttons = () => nodes(render()).filter(n => n.type === 'button');
  buttons().filter(n => typeof n.props['aria-pressed'] === 'boolean')[0].props.onClick();
  buttons().filter(n => typeof n.props['aria-pressed'] === 'boolean')[1].props.onClick();
  assert.equal(emitted.at(-1).divided_terms, 2);
  assert.equal(events.isMathInteractionEvent(emitted.at(-1)), true);
  nodes(render()).find(n => n.props['aria-label'] === 'Prediction before quotient reveal').props.onChange({ target: { value: 'Coefficients divide, exponents subtract, and restrictions keep variables nonzero.' } });
  nodes(render()).find(n => n.props['aria-label'] === 'Prediction coefficient evidence').props.onChange({ target: { value: 'PREDICT_DIVIDE_EACH_DIVIDEND_COEFFICIENT' } });
  nodes(render()).find(n => n.props['aria-label'] === 'Prediction exponent evidence').props.onChange({ target: { value: 'PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS' } });
  nodes(render()).find(n => n.props['aria-label'] === 'Prediction domain evidence').props.onChange({ target: { value: 'PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO' } });
  for (const [label, value] of [
    ['Quotient term 1 coefficient', '3'],
    ['Quotient term 1 x exponent', '2'],
    ['Quotient term 1 y exponent', '1'],
    ['Quotient term 2 coefficient', '-2'],
    ['Quotient term 2 x exponent', '1'],
    ['Quotient term 2 y exponent', '0'],
    ['Fresh quotient term 1 coefficient', '3'],
    ['Fresh quotient term 1 x exponent', '-1'],
    ['Fresh quotient term 1 y exponent', '0'],
    ['Fresh quotient term 2 coefficient', '5'],
    ['Fresh quotient term 2 x exponent', '-2'],
    ['Fresh quotient term 2 y exponent', '1'],
  ]) {
    const input = nodes(render()).find(n => n.props['aria-label'] === label);
    assert.ok(input, label);
    input.props.onChange({ target: { value } });
  }
  nodes(render()).find(n => n.props.name === 'poly-coeff' && n.props.checked === false).props.onChange();
  nodes(render()).find(n => n.props.name === 'poly-exp' && n.props.checked === false).props.onChange();
  nodes(render()).filter(n => n.type === 'input' && n.props.type === 'checkbox')[0].props.onChange();
  nodes(render()).filter(n => n.type === 'input' && n.props.type === 'checkbox')[1].props.onChange();
  for (const [label, value] of [
    ['Reconstruction product 1 coefficient', '6'],
    ['Reconstruction product 1 x exponent', '3'],
    ['Reconstruction product 1 y exponent', '2'],
    ['Reconstruction product 2 coefficient', '-4'],
    ['Reconstruction product 2 x exponent', '2'],
    ['Reconstruction product 2 y exponent', '1'],
  ]) nodes(render()).find(n => n.props['aria-label'] === label).props.onChange({ target: { value } });
  nodes(render()).find(n => n.props['aria-label'] === 'Explanation of polynomial division reasoning').props.onChange({ target: { value: 'Multiply to reconstruct the dividend, subtract exponents, and keep original nonzero restrictions.' } });
  nodes(render()).find(n => n.props['aria-label'] === 'Explanation reconstruction evidence').props.onChange({ target: { value: 'EXPLAIN_QUOTIENT_TIMES_DIVISOR_REBUILDS_DIVIDEND' } });
  nodes(render()).find(n => n.props['aria-label'] === 'Explanation exponent evidence').props.onChange({ target: { value: 'PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS' } });
  nodes(render()).find(n => n.props['aria-label'] === 'Explanation domain evidence').props.onChange({ target: { value: 'PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO' } });
  buttons().find(n => n.props.children === 'Check polynomial division').props.onClick();
  assert.match(nodes(render()).find(n => n.props.id === 'poly-feedback').props.children, /^Correct/);
  buttons().find(n => n.props.children === 'Reset guided attempt').props.onClick();
  assert.match(nodes(render()).find(n => n.props.id === 'poly-feedback').props.children, /^Enter a prediction/);
});

test('repair success removes active support rather than only changing status text', () => {
  let state = [], cursor = 0;
  const hooked = load('./InteractivePolynomialDivision.tsx', { ...imports, react: {
    useId: () => 'poly',
    useMemo: value => value(),
    useState: initial => { const i = cursor++; if (!(i in state)) state[i] = typeof initial === 'function' ? initial() : initial; return [state[i], value => { state[i] = typeof value === 'function' ? value(state[i]) : value; }]; },
  }});
  function render() { cursor = 0; const wrapper = hooked.InteractivePolynomialDivision({ independentAssessment: false }); return wrapper.type(wrapper.props); }
  function nodes(node) {
    if (!node || typeof node !== 'object') return [];
    const expanded = typeof node.type === 'function' ? node.type(node.props) : null;
    return [node, ...nodes(expanded), ...React.Children.toArray(node.props?.children).flatMap(nodes)];
  }
  const buttons = () => nodes(render()).filter(n => n.type === 'button');
  buttons().find(n => n.props.children === 'Check polynomial division').props.onClick();
  assert.ok(nodes(render()).some(n => n.props['aria-label'] === 'Socratic polynomial division repair'));
  nodes(render()).find(n => n.props.name === 'poly-repair' && n.props.checked === false).props.onChange();
  for (const [label, value] of [
    ['Repair quotient term 1 coefficient', '-3'],
    ['Repair quotient term 1 x exponent', '2'],
    ['Repair quotient term 1 y exponent', '0'],
    ['Repair quotient term 2 coefficient', '5'],
    ['Repair quotient term 2 x exponent', '0'],
    ['Repair quotient term 2 y exponent', '2'],
  ]) nodes(render()).find(n => n.props['aria-label'] === label).props.onChange({ target: { value } });
  buttons().find(n => n.props.children === 'Check repair exit').props.onClick();
  const rendered = nodes(render());
  assert.equal(rendered.some(n => n.props['aria-label'] === 'Socratic polynomial division repair'), false);
  assert.ok(rendered.some(n => React.Children.toArray(n.props?.children).join('').includes('Support faded')));
  assert.equal(rendered.some(n => React.Children.toArray(n.props?.children).join('').includes('Use exact integers or reduced rational coefficients.')), false);
});
