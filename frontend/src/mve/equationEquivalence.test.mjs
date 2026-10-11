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

test("exact response evidence selects remediation only for an observed misconception", () => {
  const equation = math.EQUATION_EQUIVALENCE_EXAMPLES[0];
  const scaled = math.applyEquationOperation(equation, { kind: "scale", amount: r(2, 1) });
  assert.equal(math.diagnoseEquationAttempt(equation, scaled), null);

  const oneSided = math.makeOneSidedCounterexample(equation, { kind: "add_constant", amount: r(1, 1) });
  assert.equal(math.diagnoseEquationAttempt(equation, oneSided), "EQ.OP.ONE_SIDE");
  assert.equal(math.diagnoseEquationAttempt(equation, scaled, { denominatorIgnored: true }), "EQ.DENOMINATOR_IGNORED");

  const falseEquation = {
    left: { x: r(-2, 1), constant: r(-2, 1) },
    right: { x: r(0, 1), constant: r(16, 1) },
  };
  assert.equal(math.diagnoseEquationAttempt(equation, falseEquation), "EQ.FALSE_EQUIVALENCE");
  assert.equal(math.diagnoseEquationAttempt({}, scaled), "EQ.FALSE_EQUIVALENCE");
});

test("semantic events accept exact bounded both-side operations only", () => {
  const event = { schema_version: 1, type: "EQUATION_TRANSFORMATION_APPLIED", operation: "SCALE_BOTH",
    amount_numerator: -1, amount_denominator: 2, preserved: true };
  assert.equal(events.isMathInteractionEvent(event), true);
  for (const change of [
    { operation: "SCALE_LEFT" }, { amount_numerator: 0 }, { amount_denominator: 0 },
    { amount_denominator: 1.5 }, { preserved: false }, { email: "student@example.test" },
  ]) assert.equal(events.isMathInteractionEvent({ ...event, ...change }), false);
  const diagnosis = { schema_version: 1, type: "EQUATION_ATTEMPT_DIAGNOSED", diagnosis: "EQ.OP.ONE_SIDE", phase: "MANIPULATE" };
  assert.equal(events.isMathInteractionEvent(diagnosis), true);
  for (const change of [{ diagnosis: "EQ.UNKNOWN" }, { phase: "ASSESSMENT" }, { student_id: "child-1" }])
    assert.equal(events.isMathInteractionEvent({ ...diagnosis, ...change }), false);
});

test("guided component is accessible, nonvisual-equivalent, reduced-motion safe, and assessment fail-closed", () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false, exampleIndex: 2 }));
  for (const term of [
    "Observe", "Predict", "Manipulate", "Explain", "aria-live=\"polite\"", "aria-pressed=\"false\"",
    "Equivalent-equation transformation table", "Left before", "Right after", "Try changing only one side",
    "Construct and compare equivalent equations", "Support stage:", "MODELED",
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
  assert.equal(emitted.length, 1);
  assert.deepEqual(emitted[0], { schema_version: 1, type: "EQUATION_ATTEMPT_DIAGNOSED",
    diagnosis: "EQ.OP.ONE_SIDE", phase: "MANIPULATE" });
  assert.match(nodes(render()).find(node => node.props?.role === "status").props.children, /No change made/);
  click("Add x to both sides");
  assert.equal(events.isMathInteractionEvent(emitted[1]), true);
  click("Subtract 2 from both sides");
  click("Multiply both sides by -1/6");
  assert.match(equationText(), /Left side x\. Right side −3/);
  assert.equal(emitted.length, 4);
  click("The same valid operation was applied to both complete sides");
  assert.ok(nodes(render()).some(node => node.type === "button" && node.props.children === "Multiply both sides by 3/2"));
  click("Multiply both sides by 2/3");
  assert.deepEqual(emitted.at(-1), { schema_version: 1, type: "EQUATION_ATTEMPT_DIAGNOSED",
    diagnosis: "EQ.DENOMINATOR_IGNORED", phase: "FRESH_EXIT" });
  assert.doesNotMatch(nodes(render()).find(node => node.props?.role === "status" && /coefficient is a fraction/i.test(String(node.props.children))).props.children, /−6|answer/i);
  click("Reset equation");
  assert.equal(equationText(), initial);
  nodes(render()).find(node => node.props?.["aria-label"] === "Choose scale 3").props.onClick();
  click("Construct equivalent equation");
  assert.ok(nodes(render()).some(node => /Constructed equation:/.test(String(node.props?.children))));
  assert.deepEqual(emitted.at(-1), { schema_version: 1, type: "EQUATION_TRANSFORMATION_APPLIED",
    operation: "SCALE_BOTH", amount_numerator: 3, amount_denominator: 1, preserved: true });
});
