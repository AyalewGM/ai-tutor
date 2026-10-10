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
const math = load("./integerNumberLine.ts");
const events = load("./interactions.ts");
const registry = load("./rendererRegistry.ts");
const visual = load("../components/ProblemVisual.tsx", { "../mve/rendererRegistry": registry });
const imports = { "./integerNumberLine": math, "../components/ProblemVisual": visual };
const { InteractiveIntegerNumberLine: Component } = load("./InteractiveIntegerNumberLine.tsx", imports);

test("all 882 bounded integer models are exact, with consistent direction and events", () => {
  for (let a = -10; a <= 10; a++) for (let b = -10; b <= 10; b++) for (const op of ["add", "subtract"]) {
    const m = math.integerModel(a, b, op);
    assert.equal(m.result, op === "add" ? a + b : a - b);
    assert.equal(m.direction, m.displacement === 0 ? "stay" : m.displacement > 0 ? "right" : "left");
    assert.equal(events.isMathInteractionEvent({ schema_version: 1, type: "INTEGER_DISPLACEMENT_CHANGED",
      start: a, operand: b, operation: op, displacement: m.displacement, result: m.result }), true);
  }
});
test("invalid models and inconsistent or PII-bearing events fail closed", () => {
  for (const n of [NaN, Infinity, 11, -11, 0.5, "2", null]) assert.throws(() => math.integerModel(n, 1, "add"));
  assert.throws(() => math.integerModel(1, 2, "multiply"));
  const event = { schema_version: 1, type: "INTEGER_DISPLACEMENT_CHANGED", start: -2, operand: -3, operation: "subtract", displacement: 3, result: 1 };
  for (const change of [{ result: 7 }, { displacement: -3 }, { email: "student@example.test" }, { operation: "multiply" }]) {
    assert.equal(events.isMathInteractionEvent({ ...event, ...change }), false);
  }
});
test("practice specifications score deterministically and reject malformed input", () => {
  for (const [i, answer] of [2, 3, -3, -4, -4].entries()) {
    assert.equal(math.checkIntegerPractice(i, String(answer)).correct, true);
    assert.equal(math.checkIntegerPractice(i, String(answer + 1)).correct, false);
  }
  for (const input of ["", "1.0", "2e0", "NaN", "100", "21", "-21"]) assert.equal(math.checkIntegerPractice(0, input).correct, false);
  const wrong = math.checkIntegerPractice(1, "2");
  assert.equal(wrong.correct, false);
  assert.equal(wrong.feedback.includes("to 3"), false);
  assert.equal(wrong.feedback.includes("result"), false);
  assert.throws(() => math.checkIntegerPractice(-1, "0"));
});
test("real rendered component has labeled keyboard controls, live feedback and SVG", () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false }));
  for (const label of ["Observe", "Manipulate", "Explain", "Practice", "aria-live=\"polite\"", "focus-visible:outline", "<svg", "type=\"range\""]) assert.ok(html.includes(label), label);
  assert.equal((html.match(/type="range"/g) ?? []).length, 2);
  for (const [, id] of html.matchAll(/<label[^>]*for="([^"]+)"/g)) assert.ok(html.includes(`id="${id}"`));
  assert.ok(html.includes("Subtracting -3 means adding its opposite, 3"));
});
test("assessment and unknown modes render nothing and cannot emit events", () => {
  for (const mode of [true, undefined, null]) assert.equal(renderToStaticMarkup(React.createElement(Component, {
    independentAssessment: mode, onMathEvent: () => assert.fail("assessment event"),
  })), "");
  for (const state of ["ASSESSMENT", "INDEPENDENT_PRACTICE", "MASTERY_CHECK", "", "UNKNOWN"]) assert.equal(math.showIntegerExploration(state, "Add integers"), false);
  for (const name of ["Add integers", "Integer Operations", "Signed Number Operations"]) assert.equal(math.showIntegerExploration("GUIDED_PRACTICE", name), true);
  assert.equal(math.showIntegerExploration("REMEDIATION", "Subtract integers"), true);
  assert.equal(math.showIntegerExploration("GUIDED_PRACTICE", "Multiply integers"), false);
});

test("actual React handlers update movement, emit bounded events and check practice", () => {
  // Minimal hook driver exercises real event handlers; SSR above exercises real React rendering.
  let state = [], cursor = 0;
  const emitted = [];
  const hooked = load("./InteractiveIntegerNumberLine.tsx", { ...imports, react: {
    useId: () => "test",
    useState: initial => { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
  } });
  function render() { cursor = 0; const wrapper = hooked.InteractiveIntegerNumberLine({ independentAssessment: false, onMathEvent: e => emitted.push(e) }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== "object" ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  let tree = nodes(render());
  tree.find(n => n.props.id === "test-operand").props.onChange({ target: { value: "5" } });
  tree = nodes(render());
  assert.equal(emitted.at(-1).result, -7);
  assert.equal(events.isMathInteractionEvent(emitted.at(-1)), true);
  tree.find(n => n.props.id === "test-answer").props.onChange({ target: { value: "2" } });
  tree = nodes(render());
  tree.find(n => n.type === "button" && n.props.children === "Check practice").props.onClick();
  tree = nodes(render());
  assert.match(tree.find(n => n.props.id === "test-feedback").props.children, /^Correct/);
  tree.find(n => n.type === "button" && n.props.children === "Next practice").props.onClick();
  tree = nodes(render());
  assert.equal(tree.find(n => n.props.id === "test-answer").props.value, "");
  assert.equal(tree.find(n => n.props.id === "test-feedback").props.children, "");
});

test("seed mapping is deterministic and bounded", () => {
  for (const seed of [-11, -1, 0, 1, 5, 11, 100]) {
    const index = math.integerPracticeIndexFromSeed(seed);
    assert.ok(index >= 0 && index < math.INTEGER_PRACTICE.length);
    assert.equal(index, math.integerPracticeIndexFromSeed(seed));
  }
  assert.throws(() => math.integerPracticeIndexFromSeed(1.5));
});

test("changing seed resets practice index, answer and feedback", () => {
  let state = [], cursor = 0;
  const hooked = load("./InteractiveIntegerNumberLine.tsx", { ...imports, react: {
    useId: () => "seedtest",
    useState: initial => { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
  } });
  function render(seed) { cursor = 0; const wrapper = hooked.InteractiveIntegerNumberLine({ independentAssessment: false, seed }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== "object" ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  let tree = nodes(render(0));
  tree.find(n => n.props.id === "seedtest-answer").props.onChange({ target: { value: "2" } });
  tree = nodes(render(0));
  tree.find(n => n.type === "button" && n.props.children === "Check practice").props.onClick();
  tree = nodes(render(3));
  assert.equal(tree.find(n => n.props.id === "seedtest-answer").props.value, "");
  assert.equal(tree.find(n => n.props.id === "seedtest-feedback").props.children, "");
  assert.ok(tree.some(n => typeof n.props?.children === "string" && n.props.children.includes("Separate practice 4 of")));
});
