import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const source = await readFile(
  new URL("../workspaceSessionGuard.ts", import.meta.url),
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
