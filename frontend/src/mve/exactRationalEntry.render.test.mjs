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
  assert.doesNotMatch(html, /aria-label="x"/);
  assert.doesNotMatch(html, /aria-label="y"/);
  assert.match(html, /Type the variable shown in the question/);
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

test("restricted keypad never suggests unsupported syntax or guesses a variable", () => {
  const expectedKeys = [
    "7", "8", "9", "4", "5", "6", "1", "2", "3",
    "0", "minus sign", "fraction slash", "backspace",
  ];
  for (const answerKind of ["RATIONAL", "VARIABLE_VALUE"]) {
    const html = render(answerKind);
    const labels = [...html.matchAll(/<button\\b[^>]*aria-label="([^"]+)"/g)]
      .map((match) => match[1]);
    assert.deepEqual(labels, expectedKeys);
    assert.match(html, /aria-label="Exact rational keypad"/);
    assert.doesNotMatch(html, /aria-label="(?:x|y|\\.|exponent|multiply|divide|\\+|=)"/);
  }
});

test("numeric, sign, fraction and backspace shortcuts dispatch the displayed token only", () => {
  const pressed = [];
  // Inspect the stateless forwardRef and keypad React element callbacks;
  // browser-level keyboard/focus checks remain independent Muse QA.
  const view = ExactRationalEntry.render({
    answerKind: "VARIABLE_VALUE", value: "",
    onValueChange: () => {}, onKey: (token) => pressed.push(token),
    disabled: false,
  }, null);
  const keypad = React.Children.toArray(view.props.children)
    .find((element) => element.type?.name === "ExactRationalKeypad");
  assert.ok(keypad);
  const keypadTree = keypad.type(keypad.props);
  const buttons = React.Children.toArray(keypadTree.props.children).flatMap(
    (row) => React.Children.toArray(row.props.children),
  );
  assert.deepEqual(buttons.map((button) => button.props.type), Array(13).fill("button"));
  for (const label of ["7", "minus sign", "fraction slash", "backspace"]) {
    const button = buttons.find((entry) => entry.props["aria-label"] === label);
    assert.ok(button, label);
    assert.equal(button.props.disabled, false);
    button.props.onClick();
  }
  assert.deepEqual(pressed, ["7", "-", "/", "\\b"]);
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
