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
  assert.ok(workspace.includes("published-recovery/current"));
  assert.ok(workspace.includes("recoveryDiscoveryRef.current"));
  assert.ok(workspace.includes("activeSessionRef.current !== requestedSession"));
  assert.ok(workspace.includes("recovered.independent_evidence_eligible !== false"));
  assert.ok(workspace.includes("recovered.mastery_eligible !== false"));
  assert.match(workspace, /!activeExtensionProblem/);
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
  assert.ok(source.includes("recoveryDiscoveredSessionRef.current = sessionId"));
  assert.ok(source.includes("encodeURIComponent(requestedSession)"));
  assert.ok(source.includes('recovered.stage === "NONE"'));
  assert.ok(source.includes('typeof recovered.problem_id !== "string"'));
  assert.ok(source.includes("setPublishedRecovery((existing) => existing ??"));
  assert.ok(source.includes("recoveryDiscoveryRef.current += 1"));
  assert.ok(source.includes("onUnavailable="));
  assert.ok(source.includes("setPublishedRecovery(null)"));
});


test("reload preserves strict persisted transfer outcomes without granting credit", async () => {
  for (const correct of [true, false]) {
    const reloaded = JSON.parse(JSON.stringify({
      ...base, stage: "TRANSFER_FEEDBACK_ONLY", correct, hints_allowed: false,
    }));
    const parsed = api.parsePublishedStage(reloaded);
    assert.equal(parsed?.correct, correct);
    assert.equal(parsed?.xp_earned, 0);
    assert.equal(parsed?.independent_evidence_eligible, false);
    assert.equal(parsed?.mastery_eligible, false);
    assert.equal(parsed?.guided_retest_task, undefined);
    assert.equal(parsed?.socratic_repair_questions, undefined);
  }
  for (const correct of ["true", "false", 1, 0, null]) {
    assert.equal(api.parsePublishedStage({ ...base, stage: "TRANSFER_FEEDBACK_ONLY", correct }), null);
  }
  const panel = await readFile(new URL("../components/PublishedLearningRecovery.tsx", import.meta.url), "utf8");
  assert.match(panel, /stage\?\.stage === "TRANSFER_FEEDBACK_ONLY" && stage\.correct === true &&/);
  assert.match(panel, /mastery\/start\?problem_id=/);
});
