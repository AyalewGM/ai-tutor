import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./InteractiveFractionBars.tsx", import.meta.url), "utf8");

test("guided fraction exploration fails closed in independent assessment", () => {
  assert.match(source, /if \(props\.independentAssessment\) return null/);
  assert.match(source, /return <GuidedFractionBars/);
});

test("fraction exploration reuses the registered fraction bar renderer", () => {
  assert.match(source, /import ProblemVisual from/);
  assert.match(source, /type: "fraction_bar"/);
  assert.match(source, /aria_label:/);
});

test("native keyboard controls and live status avoid motion dependence", () => {
  assert.match(source, /<button type="button"/);
  assert.match(source, /disabled=\{current === 0\}/);
  assert.match(source, /disabled=\{current === d\}/);
  assert.match(source, /aria-live="polite"/);
  assert.doesNotMatch(source, /setInterval|setTimeout|autoPlay/);
});

test("deterministic bounded fraction state and no answer scoring", () => {
  assert.match(source, /import \{ normalizeFractionParts \} from "\.\/fractionMath"/);
  assert.doesNotMatch(source, /mastery|correct_index|gradeAnswer/);
});


test("keyboard focus visibility and no duplicate events at bounds", () => {
  assert.match(source, /focus-visible:outline/);
  assert.match(source, /if \(value\.numerator === current\) return/);
  assert.match(source, /changeShadedParts\(/);
  assert.match(source, /onMathEvent\?\.\(\{ schema_version: 1, type: "FRACTION_SHADING_CHANGED"/);
  assert.doesNotMatch(source, /animate-|transition-|motion\.|requestAnimationFrame/);
});

test("semantic equivalent-fraction explanation remains guided and screen-reader readable", () => {
  assert.match(source, /describeFraction\(\{ numerator: current, denominator: d \}\)/);
  assert.match(source, /aria-atomic="true"/);
  assert.match(source, /if \(props\.independentAssessment\) return null/);
});
