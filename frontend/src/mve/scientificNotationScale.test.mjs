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

const math = load("./scientificNotationScale.ts");
const events = load("./interactions.ts");
const { InteractiveScientificNotationScale: Component } = load("./InteractiveScientificNotationScale.tsx", {
  "./scientificNotationScale": math,
});

test("bounded inverse scale moves preserve exact value and are reversible", () => {
  for (const example of math.SCIENTIFIC_SCALE_EXAMPLES) {
    const initial = math.initialScientificScaleState(example);
    for (let steps = 0; steps < 3; steps += 1) {
      const left = math.movePowerOfTen(initial, "COEFFICIENT_DIVIDE_BY_TEN");
      assert.equal(left.coefficient_power + left.exponent, initial.invariant_power);
      assert.deepEqual(math.movePowerOfTen(left, "COEFFICIENT_MULTIPLY_BY_TEN"), initial);
    }
  }
  assert.throws(() => math.scientificScaleExampleFromSeed(-1));
  assert.throws(() => math.movePowerOfTen({ significant_digits: 45, coefficient_power: -8, exponent: 8, invariant_power: 0 }, "COEFFICIENT_DIVIDE_BY_TEN"));
});

test("formatting and normalization use exact place value", () => {
  assert.equal(math.formatScaleCoefficient(45, 2), "4500");
  assert.equal(math.formatScaleCoefficient(45, -1), "4.5");
  assert.equal(math.formatScaleCoefficient(72, -6), "0.000072");
  assert.equal(math.isNormalizedScientificState({ significant_digits: 45, coefficient_power: -1, exponent: 3, invariant_power: 2 }), true);
  assert.equal(math.isNormalizedScientificState({ significant_digits: 45, coefficient_power: 0, exponent: 2, invariant_power: 2 }), false);
});

test("reasoning diagnosis is deterministic and does not reveal the target", () => {
  const normalized = { significant_digits: 45, coefficient_power: -1, exponent: 3, invariant_power: 2 };
  const wrong = math.evaluateScaleReasoning(normalized, "SAME_DIRECTION_PRESERVES_VALUE", "COEFFICIENT_AND_POWER_ARE_INVERSE_FACTORS");
  assert.equal(wrong.diagnosis, "SCI.EXPONENT.DIRECTION");
  assert.equal(/4\.5|10\^3|exponent 3/i.test(wrong.feedback), false);
  assert.equal(math.evaluateScaleReasoning(normalized, "INVERSE_CHANGES_PRESERVE_VALUE", "COEFFICIENT_AND_POWER_ARE_INVERSE_FACTORS").correct, true);
});

test("fresh transfer accepts exact equivalents and rejects leakage-prone malformed answers", () => {
  const small = math.SCIENTIFIC_SCALE_EXAMPLES[1];
  assert.equal(math.evaluateScientificTransfer(small, "7.2", "-5").correct, true);
  assert.equal(math.evaluateScientificTransfer(small, "72", "-6").diagnosis, "SCI.NOT_NORMALIZED");
  const wrong = math.evaluateScientificTransfer(small, "7.2", "5");
  assert.equal(wrong.diagnosis, "SCI.EXPONENT.DIRECTION");
  assert.equal(/-5|7\.2 ×/i.test(wrong.feedback), false);
  assert.equal(math.evaluateScientificTransfer(small, "NaN", "-5").diagnosis, "SCI.INVALID_EXACT_RESPONSE");
  assert.equal(math.evaluateScientificTransfer(small, "7.2", "9007199254740992").diagnosis, "SCI.INVALID_EXACT_RESPONSE");
});

test("semantic scale events are bounded, exact and privacy-safe", () => {
  const event = {
    schema_version: 1,
    type: "SCIENTIFIC_NOTATION_SCALE_CHANGED",
    significant_digits: 45,
    coefficient_power: -1,
    exponent: 3,
    invariant_power: 2,
  };
  assert.equal(events.isMathInteractionEvent(event), true);
  assert.equal(events.isMathInteractionEvent({ ...event, invariant_power: 3 }), false);
  assert.equal(events.isMathInteractionEvent({ ...event, coefficient_power: -9 }), false);
  assert.equal(events.isMathInteractionEvent({ ...event, student_id: "child-1" }), false);
});

test("guided component exposes equivalent keyboard and screen-reader state and fails closed", () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false, seed: 0 }));
  for (const text of [
    "Guided scientific notation exponent scale",
    "Observe", "Predict", "Manipulate", "Explain", "Transfer and verify",
    "Divide coefficient by 10; increase exponent",
    "Multiply coefficient by 10; decrease exponent",
    "Power-of-ten exponent scale", "Nonvisual equivalent state",
    "aria-live=\"polite\"", "aria-atomic=\"true\"", "motion-reduce:transition-none",
  ]) assert.ok(html.includes(text), text);
  assert.equal(html.includes("7.2 × 10^-5"), false);
  for (const value of [true, undefined, null]) {
    assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: value, seed: 0 })), "");
  }
  assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: false, seed: -1 })), "");
});

test("seeded remount contract is explicit and examples are deterministic", () => {
  assert.deepEqual(math.scientificScaleExampleFromSeed(0), math.scientificScaleExampleFromSeed(4));
  assert.notDeepEqual(math.scientificScaleExampleFromSeed(0), math.scientificScaleExampleFromSeed(1));
  const source = readFileSync(new URL("./InteractiveScientificNotationScale.tsx", import.meta.url), "utf8");
  assert.match(source, /<GuidedScientificNotationScale key=\{seed\}/);
});

test("actual controls update exact state, emit semantic evidence and reset", () => {
  let state = [], cursor = 0; const emitted = [];
  const hooked = load("./InteractiveScientificNotationScale.tsx", {
    "./scientificNotationScale": math,
    react: {
      useId: () => "sci",
      useState: initial => {
        const index = cursor++;
        if (!(index in state)) state[index] = typeof initial === "function" ? initial() : initial;
        return [state[index], value => { state[index] = typeof value === "function" ? value(state[index]) : value; }];
      },
    },
  });
  function render() {
    cursor = 0;
    const wrapper = hooked.InteractiveScientificNotationScale({ independentAssessment: false, seed: 0, onMathEvent: event => emitted.push(event) });
    return wrapper.type(wrapper.props);
  }
  function nodes(node) {
    if (!node || typeof node !== "object") return [];
    const expanded = typeof node.type === "function" ? node.type(node.props) : null;
    return [node, ...nodes(expanded), ...React.Children.toArray(node.props?.children).flatMap(nodes)];
  }
  const button = label => nodes(render()).find(node => node.type === "button" && node.props.children === label);
  button("Divide coefficient by 10; increase exponent").props.onClick();
  assert.deepEqual(emitted.at(-1), {
    schema_version: 1,
    type: "SCIENTIFIC_NOTATION_SCALE_CHANGED",
    significant_digits: 45,
    coefficient_power: 1,
    exponent: 1,
    invariant_power: 2,
  });
  assert.equal(events.isMathInteractionEvent(emitted.at(-1)), true);
  assert.ok(nodes(render()).some(node => React.Children.toArray(node.props?.children).join("").includes("450 × 10^1")));
  button("Reset this scale").props.onClick();
  assert.ok(nodes(render()).some(node => React.Children.toArray(node.props?.children).join("").includes("4500 × 10^0")));
});
