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
const rational = load('./linearExplorer.ts');
const math = load('./equationBalance.ts', { './linearExplorer': rational });
const events = load('./interactions.ts');
const registry = load('./rendererRegistry.ts');
const visual = load('../components/ProblemVisual.tsx', { '../mve/rendererRegistry': registry });
const imports = { './equationBalance': math, '../components/ProblemVisual': visual };
const { InteractiveEquationBalance: Component } = load('./InteractiveEquationBalance.tsx', imports);

test('all bounded equations and permitted operations preserve exact solution and semantic validity', () => {
  let transitions = 0;
  for (let lx = 1; lx <= 3; lx++) for (let rx = 0; rx < lx; rx++)
    for (let lu = 0; lu <= 12; lu++) for (let ru = lu; ru <= 12; ru++) {
      const original = { left: { x_count: lx, units: lu }, right: { x_count: rx, units: ru } };
      const snapshot = JSON.stringify(original);
      for (const operation of math.BALANCE_OPERATIONS) {
        const next = math.applyBalanceOperation(original, operation);
        assert.equal(events.isMathInteractionEvent({ schema_version: 1, type: 'BALANCE_OPERATION_APPLIED', operation,
          left_x: lx, left_units: lu, right_x: rx, right_units: ru }), next !== null);
        if (next) {
          transitions++;
          assert.deepEqual(math.balanceSolution(next), math.balanceSolution(original));
          const solution = math.balanceSolution(next);
          assert.equal(next.left.x_count * solution.numerator + next.left.units * solution.denominator,
            next.right.x_count * solution.numerator + next.right.units * solution.denominator);
        }
        assert.equal(JSON.stringify(original), snapshot);
      }
    }
  assert.ok(transitions > 1000);
});
test('two-sided variables, unit removal, exact division and undoable immutable state', () => {
  let eq = math.BALANCE_EXAMPLES[1];
  eq = math.applyBalanceOperation(eq, 'remove_x');
  assert.equal(math.balanceExpression(eq), '2x + 2 = 8');
  eq = math.applyBalanceOperation(eq, 'remove_unit');
  eq = math.applyBalanceOperation(eq, 'remove_unit');
  eq = math.applyBalanceOperation(eq, 'divide_two');
  assert.equal(math.balanceExpression(eq), 'x = 3');
  assert.equal(math.isIsolated(eq), true);
  assert.equal(math.applyBalanceOperation(eq, 'divide_two'), null);
  assert.equal(math.applyBalanceOperation(eq, 'remove_x'), null);
  assert.equal(math.applyBalanceOperation(eq, 'remove_unit'), null);
});
test('invalid state, impossible actions and private fields fail closed; practice accepts exact fractions', () => {
  for (const value of [null, {}, { left: null, right: {} }, { left: { x_count: 0, units: 0 }, right: { x_count: 0, units: 1 } }]) {
    assert.equal(math.isBalanceEquation(value), false);
    assert.equal(math.applyBalanceOperation(value, 'add_unit'), null);
  }
  assert.equal(math.applyBalanceOperation(math.BALANCE_EXAMPLES[0], 'multiply_zero'), null);
  assert.throws(() => math.balanceSolution({}));
  const event = { schema_version: 1, type: 'BALANCE_OPERATION_APPLIED', operation: 'remove_unit', left_x: 2, left_units: 4, right_x: 0, right_units: 10 };
  for (const change of [{ left_units: NaN }, { left_x: 4 }, { operation: 'divide_zero' }, { email: 'test@example.test' }]) assert.equal(events.isMathInteractionEvent({ ...event, ...change }), false);
  for (const [i, answer] of ['4', '2', '5/2'].entries()) assert.equal(math.checkBalanceAnswer(i, answer).correct, true);
  assert.equal(math.checkBalanceAnswer(2, '10/4').correct, true);
  for (const answer of ['', '5/0', '2.5', '2e0', '-1', '3']) assert.equal(math.checkBalanceAnswer(2, answer).correct, false);
  assert.throws(() => math.checkBalanceAnswer(-1, '4'));
});
test('real SVG, accessible actions, disabled undo, history and assessment isolation', () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false }));
  for (const term of ['<svg', 'aria-live="polite"', 'Balance step history', 'disabled=""', 'focus-visible:outline', 'Observe', 'Manipulate', 'Explain', 'Practice']) assert.ok(html.includes(term), term);
  for (const mode of [true, undefined, null]) assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: mode })), '');
  assert.equal(math.showBalanceExploration('GUIDED_PRACTICE', 'Two-Step and Multi-Step Equations'), true);
  for (const mode of ['INDEPENDENT_PRACTICE', 'ASSESSMENT', 'MASTERY_CHECK', '']) assert.equal(math.showBalanceExploration(mode, 'Two-Step and Multi-Step Equations'), false);
});
test('actual handlers preserve equality, undo/reset, emit semantic actions, and check practice', () => {
  let state = [], cursor = 0;
  const emitted = [];
  const hooked = load('./InteractiveEquationBalance.tsx', { ...imports, react: {
    useId: () => 'balance',
    useState: initial => { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
  } });
  function render() { cursor = 0; const wrapper = hooked.InteractiveEquationBalance({ independentAssessment: false, onMathEvent: e => emitted.push(e) }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== 'object' ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  const click = name => nodes(render()).find(n => n.type === 'button' && n.props.children === name).props.onClick();
  click('Subtract 1 from both sides');
  assert.equal(nodes(render()).find(n => n.props.spec).props.spec.left.units, 3);
  assert.equal(events.isMathInteractionEvent(emitted[0]), true);
  click('Undo balance step');
  assert.equal(nodes(render()).find(n => n.props.spec).props.spec.left.units, 4);
  for (let i = 0; i < 4; i++) click('Subtract 1 from both sides');
  click('Divide both sides by 2');
  assert.equal(nodes(render()).find(n => n.props.spec).props.spec.right.units, 3);
  click('Reset balance');
  assert.equal(nodes(render()).find(n => n.props.spec).props.spec.left.units, 4);
  nodes(render()).find(n => n.props.id === 'balance-answer').props.onChange({ target: { value: '4' } });
  click('Check equation');
  assert.match(nodes(render()).find(n => n.props.id === 'balance-feedback').props.children, /^Correct/);
  click('Next equation practice');
  assert.equal(nodes(render()).find(n => n.props.id === 'balance-feedback').props.children, '');
});
