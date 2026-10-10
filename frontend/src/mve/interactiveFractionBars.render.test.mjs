/** Executable render tests for InteractiveFractionBars — no source-text
 * assertions. The component is bundled with esbuild (ProblemVisual is
 * stubbed to record specs) and rendered with react-dom/server.
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
// Bundle inside node_modules so `react`/`react-dom` resolve from the project.
const outdir = path.join(here, "..", "..", "node_modules", ".cache", "mve-render-test");
mkdirSync(outdir, { recursive: true });
const bundlePath = path.join(outdir, "fraction-bars.bundle.mjs");

globalThis.__mveVisualCalls = [];

await build({
  entryPoints: [path.join(here, "InteractiveFractionBars.tsx")],
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

const { InteractiveFractionBars, fractionComparisonTarget } = await import(bundlePath);
const render = (props) =>
  renderToStaticMarkup(React.createElement(InteractiveFractionBars, props));

test("mounts nothing during independent assessment", () => {
  assert.equal(render({ independentAssessment: true }), "");
});

test("guided render shows bounded controls, live status, and bar spec", () => {
  globalThis.__mveVisualCalls.length = 0;
  const html = render({ independentAssessment: false, denominator: 4, initialNumerator: 2 });
  assert.match(html, /Guided fraction bar exploration/);
  assert.match(html, /role="status" aria-live="polite"/);
  assert.match(html, /2 out of 4 equal parts are shaded\. This is equivalent to 1\/2\./);
  assert.match(html, /Shade one fewer part/);
  assert.match(html, /Shade one more part/);
  assert.equal(globalThis.__mveVisualCalls.length, 1);
  assert.deepEqual(globalThis.__mveVisualCalls[0].numerator, 2);
  assert.equal(globalThis.__mveVisualCalls[0].denominator, 4);
});

test("boundary: zero-shaded fraction disables decrement and clear", () => {
  const html = render({ independentAssessment: false, denominator: 6, initialNumerator: 0 });
  const disabled = html.match(/disabled=""/g) ?? [];
  assert.equal(disabled.length, 2);
});

test("boundary: fully shaded fraction disables increment", () => {
  const html = render({ independentAssessment: false, denominator: 3, initialNumerator: 3 });
  assert.match(html, /<button type="button" disabled=""[^>]*>Shade one more part<\/button>/);
  assert.match(html, /equivalent to 1\/1/);
});

test("invalid denominator falls back to fourths deterministically", () => {
  // Non-integer denominators hit the normalize fallback; integer
  // out-of-range values clamp instead.
  const nonInteger = render({ independentAssessment: false, denominator: 2.5, initialNumerator: 1 });
  assert.match(nonInteger, /1 out of 4 equal parts are shaded/);
  const clampedLow = render({ independentAssessment: false, denominator: 0, initialNumerator: 1 });
  assert.match(clampedLow, /1 out of 1 equal parts are shaded/);
  const clampedHigh = render({ independentAssessment: false, denominator: 99, initialNumerator: 5 });
  assert.match(clampedHigh, /5 out of 12 equal parts are shaded/);
});

test("comparison section renders only for a valid compareWith target", () => {
  const withTarget = render({
    independentAssessment: false, denominator: 4, initialNumerator: 1,
    compareWith: { numerator: 3, denominator: 4 },
  });
  assert.match(withTarget, /Compare your shaded fraction with 3\/4/);
  assert.match(withTarget, /Explain comparison/);

  const invalidTarget = render({
    independentAssessment: false, denominator: 4, initialNumerator: 1,
    compareWith: { numerator: 9, denominator: 4 },
  });
  assert.doesNotMatch(invalidTarget, /Explain comparison/);

  const noTarget = render({ independentAssessment: false, denominator: 4, initialNumerator: 1 });
  assert.doesNotMatch(noTarget, /Explain comparison/);
});

test("comparison bar emits a second fraction_bar spec for the target", () => {
  globalThis.__mveVisualCalls.length = 0;
  render({
    independentAssessment: false, denominator: 4, initialNumerator: 1,
    compareWith: { numerator: 3, denominator: 4 },
  });
  assert.equal(globalThis.__mveVisualCalls.length, 2);
  assert.deepEqual(globalThis.__mveVisualCalls[1].numerator, 3);
});

test("equivalence section offers only in-bounds multipliers", () => {
  const fourths = render({ independentAssessment: false, denominator: 4, initialNumerator: 1 });
  assert.match(fourths, /Multiply by 2/);
  assert.match(fourths, /Multiply by 3/);
  assert.doesNotMatch(fourths, /Multiply by 4/);
  assert.match(fourths, /Choose a multiplier or the simplest form/);
  const sevenths = render({ independentAssessment: false, denominator: 7, initialNumerator: 1 });
  assert.doesNotMatch(sevenths, /Multiply by/);
  assert.doesNotMatch(sevenths, /Show simplest form/);
});

test("simplest-form control reflects whether the fraction is reducible", () => {
  const reducible = render({ independentAssessment: false, denominator: 4, initialNumerator: 2 });
  assert.match(reducible, /<button type="button"[^>]*aria-describedby[^>]*>Show simplest form<\/button>/);
  assert.doesNotMatch(reducible, /<button type="button" disabled=""[^>]*>Show simplest form<\/button>/);
  const lowest = render({ independentAssessment: false, denominator: 4, initialNumerator: 3 });
  assert.match(lowest, /<button type="button" disabled=""[^>]*>Show simplest form<\/button>/);
  // Reducible twelfths offer the section even when no multipliers fit.
  const twelfths = render({ independentAssessment: false, denominator: 12, initialNumerator: 6 });
  assert.match(twelfths, /Show simplest form/);
  assert.doesNotMatch(twelfths, /Multiply by/);
});

test("equivalence construction emits no bar until a multiplier is chosen", () => {
  globalThis.__mveVisualCalls.length = 0;
  render({ independentAssessment: false, denominator: 4, initialNumerator: 1 });
  assert.equal(globalThis.__mveVisualCalls.length, 1);
});

test("comparison target derives only from validated spec.math fractions", () => {
  const spec = { type: "fraction_bar", numerator: 1, denominator: 2 };
  assert.deepEqual(
    fractionComparisonTarget({ ...spec, math: [{ kind: "fraction", numerator: 3, denominator: 4 }] }),
    { numerator: 3, denominator: 4 });
  assert.deepEqual(
    fractionComparisonTarget({ ...spec, math: { kind: "fraction", numerator: 3, denominator: 4 } }),
    { numerator: 3, denominator: 4 });
  assert.equal(
    fractionComparisonTarget({ ...spec, math: [{ kind: "fraction", numerator: 1, denominator: 2 }] }), null);
  assert.equal(
    fractionComparisonTarget({ ...spec, math: [{ kind: "fraction", numerator: 9, denominator: 4 }] }), null);
  assert.equal(
    fractionComparisonTarget({ ...spec, math: [{ kind: "point", x: 1, y: 2 }] }), null);
  assert.equal(fractionComparisonTarget(spec), null);
  assert.equal(
    fractionComparisonTarget({ type: "number_line", math: [{ kind: "fraction", numerator: 3, denominator: 4 }] }), null);
  assert.equal(fractionComparisonTarget(null), null);
});
