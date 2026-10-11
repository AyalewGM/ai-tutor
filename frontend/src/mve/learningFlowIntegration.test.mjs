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
