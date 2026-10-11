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

const rational = load("./linearExplorer.ts");
const math = load("./polynomialDivision.ts", { "./linearExplorer": rational });
const events = load("./interactions.ts");
const imports = { "./polynomialDivision": math };
const { InteractivePolynomialDivision: Component } = load("./InteractivePolynomialDivision.tsx", imports);

test("all bounded variants divide every term exactly and reconstruct the dividend", () => {
  for (const variant of math.POLYNOMIAL_DIVISION_VARIANTS) {
    const quotient = math.quotientTerms(variant);
    assert.equal(quotient.length, variant.dividend.length);
    assert.equal(math.reconstructsDividend(variant, quotient), true);
    quotient.forEach((term, index) => assert.equal(
      math.samePolynomialTerm(math.multiplyPolynomialTerms(term, variant.divisor), variant.dividend[index]), true));
  }
  assert.equal(math.formatPolynomial(math.POLYNOMIAL_DIVISION_VARIANTS[0].dividend), "6x^3y − 10x^2");
  assert.equal(math.formatPolynomialTerm(math.quotientTerms(math.POLYNOMIAL_DIVISION_VARIANTS[1])[0]), "−4x^2y^-1");
});

test("seed selection is deterministic and malformed or out-of-bounds terms fail closed", () => {
  assert.equal(math.polynomialDivisionVariant(4).id, math.polynomialDivisionVariant(4).id);
  for (const seed of [-1, 1.5, Number.MAX_SAFE_INTEGER, "2", null]) assert.throws(() => math.polynomialDivisionVariant(seed));
  for (const value of [null, {}, { coefficient: { numerator: 1, denominator: 0 }, xExponent: 1, yExponent: 0 },
    { coefficient: { numerator: 2, denominator: 2 }, xExponent: 1, yExponent: 0 },
    { coefficient: { numerator: 1, denominator: 1 }, xExponent: 13, yExponent: 0 }]) {
    assert.equal(math.isPolynomialTerm(value), false);
  }
});

test("interaction evidence routes four accepted misconceptions without answer leakage", () => {
  const variant = math.POLYNOMIAL_DIVISION_VARIANTS[1];
  const correct = { processedTermIndexes: [0, 1], coefficientReason: "DIVIDEND_BY_DIVISOR", exponentReason: "SUBTRACT",
    restrictions: ["x", "y"], reconstructionConfirmed: true };
  assert.equal(math.diagnosePolynomialDivisionAttempt(variant, correct), null);
  assert.equal(math.diagnosePolynomialDivisionAttempt(variant, { ...correct, processedTermIndexes: [0] }), "POLY.DIV.ONE_TERM_ONLY");
  assert.equal(math.diagnosePolynomialDivisionAttempt(variant, { ...correct, coefficientReason: "DIVISOR_BY_DIVIDEND" }), "POLY.DIV.COEFFICIENT_RECIPROCAL");
  assert.equal(math.diagnosePolynomialDivisionAttempt(variant, { ...correct, exponentReason: "ADD" }), "POLY.DIV.ADD_EXPONENTS");
  assert.equal(math.diagnosePolynomialDivisionAttempt(variant, { ...correct, restrictions: ["x"] }), "POLY.DIV.DOMAIN_OMITTED");
});

test("fresh exits are deterministic, structurally fresh, and exponent repair includes a negative exponent", () => {
  for (let seed = 0; seed < math.POLYNOMIAL_DIVISION_VARIANTS.length; seed++) {
    for (const diagnosis of ["POLY.DIV.COEFFICIENT_RECIPROCAL", "POLY.DIV.ADD_EXPONENTS", "POLY.DIV.ONE_TERM_ONLY", "POLY.DIV.DOMAIN_OMITTED"]) {
      const first = math.freshPolynomialDivisionVariant(seed, diagnosis);
      const second = math.freshPolynomialDivisionVariant(seed, diagnosis);
      assert.equal(first.id, second.id);
      assert.notEqual(first.id, math.polynomialDivisionVariant(seed).id);
      if (diagnosis === "POLY.DIV.ADD_EXPONENTS") {
        assert.ok(math.quotientTerms(first).some(term => term.xExponent < 0 || term.yExponent < 0));
      }
    }
  }
});

