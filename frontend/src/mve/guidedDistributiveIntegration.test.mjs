import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
const guided = await readFile(new URL("./GuidedDistributivePractice.tsx", import.meta.url), "utf8");
const player = await readFile(new URL("./PedagogicalAnimation.tsx", import.meta.url), "utf8");
const lesson = await readFile(new URL("./distributiveLesson.ts", import.meta.url), "utf8");

// Transpile real React components in memory, without adding a new test framework
// or touching the browser application. Stub only the SVG renderer.
function loadTypeScript(source, imports = {}) {
  const js = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const resolve = (name) => Object.hasOwn(imports, name) ? imports[name] : require(name);
  new Function("require", "module", "exports", js)(resolve, module, module.exports);
  return module.exports;
}

const lessonModule = loadTypeScript(lesson);
const playerModule = loadTypeScript(player);
const guidedModule = loadTypeScript(guided, {
  "../components/ProblemVisual": {
    default: ({ spec }) => React.createElement("div", {
      role: "img", "aria-label": spec.aria_label,
    }),
  },
  "./PedagogicalAnimation": playerModule,
  "./distributiveLesson": lessonModule,
});

test("workspace only mounts guided explanation in guided or remediation states", () => {
  assert.match(workspace, /workspace\.state === "GUIDED_PRACTICE" \|\| workspace\.state === "REMEDIATION"/);
  assert.match(workspace, /<GuidedDistributivePractice\s/);
  assert.match(workspace, /independentAssessment=\{workspace\.state !== "GUIDED_PRACTICE" && workspace\.state !== "REMEDIATION"\}/);
});

test("independent assessment renders no guided explanation, worked answer, or controls", () => {
  const { GuidedDistributivePractice } = guidedModule;
  const html = renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
    independentAssessment: true, factor: 5, constant: 3,
  }));
  assert.equal(html, "");
  // The fail-closed guard must run before lesson construction, even on invalid data.
  assert.equal(renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
    independentAssessment: true, factor: -1, constant: 3,
  })), "");
});

test("guided state renders the real accessible player and separate worked example", () => {
  const { GuidedDistributivePractice } = guidedModule;
  const html = renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
    independentAssessment: false, factor: 5, constant: 3,
  }));
  assert.match(html, /Guided distributive property lesson/);
  assert.match(html, /5\(x \+ 3\)/);
  assert.match(html, /Worked example, separate from your current question/);
  assert.match(html, /aria-label="Animation playback controls"/);
  assert.match(html, /aria-label="Play animation"/);
  assert.match(html, /<button type="button"/);
  assert.match(html, /Previous step/);
  assert.match(html, /Next step/);
  assert.match(html, /Replay/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /Coefficient of x/);
  assert.match(html, /Constant term/);
});

test("shared player supports reduced-motion, keyboard-native controls, and timer cleanup", () => {
  assert.match(guided, /<PedagogicalAnimation/);
  assert.match(player, /prefers-reduced-motion: reduce/);
  assert.match(player, /if \(prefersReducedMotion\) setPlaying\(false\)/);
  assert.match(player, /clearTimeout\(timer\)/);
  assert.match(player, /onClick=/);
  assert.match(player, /aria-label="Animation playback controls"/);
});

test("guided checks use deterministic misconception classification", () => {
  assert.match(guided, /checkDistributiveCoefficients\(lesson/);
  assert.match(guided, /MISSED_SECOND_TERM/);
  assert.match(guided, /COEFFICIENT_ERROR/);
  assert.equal(lessonModule.checkDistributiveCoefficients(
    lessonModule.buildDistributiveLesson(5, 3), 5, 3,
  ).misconception, "MISSED_SECOND_TERM");
});
