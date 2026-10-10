/** Executable render tests for GuidedIntegerNumberLine — esbuild bundle +
 * react-dom/server markup (the component renders its own SVG; no stubs).
 */
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
const bundlePath = path.join(outdir, "integer-number-line.bundle.mjs");

await build({
  entryPoints: [path.join(here, "GuidedIntegerNumberLine.tsx")],
  bundle: true,
  format: "esm",
  platform: "node",
  jsx: "automatic",
  external: ["react", "react-dom", "react/jsx-runtime"],
  outfile: bundlePath,
});

const { GuidedIntegerNumberLine } = await import(bundlePath);
const render = (props) =>
  renderToStaticMarkup(React.createElement(GuidedIntegerNumberLine, props));

test("mounts nothing during independent assessment", () => {
  assert.equal(render({ seed: 17, independentAssessment: true }), "");
});

test("guided render shows the seeded task, controls and live status", () => {
  const html = render({ seed: 17, independentAssessment: false });
  assert.match(html, /Explore adding signed integers/);
  assert.match(html, /Move left 1/);
  assert.match(html, /Move right 1/);
  assert.match(html, /Ask a guiding question/);
  assert.match(html, /Try another task/);
  assert.match(html, /Check my reasoning/);
  assert.match(html, /role="status" aria-live="polite"/);
  assert.match(html, /You are still at the start/);
});

test("seeded task text is deterministic per seed and differs across seeds", () => {
  const a1 = render({ seed: 1, independentAssessment: false });
  const a1again = render({ seed: 1, independentAssessment: false });
  const a2 = render({ seed: 2, independentAssessment: false });
  const prompt1 = a1.match(/Find (-?\d+) \+ \((-?\d+)\)\./);
  assert.ok(prompt1);
  assert.ok(a1again.includes(prompt1[0]));
  assert.notEqual(a2.match(/Find (-?\d+) \+ \((-?\d+)\)\./)?.[0], prompt1[0]);
});

test("markers start on the task's starting integer without revealing the answer", () => {
  const html = render({ seed: 17, independentAssessment: false });
  const prompt = html.match(/Find (-?\d+) \+ \((-?\d+)\)\./);
  assert.ok(prompt);
  const a = Number(prompt[1]);
  assert.match(html, new RegExp(`starting at ${a}, current position ${a}`));
  // The blue start marker and the orange position marker coincide at the start.
  assert.equal((html.match(/<circle/g) ?? []).length, 2);
  assert.doesNotMatch(html, /answer =|the answer is/i);
});
