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
    { ...base, stage: "COMPLETE_FEEDBACK_ONLY" },
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
  assert.match(workspace, /published-recovery\\/current/);
  assert.match(workspace, /recoveryDiscoveryRef\\.current/);
  assert.match(workspace, /activeSessionRef\\.current !== requestedSession/);
  assert.match(workspace, /recovered\\.independent_evidence_eligible !== false/);
  assert.match(workspace, /recovered\\.mastery_eligible !== false/);
  assert.match(workspace, /!activeExtensionProblem/);
  assert.doesNotMatch(workspace, /sessionStorage|localStorage/);
  assert.match(panel, /published-recovery\?problem_id=/);
  assert.match(panel, /if \(!stage && !error\) return null/);
  assert.match(panel, /revision\.current/);
  assert.match(panel, /transfer\/respond/);
  assert.doesNotMatch(panel, /skill_name|MATH\.[A-Z_]+|xp_earned\s*=|mastery_eligible\s*=\s*true/);
});


test("failed recovery displays an explicit safe continuation rather than silently disappearing", async () => {
  const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
  assert.match(workspace, /This recovery step could not be restored or was revoked/);
  assert.match(workspace, /server-authorized fresh task/);
  assert.match(workspace, /setPublishedRecovery\(null\)/);
});

test("hard reload discovery is session-scoped, fail-closed and does not guess content", async () => {
  const source = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
  assert.match(source, /recoveryDiscoveredSessionRef\\.current = sessionId/);
  assert.match(source, /encodeURIComponent\\(requestedSession\\)/);
  assert.match(source, /recovered\\.stage === "NONE"/);
  assert.match(source, /typeof recovered\\.problem_id !== "string"/);
  assert.match(source, /setPublishedRecovery\\(\\(existing\\) => existing \\?\\?/);
  assert.match(source, /recoveryDiscoveryRef\\.current \\+= 1/);
  assert.match(source, /onUnavailable=\\{\\(\\) => setPublishedRecovery\\(null\\)\\}/);
});
