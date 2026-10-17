import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const source = await readFile(
  new URL("../workspaceSessionGuard.ts", import.meta.url),
  "utf8",
);
const workspaceSource = await readFile(
  new URL("../pages/Workspace.tsx", import.meta.url),
  "utf8",
);
const js = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const api = await import(
  `data:text/javascript;base64,${Buffer.from(js).toString("base64")}`
);

test("workspace payload must match both requested and current session", () => {
  assert.equal(api.isCurrentWorkspaceResponse("A", "A", "A"), true);
  for (const ids of [
    ["A", "B", "A"],
    ["A", "A", "B"],
    ["A", "B", "B"],
    [undefined, undefined, undefined],
    ["", "", ""],
  ]) {
    assert.equal(api.isCurrentWorkspaceResponse(...ids), false);
  }
});

test("challenge responses are accepted only while their requested session is current", () => {
  assert.equal(api.isCurrentSessionResponse("A", "A"), true);
  for (const ids of [
    ["A", "B"],
    ["B", "A"],
    [undefined, undefined],
    ["", ""],
  ]) {
    assert.equal(api.isCurrentSessionResponse(...ids), false);
  }
});


test("session operations require both the current session and latest request token", () => {
  assert.equal(api.isCurrentSessionOperationResponse("A", "A", 3, 3), true);
  for (const values of [
    ["A", "B", 3, 3],
    ["A", "A", 2, 3],
    ["A", "A", 4, 3],
    [undefined, undefined, 3, 3],
    ["", "", 3, 3],
  ]) {
    assert.equal(api.isCurrentSessionOperationResponse(...values), false);
  }
});


test("a deferred session-A continuation is rejected after navigation to session B", async () => {
  let currentSessionId = "A";
  let currentRequestId = 7;
  let resolveResponse;
  const response = new Promise((resolve) => {
    resolveResponse = resolve;
  });
  const applied = [];
  const continuation = response.then(() => {
    if (
      api.isCurrentSessionOperationResponse(
        "A",
        currentSessionId,
        7,
        currentRequestId,
      )
    ) {
      applied.push("stale mutation");
    }
  });

  currentSessionId = "B";
  currentRequestId += 1;
  resolveResponse();
  await continuation;
  assert.deepEqual(applied, []);
});

test("answer, hint, recap and goal handlers use independent session operation tokens", () => {
  for (const [handler, requestRef] of [
    ["submitAnswerText", "answerRequestRef"],
    ["requestHelp", "helpRequestRef"],
    ["openRecap", "recapRequestRef"],
    ["saveDailyGoal", "goalRequestRef"],
  ]) {
    assert.match(workspaceSource, new RegExp(`async function ${handler}\\(`));
    assert.match(
      workspaceSource,
      new RegExp(`const requestId = \\+\\+${requestRef}\\.current`),
    );
  }
  assert.match(workspaceSource, /isCurrentSessionOperationResponse\(/);
  assert.match(workspaceSource, /answerRequestRef\.current \+= 1/);
  assert.match(workspaceSource, /helpRequestRef\.current \+= 1/);
  assert.match(workspaceSource, /recapRequestRef\.current \+= 1/);
  assert.match(workspaceSource, /goalRequestRef\.current \+= 1/);
});
