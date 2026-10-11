import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

// Regression tests for the two files reconciled when #347 moved onto main.
// This is a source/contract suite; the browser journey and AT review remain
// independent gates.
const interactionsSource = await readFile(new URL("./interactions.ts", import.meta.url), "utf8");
const workspaceSource = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
const code = ts.transpileModule(interactionsSource, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { isMathInteractionEvent } = await import(
  `data:text/javascript;base64,${Buffer.from(code).toString("base64")}`
);

test("reconciled Workspace retains existing guided boundaries and default-off equation route", () => {
  assert.match(workspaceSource, /integerAdditionEligible\(workspace\.state, learn\)/);
  assert.match(workspaceSource, /import\.meta\.env\.VITE_ENABLE_DRAFT_MTH1W_EQUATION_FLOW === "true"/);
  assert.match(workspaceSource, /equationEquivalenceEnabled &&/);
  assert.match(workspaceSource, /showPolynomialDivisionExploration\(workspace\.state, undefined\)/);
  assert.match(workspaceSource, /<InteractiveFractionBars\b/);
  assert.match(workspaceSource, /<InteractiveFractionAddition\b/);
  assert.doesNotMatch(workspaceSource, /showIntegerExploration\(/);
  assert.doesNotMatch(workspaceSource, /<<<<<<<|=======|>>>>>>>/);
});

test("reconciled interaction schema retains polynomial and exact fraction validation", () => {
  const polynomial = {
    schema_version: 1, type: "POLYNOMIAL_DIVISION_MANIPULATED", divided_terms: 2,
    coefficient_reason: "DIVIDEND_COEFFICIENT_DIVIDED_BY_DIVISOR_COEFFICIENT",
    exponent_reason: "DIVIDEND_EXPONENT_MINUS_DIVISOR_EXPONENT",
    domain_x: true, domain_y: false,
  };
  const fraction = {
    schema_version: 1, type: "FRACTION_ADDITION_EXPLORED",
    first: { numerator: 1, denominator: 2 },
    second: { numerator: 1, denominator: 3 },
    common_denominator: 6, sum_numerator: 5, sum_denominator: 6,
  };
  assert.equal(isMathInteractionEvent(polynomial), true);
  assert.equal(isMathInteractionEvent({ ...polynomial, divided_terms: 5 }), false);
  assert.equal(isMathInteractionEvent(fraction), true);
  assert.equal(isMathInteractionEvent({ ...fraction, sum_numerator: 6 }), false);
  assert.equal(isMathInteractionEvent({ ...fraction, common_denominator: 12 }), false);
});

test("reconciled equation events accept bounded evidence and reject malformed transformations", () => {
  const transform = {
    schema_version: 1, type: "EQUATION_TRANSFORMATION_APPLIED",
    operation: "SCALE_BOTH", amount_numerator: 2, amount_denominator: 3,
    preserved: true,
  };
  const diagnosis = {
    schema_version: 1, type: "EQUATION_ATTEMPT_DIAGNOSED",
    diagnosis: "EQ.OP.ONE_SIDE", phase: "FRESH_EXIT",
  };
  assert.equal(isMathInteractionEvent(transform), true);
  assert.equal(isMathInteractionEvent(diagnosis), true);
  for (const invalid of [
    { ...transform, amount_numerator: 0 },
    { ...transform, amount_denominator: 0 },
    { ...transform, preserved: false },
    { ...transform, untrusted: true },
    { ...diagnosis, diagnosis: "INVENTED_CLASSIFICATION" },
    { ...diagnosis, phase: "MASTERY_CHECK" },
  ]) {
    assert.equal(isMathInteractionEvent(invalid), false);
  }
});
