import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import React from "react";
import ts from "typescript";

const require = createRequire(import.meta.url);
function load(path, imports = {}) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  const js = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021,
    jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true,
  } }).outputText;
  const module = { exports: {} };
  new Function("require", "module", "exports", js)(name => imports[name] ?? require(name), module, module.exports);
  return module.exports;
}


const validation = load("./coordinateValidation.ts");

test("keyboard cursor label reports coordinates and submission uses the announced point", () => {
  const values = []; let cursor = 0; const results = [];
  const { InteractiveCoordinatePlane } = load("./InteractiveCoordinatePlane.tsx", {
    "./coordinateValidation": validation,
    react: { useState: initial => {
      const i = cursor++;
      if (!(i in values)) values[i] = initial;
      return [values[i], next => { values[i] = next; }];
    } },
  });
  const render = () => {
    cursor = 0;
    return InteractiveCoordinatePlane({ expected: [2, -1], min: -2, max: 2, onResult: value => results.push(value) });
  };
  const plane = () => React.Children.toArray(render().props.children).find(node => node.type === "svg");
  const press = key => {
    let prevented = false;
    plane().props.onKeyDown({ key, preventDefault: () => { prevented = true; } });
    assert.equal(prevented, true);
  };
  assert.match(plane().props["aria-label"], /cursor at \(0, 0\)/);
  assert.doesNotMatch(plane().props["aria-label"], /\$\{/);
  assert.equal(plane().props.tabIndex, 0);
  press("ArrowRight"); press("ArrowRight"); press("ArrowRight"); press("ArrowDown");
  assert.match(plane().props["aria-label"], /cursor at \(2, -1\)/);
  press("Enter");
  assert.equal(results.at(-1).correct, true);
  assert.deepEqual(results.at(-1).actual, [2, -1]);
  press("ArrowLeft"); press(" ");
  assert.match(plane().props["aria-label"], /cursor at \(1, -1\)/);
  assert.deepEqual(results.at(-1).actual, [1, -1]);
  assert.equal(results.at(-1).correct, false);
  for (let i = 0; i < 6; i++) { press("ArrowLeft"); press("ArrowDown"); }
  assert.match(plane().props["aria-label"], /cursor at \(-2, -2\)/);
  for (let i = 0; i < 6; i++) press("ArrowUp");
  assert.match(plane().props["aria-label"], /cursor at \(-2, 2\)/);
});
