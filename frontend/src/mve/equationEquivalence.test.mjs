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

const rationalModule = load("./linearExplorer.ts");
const math = load("./equationEquivalence.ts", { "./linearExplorer": rationalModule });
const events = load("./interactions.ts");
const componentImports = { "./equationEquivalence": math };
const { InteractiveEquationEquivalence: Component } = load("./InteractiveEquationEquivalence.tsx", componentImports);
const r = rationalModule.rational;

test("examples solve exactly, including negative, fractional, and two-sided equations", () => {
  assert.deepEqual(math.EQUATION_EQUIVALENCE_EXAMPLES.map(math.equationSolution), [r(-17, 2), r(-5, 1), r(-3, 1)]);
  assert.deepEqual(math.EQUATION_EQUIVALENCE_EXAMPLES.map(math.formatAffineEquation), [
    "−2x − 3 = 14", "1/5x + 8 = 7", "−7x + 2 = −x + 20",
  ]);
  for (const equation of math.EQUATION_EQUIVALENCE_EXAMPLES) assert.equal(math.equationHolds(equation, math.equationSolution(equation)), true);
});

test("every deterministic move preserves the exact solution and isolates within three moves", () => {
  for (const starting of math.EQUATION_EQUIVALENCE_EXAMPLES) {
    const snapshot = JSON.stringify(starting);
    const solution = math.equationSolution(starting);
    let equation = starting;
    let steps = 0;
    while (!math.isEquationIsolated(equation) && steps < 4) {
      const [operation] = math.nextEquationMoves(equation);
      assert.ok(operation);
      const next = math.applyEquationOperation(equation, operation);
      assert.ok(next);
      assert.deepEqual(math.equationSolution(next), solution);
      assert.equal(math.equationHolds(next, solution), true);
      equation = next;
      steps++;
    }
    assert.equal(math.isEquationIsolated(equation), true);
    assert.ok(steps <= 3);
    assert.equal(JSON.stringify(starting), snapshot);
  }
});

test("bounded rational transformations fail closed and scale equivalence rejects partial changes", () => {
  const equation = math.EQUATION_EQUIVALENCE_EXAMPLES[0];
  for (const operation of [
    { kind: "scale", amount: r(0, 1) },
    { kind: "divide", amount: r(2, 1) },
    { kind: "add_constant", amount: { numerator: 2, denominator: 2 } },
    { kind: "scale", amount: { numerator: 10001, denominator: 1 } },
  ]) assert.equal(math.applyEquationOperation(equation, operation), null);
  for (const value of [null, {}, { left: {}, right: {} }, { left: equation.left, right: equation.left }]) {
    assert.equal(math.isAffineEquation(value), false);
    assert.equal(math.applyEquationOperation(value, { kind: "scale", amount: r(2, 1) }), null);
  }
  const doubled = math.applyEquationOperation(equation, { kind: "scale", amount: r(2, 1) });
  assert.equal(math.areScaleEquivalent(equation, doubled), true);
  assert.equal(math.areScaleEquivalent(equation, { ...doubled, right: equation.right }), false);
});

test("semantic events accept exact bounded both-side operations only", () => {
  const event = { schema_version: 1, type: "EQUATION_TRANSFORMATION_APPLIED", operation: "SCALE_BOTH",
    amount_numerator: -1, amount_denominator: 2, preserved: true };
  assert.equal(events.isMathInteractionEvent(event), true);
  for (const change of [
    { operation: "SCALE_LEFT" }, { amount_numerator: 0 }, { amount_denominator: 0 },
    { amount_denominator: 1.5 }, { preserved: false }, { email: "student@example.test" },
  ]) assert.equal(events.isMathInteractionEvent({ ...event, ...change }), false);
});

test("guided component is accessible, nonvisual-equivalent, reduced-motion safe, and assessment fail-closed", () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false, exampleIndex: 2 }));
  for (const term of [
    "Observe", "Predict", "Manipulate", "Explain", "aria-live=\"polite\"", "aria-pressed=\"false\"",
    "Equivalent-equation transformation table", "Left before", "Right after", "Try changing only one side",
    "motion-reduce:transition-none", "−7x + 2", "does not count toward mastery",
  ]) assert.ok(html.includes(term), term);
  for (const mode of [true, undefined, null]) assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: mode })), "");
  assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: false, exampleIndex: 99 })), "");
});

test("actual handlers preserve state on rejection, emit validated success, isolate, and reset", () => {
  let state = [], cursor = 0;
  const emitted = [];
  const hooked = load("./InteractiveEquationEquivalence.tsx", { ...componentImports, react: {
    useId: () => "equivalence",
    useState: initial => { const index = cursor++; if (!(index in state)) state[index] = initial;
      return [state[index], value => { state[index] = typeof value === "function" ? value(state[index]) : value; }]; },
  } });
  function render() {
    cursor = 0;
    const wrapper = hooked.InteractiveEquationEquivalence({ independentAssessment: false, exampleIndex: 2, onMathEvent: event => emitted.push(event) });
    return wrapper.type(wrapper.props);
  }
  function nodes(node) { return !node || typeof node !== "object" ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  const equationText = () => nodes(render()).find(node => node.props?.role === "img").props["aria-label"];
  const click = label => nodes(render()).find(node => node.type === "button" && node.props.children === label).props.onClick();
  const initial = equationText();
  click("Try changing only one side");
  assert.equal(equationText(), initial);
  assert.equal(emitted.length, 0);
  assert.match(nodes(render()).find(node => node.props?.role === "status").props.children, /No change made/);
  click("Add x to both sides");
  assert.equal(events.isMathInteractionEvent(emitted[0]), true);
  click("Subtract 2 from both sides");
  click("Multiply both sides by -1/6");
  assert.match(equationText(), /Left side x\. Right side −3/);
  assert.equal(emitted.length, 3);
  click("Reset equation");
  assert.equal(equationText(), initial);
});
