/** Render/contract regressions for the learner's exact-rational answer input. */
import assert from "node:assert/strict";
import { mkdirSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { build } from "esbuild";

const here = path.dirname(fileURLToPath(import.meta.url));
const outdir = path.join(here, "..", "..", "node_modules", ".cache", "mve-render-test");
mkdirSync(outdir, { recursive: true });
const outfile = path.join(outdir, "exact-rational-entry.bundle.mjs");

await build({
  entryPoints: [path.join(here, "..", "components", "ExactRationalEntry.tsx")],
  bundle: true,
  format: "esm",
  platform: "node",
  // Node defaults to the CommonJS lucide-react entry, which dynamically
  // requires React from an ESM bundle. Prefer its ESM entry for SSR tests.
  mainFields: ["module", "main"],
  jsx: "automatic",
  external: ["react", "react-dom", "react/jsx-runtime"],
  loader: { ".css": "empty" },
  outfile,
});

const { default: ExactRationalEntry } = await import(outfile);
const render = (answerKind, extra = {}) =>
  renderToStaticMarkup(React.createElement(ExactRationalEntry, {
    answerKind,
    value: "",
    onValueChange: () => {},
    onKey: () => {},
    ...extra,
  }));

test("variable-value mode supports accessible exact signed fractions without supplying an oracle", () => {
  const html = render("VARIABLE_VALUE", { value: "x=-5/6" });
  assert.match(html, /aria-label="Exact variable value"/);
  assert.match(html, /aria-describedby="exact-rational-answer-format"/);
  assert.match(html, /id="exact-rational-answer-format"/);
  assert.match(html, /value="x=-5\/6"/);
  assert.match(html, /aria-label="fraction slash"/);
  assert.match(html, /aria-label="x"/);
  assert.match(html, /format: x=numerator\/denominator/);
  assert.doesNotMatch(html, /correct answer|worked solution/i);
});

test("bare rational mode provides an integer-or-fraction path without misleading variable binding", () => {
  const html = render("RATIONAL", { value: "-5/6" });
  assert.match(html, /aria-label="Exact rational number"/);
  assert.match(html, /value="-5\/6"/);
  assert.match(html, /Do not round to a decimal/);
  assert.doesNotMatch(html, /aria-label="x"/);
  assert.doesNotMatch(html, /aria-label="y"/);
  assert.match(html, /aria-label="fraction slash"/);
});

test("a disabled answer field also disables on-screen keys", () => {
  const html = render("VARIABLE_VALUE", { disabled: true });
  assert.match(html, /<input[^>]+disabled=""/);
  assert.match(html, /<button[^>]+disabled=""/);
  assert.match(html, /maxlength="64"/i);
});

test("Workspace routes only exact rational kinds through new field and preserves server submit", async () => {
  const source = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
  assert.match(source, /problemKind === "FRACTION"/);
  assert.match(source, /problemKind === "RATIONAL" \|\| problemKind === "VARIABLE_VALUE"/);
  assert.match(source, /<ExactRationalEntry\b/);
  assert.match(source, /ref=\{answerRef\}/);
  assert.match(source, /onKey=\{insertToken\}/);
  assert.match(source, /disabled=\{!hasAction\("SUBMIT_ANSWER"\) \|\| !currentProblem\}/);
  assert.match(source, /\/adaptive-tutor\/sessions\/\$\{requestedSessionId\}\/respond/);
  assert.match(source, /assistance_level: 0/);
});
