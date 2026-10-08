import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
const guided = await readFile(new URL("./GuidedDistributivePractice.tsx", import.meta.url), "utf8");

test("guided MVE mounts only for guided or remediation states", () => {
  assert.match(workspace, /workspace\.state === "GUIDED_PRACTICE" \|\| workspace\.state === "REMEDIATION"/);
  assert.match(workspace, /GuidedDistributivePractice key=/);
  assert.doesNotMatch(workspace, /workspace\.state === "INDEPENDENT_PRACTICE"\) &&\s*<GuidedDistributivePractice/);
});
test("guided MVE provides accessible transport and nonvisual steps", () => {
  for (const label of ["Pause", "Play", "Previous step", "Next step", "Replay"]) {
    assert.ok(guided.includes(label), `missing ${label}`);
  }
  assert.match(guided, /aria-live="polite"/);
  assert.match(guided, /prefers-reduced-motion: reduce/);
  assert.match(guided, /independentAssessment\) return null/);
});
test("guided MVE reuses deterministic misconception classification", () => {
  assert.match(guided, /checkDistributiveCoefficients\(lesson/);
  assert.match(guided, /MISSED_SECOND_TERM/);
  assert.match(guided, /COEFFICIENT_ERROR/);
});
