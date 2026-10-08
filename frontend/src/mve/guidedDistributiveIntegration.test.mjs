import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
const guided = await readFile(new URL("./GuidedDistributivePractice.tsx", import.meta.url), "utf8");
const player = await readFile(new URL("./PedagogicalAnimation.tsx", import.meta.url), "utf8");

test("guided MVE is limited to guided and remediation states", () => {
  assert.match(workspace, /workspace\.state === "GUIDED_PRACTICE" \|\| workspace\.state === "REMEDIATION"/);
  assert.match(workspace, /GuidedDistributivePractice key=/);
  assert.match(workspace, /independentAssessment=/);
  assert.match(guided, /if \(props\.independentAssessment\) return null/);
});

test("guided MVE delegates accessible playback to the existing player", () => {
  assert.match(guided, /<PedagogicalAnimation/);
  for (const label of ["Pause", "Play", "Previous step", "Next step", "Replay"]) {
    assert.ok(player.includes(label), `missing ${label}`);
  }
  assert.match(player, /aria-live="polite"/);
  assert.match(player, /prefers-reduced-motion: reduce/);
  assert.match(player, /clearTimeout\(timer\)/);
  assert.match(player, /aria-label="Animation playback controls"/);
});

test("guided MVE uses deterministic misconception classification", () => {
  assert.match(guided, /checkDistributiveCoefficients\(lesson/);
  assert.match(guided, /MISSED_SECOND_TERM/);
  assert.match(guided, /COEFFICIENT_ERROR/);
});
