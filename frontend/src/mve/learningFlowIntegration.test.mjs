import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const file = await readFile(
  new URL("../learningFlowInteractions.ts", import.meta.url),
  "utf8",
);
const js = ts.transpileModule(file, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const api = await import(
  `data:text/javascript;base64,${Buffer.from(js).toString("base64")}`
);

test("integer addition routing requires the explicit guided interaction", () => {
  const allowed = { guided_interactions: ["MATH.INT.ADD"] };
  assert.equal(api.integerAdditionEligible("GUIDED_PRACTICE", allowed), true);
  assert.equal(api.integerAdditionEligible("REMEDIATION", allowed), true);

  for (const state of [
    "DIAGNOSE",
    "INDEPENDENT_PRACTICE",
    "MASTERY_CHECK",
    "COMPLETE",
  ]) {
    assert.equal(api.integerAdditionEligible(state, allowed), false);
  }
});

test("display labels, malformed metadata and unrelated families fail closed", () => {
  const rejected = [
    undefined,
    null,
    {},
    { guided_interactions: [] },
    { guided_interactions: ["Signed Number Operations"] },
    { guided_interactions: ["Integer Operations"] },
    { guided_interactions: ["MATH.INT.SUB"] },
    { guided_interactions: ["MATH.INT.MUL", "MATH.INT.DIV"] },
  ];
  for (const learn of rejected) {
    assert.equal(
      api.integerAdditionEligible("GUIDED_PRACTICE", learn),
      false,
    );
  }
});

const mth1wTwoStep = {
  curriculumName: "Grade 9 Mathematics (MTH1W)",
  jurisdiction: "Ontario, Canada",
  skillName: "Two-Step and Multi-Step Equations",
};

test("draft equation routing requires the exact MTH1W identity and explicit runtime gate", () => {
  assert.equal(api.equationEquivalenceEligible("GUIDED_PRACTICE", mth1wTwoStep, true), true);
  assert.equal(api.equationEquivalenceEligible("REMEDIATION", {
    ...mth1wTwoStep,
    skillName: "Multi-Step Equations with Variables on Both Sides",
  }, true), true);

  assert.equal(api.equationEquivalenceEligible("GUIDED_PRACTICE", mth1wTwoStep), false);
  assert.equal(api.equationEquivalenceEligible("GUIDED_PRACTICE", mth1wTwoStep, false), false);
  for (const state of ["DIAGNOSE", "INDEPENDENT_PRACTICE", "MASTERY_CHECK", "COMPLETE"]) {
    assert.equal(api.equationEquivalenceEligible(state, mth1wTwoStep, true), false);
  }
});

test("equation routing rejects lookalike curricula, jurisdictions and skills", () => {
  for (const identity of [
    undefined,
    null,
    { ...mth1wTwoStep, curriculumName: "MCPS Algebra 1" },
    { ...mth1wTwoStep, jurisdiction: "Maryland, USA" },
    { ...mth1wTwoStep, skillName: "One-Step Equations" },
    { ...mth1wTwoStep, skillName: "Two Step and Multi Step Equations" },
    { ...mth1wTwoStep, skillName: "Scientific Notation" },
  ]) {
    assert.equal(api.equationEquivalenceEligible("GUIDED_PRACTICE", identity, true), false);
  }
});

test("equation variants replay deterministically and preserve the both-sides exit", () => {
  const first = api.equationEquivalenceExampleIndex("problem-a", mth1wTwoStep.skillName);
  assert.equal(first, api.equationEquivalenceExampleIndex("problem-a", mth1wTwoStep.skillName));
  assert.ok([0, 1].includes(first));
  assert.equal(api.equationEquivalenceExampleIndex(
    "any-problem",
    "Multi-Step Equations with Variables on Both Sides",
  ), 2);
  const variants = new Set(Array.from({ length: 40 }, (_, index) =>
    api.equationEquivalenceExampleIndex(`problem-${index}`, mth1wTwoStep.skillName)));
  assert.deepEqual([...variants].sort(), [0, 1]);
});
