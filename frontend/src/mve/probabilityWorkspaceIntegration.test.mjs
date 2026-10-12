import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

// Regression for integrating the independent-stage probability explorer without
// inventing a server-owned canonical identity or enabling an assessment route.
const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
const interactions = await readFile(new URL("./interactions.ts", import.meta.url), "utf8");
const browser = await readFile(new URL("../../../e2e/mve-guided-browser.mjs", import.meta.url), "utf8");
const js = ts.transpileModule(interactions, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { isMathInteractionEvent } = await import(
  `data:text/javascript;base64,${Buffer.from(js).toString("base64")}`
);

test("probability route is default-off, including display-name collisions and all assessment states", () => {
  assert.doesNotMatch(workspace, /showProbabilityTreeExploration\(/);
  assert.doesNotMatch(workspace, /<InteractiveProbabilityTree\b/);
  assert.match(workspace, /Probability-tree route remains disabled until an approved server-owned capability/);
  assert.match(workspace, /showPolynomialDivisionExploration\(workspace.state, undefined\)/);
  assert.match(workspace, /integerAdditionEligible\(workspace.state, learn\)/);
  assert.match(workspace, /<InteractiveFractionBars\b/);
  assert.match(workspace, /<InteractiveFractionAddition\b/);
  for (const identity of [undefined, null, "", "Probability", "Compound Probability",
    "Probability Trees", "Sample Space", "MATH.PROB.UNAPPROVED"]) {
    // No proposed or mutable identity is consumed by Workspace: the
    // component does not mount in guided, remediation or independent phases.
    for (const state of ["GUIDED_PRACTICE", "REMEDIATION", "DIAGNOSE",
      "INDEPENDENT_PRACTICE", "MASTERY_CHECK", "COMPLETE"]) {
      assert.equal(workspace.includes("showProbabilityTreeExploration(workspace.state, workspace.focus.skill_name)"), false,
        `${identity} must not authorize ${state}`);
    }
  }
});

test("probability semantic events are bounded and do not expose learner information", () => {
  const event = { schema_version: 1, type: "PROBABILITY_TREE_CHANGED",
    first_favorable: 3, first_total: 8, second_favorable: 1, second_total: 2 };
  assert.equal(isMathInteractionEvent(event), true);
  for (const invalid of [
    { ...event, first_total: 1 }, { ...event, first_total: 13 },
    { ...event, first_favorable: 8 }, { ...event, second_favorable: 0 },
    { ...event, first_favorable: 1.5 }, { ...event, first_total: "8" },
    { ...event, learner_id: "student-123" }, { ...event, attempt_id: "a" },
    { ...event, schema_version: 2 },
  ]) assert.equal(isMathInteractionEvent(invalid), false);
});

test("browser integration enforces prediction before manipulation and assessment unmount", () => {
  assert.match(browser, /Lock prediction/);
  assert.match(browser, /First event total outcomes:'\)\.isDisabled\(\)/);
  assert.match(browser, /assert\.equal\(await probability\.count\(\), 0\)/);
  assert.match(browser, /probability\.getByLabel\('Reasoning choice'\)\.selectOption\('multiply'\)/);
  assert.match(browser, /probability\.getByRole\('button', \{ name: 'Check repair' \}\)\.click\(\)/);
  assert.match(browser, /probability\.getByRole\('region', \{ name: 'Misconception repair' \}\)\.count\(\)/);
  assert.match(browser, /probability\.getByRole\('region', \{ name: 'Probability model transfer' \}\)\.count\(\)/);
  assert.match(browser, /probability\.getByLabel\('First event total outcomes:'\)\.isDisabled\(\)/);
});
