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
    'x not equal to 0',
    'aria-live="polite"',
    'focus-visible:outline',
  ]) assert.ok(html.includes(term), term);
  for (const mode of [true, undefined, null]) {
    assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: mode })), '');
  }
  assert.equal(math.showPolynomialDivisionExploration('GUIDED_PRACTICE', 'Dividing a Polynomial by a Monomial'), true);
  assert.equal(math.showPolynomialDivisionExploration('REMEDIATION', 'Polynomial division'), true);
  assert.equal(math.showPolynomialDivisionExploration('MASTERY_CHECK', 'Polynomial division'), false);
});

test('handlers emit bounded events, diagnose repairs and reset', () => {
  let state = [], cursor = 0; const emitted = [];
  const hooked = load('./InteractivePolynomialDivision.tsx', { ...imports, react: {
    useId: () => 'poly',
    useMemo: value => value(),
    useState: initial => { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
  }});
  function render() { cursor = 0; const wrapper = hooked.InteractivePolynomialDivision({ independentAssessment: false, onMathEvent: e => emitted.push(e) }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== 'object' ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  const buttons = () => nodes(render()).filter(n => n.type === 'button');
  buttons().filter(n => typeof n.props['aria-pressed'] === 'boolean')[0].props.onClick();
  buttons().filter(n => typeof n.props['aria-pressed'] === 'boolean')[1].props.onClick();
  assert.equal(emitted.at(-1).divided_terms, 2);
  assert.equal(events.isMathInteractionEvent(emitted.at(-1)), true);
  nodes(render()).find(n => n.props.name === 'poly-coeff' && n.props.checked === false).props.onChange();
  nodes(render()).find(n => n.props.name === 'poly-exp' && n.props.checked === false).props.onChange();
  nodes(render()).filter(n => n.type === 'input' && n.props.type === 'checkbox')[0].props.onChange();
  nodes(render()).filter(n => n.type === 'input' && n.props.type === 'checkbox')[1].props.onChange();
  buttons().find(n => n.props.children === 'Check polynomial division').props.onClick();
  assert.match(nodes(render()).find(n => n.props.id === 'poly-feedback').props.children, /^Correct/);
  buttons().find(n => n.props.children === 'Reset guided attempt').props.onClick();
  assert.equal(nodes(render()).find(n => n.props.id === 'poly-feedback').props.children, '');
});
