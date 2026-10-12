/** Executable integration tests for fail-closed lesson-panel isolation. */
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
const bundlePath = path.join(outdir, "learn-panel-isolation.bundle.mjs");

await build({
  entryPoints: [path.join(here, "..", "components", "LearnPanel.tsx")],
  bundle: true,
  format: "esm",
  platform: "node",
  jsx: "automatic",
  external: ["react", "react-dom", "react/jsx-runtime"],
  loader: { ".css": "empty" },
  outfile: bundlePath,
});

const { default: LearnPanel } = await import(bundlePath);
const learn = {
  summary: "Use inverse operations and keep both sides equal.",
  examples: [{
    title: "A worked answer",
    steps: ["Subtract the same value from both sides."],
    answer: "x = 4",
  }],
  key_terms: [{ term: "inverse operation", definition: "An operation that undoes another." }],
  watch_out: ["Do not change only one side."],
  guided_interactions: ["MATH.INT.ADD"],
};

const render = (props) =>
  renderToStaticMarkup(React.createElement(LearnPanel, { learn, ...props }));

test("lesson content fails closed unless guided mode is explicit", () => {
  assert.equal(render({ independentAssessment: true }), "");
  assert.equal(render({}), "");
  assert.equal(render({ independentAssessment: null }), "");
});

test("explicit guided mode retains the non-assessment lesson preview", () => {
  const html = render({ independentAssessment: false });
  assert.match(html, /Use inverse operations/);
  assert.match(html, /A worked answer/);
  assert.match(html, /Answer:/);
  assert.match(html, /Key words/);
  assert.match(html, /Watch out for/);
});

test("guided integer MVE remains isolated behind both explicit gates", () => {
  assert.doesNotMatch(
    render({ independentAssessment: false }),
    /data-mve-family="integer-addition"/,
  );
  assert.match(
    render({ independentAssessment: false, integerPracticeSeed: 17 }),
    /data-mve-family="integer-addition"/,
  );
  assert.equal(
    render({ independentAssessment: true, integerPracticeSeed: 17 }),
    "",
  );
});
