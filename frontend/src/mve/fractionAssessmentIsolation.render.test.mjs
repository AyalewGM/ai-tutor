/** Runtime render regression for fail-closed fraction assessment isolation. */
import assert from "node:assert/strict";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { build } from "esbuild";

const here = path.dirname(fileURLToPath(import.meta.url));
const outdir = path.join(here, "..", "..", "node_modules", ".cache", "mve-render-test");
mkdirSync(outdir, { recursive: true });

async function bundle(entry, outfile) {
  const bundlePath = path.join(outdir, outfile);
  await build({
    entryPoints: [path.join(here, entry)],
    bundle: true,
    format: "esm",
    platform: "node",
    jsx: "automatic",
    external: ["react", "react-dom", "react/jsx-runtime"],
    plugins: [{
      name: "stub-problem-visual",
      setup(b) {
        b.onResolve({ filter: /ProblemVisual$/ }, () => ({ path: "stub", namespace: "mve-stub" }));
        b.onLoad({ filter: /.*/, namespace: "mve-stub" }, () => ({
          contents: "export default function ProblemVisualStub(){return null}", loader: "js",
        }));
      },
    }],
    outfile: bundlePath,
  });
  return import(bundlePath);
}

const { InteractiveFractionBars } = await bundle("InteractiveFractionBars.tsx", "fraction-isolation-bars.mjs");
const { InteractiveFractionAddition } = await bundle("InteractiveFractionAddition.tsx", "fraction-isolation-addition.mjs");
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));

for (const [name, Component] of [
  ["fraction bars", InteractiveFractionBars],
  ["fraction addition", InteractiveFractionAddition],
]) {
  test(`${name} mounts only when guided mode is explicitly confirmed`, () => {
    assert.equal(render(Component, { independentAssessment: true }), "");
    assert.equal(render(Component, {}), "");
    assert.equal(render(Component, { independentAssessment: null }), "");
    assert.notEqual(render(Component, { independentAssessment: false }), "");
  });
}

test("fraction bar example identity changes deterministic initial state", () => {
  const halves = render(InteractiveFractionBars, {
    independentAssessment: false, denominator: 2, initialNumerator: 1,
  });
  const fourths = render(InteractiveFractionBars, {
    independentAssessment: false, denominator: 4, initialNumerator: 3,
  });
  assert.match(halves, /1 out of 2 equal parts are shaded/);
  assert.match(fourths, /3 out of 4 equal parts are shaded/);
});

test("fraction addition identity changes deterministic staged prompt", () => {
  const first = render(InteractiveFractionAddition, {
    independentAssessment: false,
    first: { numerator: 1, denominator: 4 }, second: { numerator: 1, denominator: 2 },
  });
  const second = render(InteractiveFractionAddition, {
    independentAssessment: false,
    first: { numerator: 1, denominator: 3 }, second: { numerator: 1, denominator: 4 },
  });
  assert.match(first, /1\/4 \+ 1\/2/);
  assert.match(second, /1\/3 \+ 1\/4/);
});
