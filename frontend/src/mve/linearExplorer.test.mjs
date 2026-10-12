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
const math = load("./linearExplorer.ts");
const events = load("./interactions.ts");
const registry = load("./rendererRegistry.ts");
const visual = load("../components/ProblemVisual.tsx", { "../mve/rendererRegistry": registry });
const imports = { "./linearExplorer": math, "../components/ProblemVisual": visual };
const { InteractiveLinearExplorer: Component } = load("./InteractiveLinearExplorer.tsx", imports);

test("702 parameter sets preserve exact slope and table identities", () => {
  for (let rise = -6; rise <= 6; rise++) for (let run = 1; run <= 6; run++) for (let b = -4; b <= 4; b++) {
    const m = math.linearModel(rise, run, b);
    assert.equal(m.slope.numerator * run, rise * m.slope.denominator);
    for (const { x, y } of m.rows) assert.equal(y.numerator * run, (rise * x + b * run) * y.denominator);
    assert.equal(events.isMathInteractionEvent({ schema_version: 1, type: "LINEAR_PARAMETERS_CHANGED", rise, run, intercept: b }), true);
  }
});
test("zero slope, negative fractions, equivalent answers and invalid inputs", () => {
  assert.deepEqual(math.rational(0, -5), { numerator: 0, denominator: 1 });
  assert.deepEqual(math.rational(6, -4), { numerator: -3, denominator: 2 });
  assert.equal(math.formatRational(math.rational(4, 2)), "2");
  for (const args of [[NaN, 2, 1], [1, 0, 1], [1, -2, 1], [7, 2, 1], [1, 2, 5], [0.5, 2, 1]]) assert.throws(() => math.linearModel(...args));
  assert.throws(() => math.rational(1, 0));
  assert.throws(() => math.rational(10001, 1));
  for (const answer of ["1/2", "2/4", "-1/-2"]) assert.equal(math.checkSlope(0, answer).correct, true);
  for (const [index, answer] of ["1/2", "-3/2", "0", "2"].entries()) assert.equal(math.checkSlope(index, answer).correct, true);
  for (const answer of ["", "1/0", "0.5", "2e0", "3", "2/1", "1/2 extra"]) assert.equal(math.checkSlope(0, answer).correct, false);
  assert.throws(() => math.checkSlope(99, "1"));
  const event = { schema_version: 1, type: "LINEAR_PARAMETERS_CHANGED", rise: 1, run: 2, intercept: 0 };
  for (const change of [{ run: 0 }, { rise: 0.5 }, { intercept: 5 }, { student_id: "test" }]) assert.equal(events.isMathInteractionEvent({ ...event, ...change }), false);
});
test("real rendered controls, table and graph are accessible and assessment fails closed", () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false }));
  for (const term of ["<svg", "<caption>", 'scope="col"', 'aria-live="polite"', "focus-visible:outline", "Observe", "Manipulate", "Explain", "Practice", "2/3", "run 3", "rise 2"]) assert.ok(html.includes(term), term);
  assert.equal((html.match(/type="range"/g) ?? []).length, 3);
  for (const [, id] of html.matchAll(/<label[^>]*for="([^"]+)"/g)) assert.ok(html.includes(`id="${id}"`));
  for (const mode of [true, undefined, null]) assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: mode })), "");
  for (const state of ["INDEPENDENT_PRACTICE", "ASSESSMENT", "MASTERY_CHECK", ""]) assert.equal(math.showLinearExploration(state, "Slope-Intercept Form"), false);
  assert.equal(math.showLinearExploration("GUIDED_PRACTICE", "Slope-Intercept Form"), true);
  assert.equal(math.showLinearExploration("REMEDIATION", "Slope Intercept"), true);
  assert.equal(math.showLinearExploration("GUIDED_PRACTICE", "Quadratic equations"), false);
});
test("corner intersections produce a visible line rather than duplicate endpoints", () => {
  const html = renderToStaticMarkup(React.createElement(visual.default, { spec: { type: "linear_graph", m_num: 6, m_den: 5, b: 2, min: -10, max: 10 } }));
  const curve = html.match(/<line[^>]+class="viz-curve"/)[0];
  const coordinates = Object.fromEntries([...curve.matchAll(/(x1|y1|x2|y2)="([^"]+)"/g)].map(m => [m[1], Number(m[2])]));
  assert.ok(coordinates.x1 !== coordinates.x2 || coordinates.y1 !== coordinates.y2);
  for (const n of Object.values(coordinates)) assert.ok(Number.isFinite(n) && n >= 29.999 && n <= 310.001);
});
test("real handlers update graph, table and semantic event and reset practice feedback", () => {
  let state = [], cursor = 0;
  const emitted = [];
  const hooked = load("./InteractiveLinearExplorer.tsx", { ...imports, react: {
    useId: () => "linear",
    useState: initial => { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
  } });
  function render() { cursor = 0; const wrapper = hooked.InteractiveLinearExplorer({ independentAssessment: false, onMathEvent: e => emitted.push(e) }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== "object" ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  let tree = nodes(render());
  tree.find(n => n.props.id === "linear-rise").props.onChange({ target: { value: "-3" } });
  tree = nodes(render());
  assert.equal(tree.find(n => n.props.spec).props.spec.m_num, -3);
  assert.equal(events.isMathInteractionEvent(emitted.at(-1)), true);
  tree.find(n => n.props.id === "linear-answer").props.onChange({ target: { value: "2/4" } });
  tree = nodes(render());
  tree.find(n => n.type === "button" && n.props.children === "Check slope").props.onClick();
  tree = nodes(render());
  assert.match(tree.find(n => n.props.id === "linear-feedback").props.children, /^Correct/);
  tree.find(n => n.type === "button" && n.props.children === "Next practice").props.onClick();
  tree = nodes(render());
  assert.equal(tree.find(n => n.props.id === "linear-answer").props.value, "");
  assert.equal(tree.find(n => n.props.id === "linear-feedback").props.children, "");
});
