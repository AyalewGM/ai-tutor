/** Executable render tests for InteractiveFractionAddition — esbuild bundle,
 * react-dom/server markup, ProblemVisual stubbed to record specs.
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
const bundlePath = path.join(outdir, "fraction-addition.bundle.mjs");

globalThis.__mveVisualCalls = [];

await build({
  entryPoints: [path.join(here, "InteractiveFractionAddition.tsx")],
  bundle: true,
  format: "esm",
  platform: "node",
  jsx: "automatic",
  external: ["react", "react-dom", "react/jsx-runtime"],
  plugins: [
    {
      name: "stub-problem-visual",
      setup(b) {
        b.onResolve({ filter: /ProblemVisual$/ }, () => ({
          path: "problem-visual-stub",
          namespace: "mve-stub",
        }));
        b.onLoad({ filter: /.*/, namespace: "mve-stub" }, () => ({
          contents:
            "export default function ProblemVisualStub(props) {" +
            "  globalThis.__mveVisualCalls.push(props.spec);" +
            "  return null;" +
            "}",
          loader: "js",
        }));
      },
    },
  ],
  outfile: bundlePath,
});

const { InteractiveFractionAddition } = await import(bundlePath);
const render = (props) =>
  renderToStaticMarkup(React.createElement(InteractiveFractionAddition, props));

test("mounts nothing during independent assessment", () => {
  assert.equal(render({ independentAssessment: true }), "");
});

test("guided render shows both addend bars and staged controls", () => {
  globalThis.__mveVisualCalls.length = 0;
  const html = render({
    independentAssessment: false,
    first: { numerator: 1, denominator: 4 },
    second: { numerator: 1, denominator: 2 },
  });
  assert.match(html, /1\/4 \+ 1\/2/);
  assert.match(html, /Make equal parts/);
  assert.match(html, /Combine the parts/);
  assert.match(html, /Make equal parts first, then combine/);
  assert.equal(globalThis.__mveVisualCalls.length, 2);
  assert.equal(globalThis.__mveVisualCalls[0].denominator, 4);
  assert.equal(globalThis.__mveVisualCalls[1].denominator, 2);
});

test("combine is disabled until equal parts are built", () => {
  const html = render({
    independentAssessment: false,
    first: { numerator: 1, denominator: 4 },
    second: { numerator: 1, denominator: 2 },
  });
  assert.match(html, /<button type="button" disabled=""[^>]*>Combine the parts<\/button>/);
  assert.doesNotMatch(html, /<button type="button" disabled=""[^>]*>Make equal parts<\/button>/);
});

test("invalid operands fail closed with an explanatory panel, not a crash", () => {
  const html = render({
    independentAssessment: false,
    first: { numerator: 9, denominator: 4 },
    second: { numerator: 1, denominator: 2 },
  });
  assert.match(html, /cannot be shown with the bounded bar model/);
  assert.doesNotMatch(html, /Make equal parts/);
  const lcdOverflow = render({
    independentAssessment: false,
    first: { numerator: 1, denominator: 7 },
    second: { numerator: 1, denominator: 5 },
  });
  assert.match(lcdOverflow, /cannot be shown with the bounded bar model/);
});

test("no sum bar renders before the combine stage", () => {
  globalThis.__mveVisualCalls.length = 0;
  render({
    independentAssessment: false,
    first: { numerator: 1, denominator: 4 },
    second: { numerator: 1, denominator: 2 },
  });
  assert.equal(globalThis.__mveVisualCalls.length, 2);
});