test("semantic term events prove exact division and reject inconsistent or identifying fields", () => {
  const variant = math.POLYNOMIAL_DIVISION_VARIANTS[1];
  const event = { schema_version: 1, type: "POLYNOMIAL_TERM_DIVIDED", term_index: 0,
    dividend: variant.dividend[0], divisor: variant.divisor, quotient: math.dividePolynomialTerm(variant.dividend[0], variant.divisor) };
  assert.equal(events.isMathInteractionEvent(event), true);
  for (const change of [
    { quotient: { ...event.quotient, xExponent: event.quotient.xExponent + 1 } },
    { quotient: { ...event.quotient, coefficient: { numerator: 2, denominator: 2 } } },
    { term_index: 4 }, { student_id: "child-1" },
  ]) assert.equal(events.isMathInteractionEvent({ ...event, ...change }), false);
  const diagnosis = { schema_version: 1, type: "POLYNOMIAL_DIVISION_DIAGNOSED", diagnosis: "POLY.DIV.ADD_EXPONENTS", phase: "DIAGNOSE" };
  assert.equal(events.isMathInteractionEvent(diagnosis), true);
  assert.equal(events.isMathInteractionEvent({ ...diagnosis, answer: "-4x^2/y" }), false);
});

test("component exposes keyboard and screen-reader equivalent discrete states and fails closed in assessment", () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false, seed: 1 }));
  for (const term of ["Observe", "Predict", "Manipulate", "Explain", "Transfer and verify", "Grouped-term polynomial division state",
    "aria-live=\"polite\"", "aria-current=\"true\"", "motion-reduce:transition-none", "cannot award mastery",
    "x ≠ 0", "y ≠ 0", "Not divided yet"]) assert.ok(html.includes(term), term);
  for (const mode of [true, undefined, null]) assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: mode })), "");
  assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: false, seed: -1 })), "");
});

test("actual handlers diagnose one-term work, load a fresh repair, reconstruct, and fade support", () => {
  let state = [], cursor = 0;
  const emitted = [];
  const hooked = load("./InteractivePolynomialDivision.tsx", { ...imports, react: {
    useId: () => "poly",
    useState: initial => { const index = cursor++; if (!(index in state)) state[index] = initial;
      return [state[index], value => { state[index] = typeof value === "function" ? value(state[index]) : value; }]; },
  } });
  function render() { cursor = 0; const wrapper = hooked.InteractivePolynomialDivision({ independentAssessment: false, seed: 0,
    onMathEvent: event => emitted.push(event) }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== "object" ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  const click = label => nodes(render()).find(node => node.type === "button" && node.props.children === label).props.onClick();
  click("Divide selected term by shared divisor");
  assert.equal(events.isMathInteractionEvent(emitted[0]), true);
  click("Check my reasoning");
  assert.equal(emitted.at(-1).diagnosis, "POLY.DIV.ONE_TERM_ONLY");
  assert.doesNotMatch(String(nodes(render()).find(node => node.props?.role === "status").props.children), /−?5x|answer/i);
  click("Try a fresh related example");
  assert.ok(String(nodes(render()).find(node => node.props?.["aria-label"]?.startsWith("Expression ")).props["aria-label"]).includes("÷"));
  click("Divide selected term by shared divisor");
  click("Next term");
  click("Divide selected term by shared divisor");
  let tree = nodes(render());
  tree.filter(node => node.type === "input" && node.props.name === "poly-coefficient")[0].props.onChange();
  tree = nodes(render());
  tree.filter(node => node.type === "input" && node.props.name === "poly-exponent")[0].props.onChange();
  tree = nodes(render());
  tree.filter(node => node.type === "input" && node.props.type === "checkbox")[0].props.onChange();
  click("Verify reconstructed areas");
  click("Check my reasoning");
  tree = nodes(render());
  assert.ok(tree.some(node => String(node.props?.children).includes("INDEPENDENT READINESS")));
  assert.match(String(tree.find(node => node.props?.role === "status").props.children), /Fresh repair complete/);
});
