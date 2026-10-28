import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const src = await readFile(new URL("../publishedLearningFlow.ts", import.meta.url), "utf8");
const js = ts.transpileModule(src, { compilerOptions: {
  module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022,
}}).outputText;
const api = await import("data:text/javascript;base64," + Buffer.from(js).toString("base64"));
const base = { independent_evidence_eligible: false, mastery_eligible: false, xp_earned: 0 };
const choices = [{ id: "OPTION_1", text: "First" }, { id: "OPTION_2", text: "Second" }];
const task = (mode) => ({ variant_id: "opaque-server-variant", mode, prompt: "Solve the equation" });

test("published recovery is a narrow candidate, never authorized by mutable labels", () => {
  assert.equal(api.canOfferPublishedRecovery("DIAGNOSE", true, false, false), true);
  assert.equal(api.canOfferPublishedRecovery("GUIDED_PRACTICE", true, false, false), true);
  for (const state of ["REMEDIATION", "INDEPENDENT_PRACTICE", "MASTERY_CHECK", "COMPLETE",
    "REVIEW", "Grade 8 Equations", "Signed Integers", "", null, undefined]) {
    assert.equal(api.canOfferPublishedRecovery(state, true, false, false), false);
  }
  for (const params of [
    ["DIAGNOSE", false, false, false], ["DIAGNOSE", true, true, false],
    ["DIAGNOSE", true, false, true],
  ]) assert.equal(api.canOfferPublishedRecovery(...params), false);
});

test("server-authorized exact stages accept only noncredit, correctly typed payloads", () => {
  const accepted = [
    { ...base, stage: "CONFIRM_REASONING", problem_id: "server-owned-problem", prompt: "Why?", choices },
    { ...base, stage: "SOCRATIC_REPAIR", repair_check: "Choose", repair_choices: choices },
    { ...base, stage: "SOCRATIC_REPAIR_RETRY", repair_check: "An exact value", repair_choices: [] },
    { ...base, stage: "GUIDED_RETEST", guided_retest_task: task("GUIDED") },
    { ...base, stage: "GUIDED_RETEST_RETRY", guided_retest_task: task("GUIDED"), correct: false },
    { ...base, stage: "READY_FOR_TRANSFER_CONFIRMATION", correct: true },
    { ...base, stage: "INDEPENDENT_EXIT", independent_task: task("INDEPENDENT"), hints_allowed: false },
    { ...base, stage: "TRANSFER_FEEDBACK_ONLY", correct: true },
    { ...base, stage: "MASTERY_VERIFICATION_FEEDBACK_ONLY", verification_task: task("MASTERY"), hints_allowed: false },
    { ...base, stage: "MASTERY_VERIFICATION_FEEDBACK_ONLY", correct: true },
  ];
  for (const stage of accepted) assert.equal(api.parsePublishedStage(stage)?.stage, stage.stage);
});

test("missing/malformed/rewarding/cross-mode stage responses fail closed", () => {
  for (const stage of [
    undefined, null, {}, { stage: "GUIDED_RETEST" },
    { ...base, stage: "GUIDED_RETEST", guided_retest_task: task("MASTERY") },
    { ...base, stage: "INDEPENDENT_EXIT", independent_task: task("GUIDED"), hints_allowed: false },
    { ...base, stage: "INDEPENDENT_EXIT", independent_task: task("INDEPENDENT") },
    { ...base, stage: "MASTERY_VERIFICATION_FEEDBACK_ONLY", verification_task: task("MASTERY") },
    { ...base, stage: "SOCRATIC_REPAIR", repair_check: "" },
    { ...base, stage: "CONFIRM_REASONING", problem_id: "x", prompt: "Why", choices: [] },
    { ...base, stage: "CONFIRM_REASONING", problem_id: "x", prompt: "Why", choices: [{ id: "", text: "Good" }] },
    { ...base, stage: "GUIDED_RETEST", guided_retest_task: task("GUIDED"), mastery_eligible: true },
    { ...base, stage: "TRANSFER_FEEDBACK_ONLY", independent_evidence_eligible: true },
    { ...base, stage: "MASTERY_VERIFICATION_FEEDBACK_ONLY", xp_earned: 100 },
    { ...base, stage: "UNKNOWN_STAGE" },
    { ...base, stage: "MASTERY_VERIFICATION_FEEDBACK_ONLY", correct: "yes" },
  ]) assert.equal(api.parsePublishedStage(stage), null);
});

test("Workspace requires a persisted server-eligible wrong response; never display regex", async () => {
  const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
  const panel = await readFile(new URL("../components/PublishedLearningRecovery.tsx", import.meta.url), "utf8");
  assert.match(workspace, /canOfferPublishedRecovery\(/);
  assert.match(workspace, /publishedRecovery\.sessionId === sessionId/);
  assert.match(workspace, /\["DIAGNOSE", "GUIDED_PRACTICE", "REMEDIATION"\]/);
  assert.match(panel, /published-reasoning\?problem_id=/);
  assert.match(panel, /if \(!stage && !error\) return null/);
  assert.match(panel, /revision\.current/);
  assert.match(panel, /transfer\/respond/);
  assert.doesNotMatch(panel, /skill_name|MATH\.[A-Z_]+|xp_earned\s*=|mastery_eligible\s*=\s*true/);
});
