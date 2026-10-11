import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./InteractiveFractionBars.tsx", import.meta.url), "utf8");

test("guided fraction exploration fails closed unless assessment mode is explicitly false", () => {
  assert.match(source, /if \(props\.independentAssessment !== false\) return null/);
  assert.match(source, /return <GuidedFractionBars key=\{lifecycleKey\}/);
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
  for (const helper of ["normalizeFractionParts", "changeShadedParts", "describeFraction"]) {
    assert.match(source, new RegExp(`import \\{[^}]*\\b${helper}\\b[^}]*\\} from "\\.\\/fractionMath"`));
  }
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
  assert.match(source, /if \(props\.independentAssessment !== false\) return null/);
});

test("all fraction buttons share a labeled control group and status description", () => {
  assert.match(source, /role="group"/);
  assert.match(source, /aria-label="Fraction exploration controls"/);
  assert.equal((source.match(/aria-describedby=\{statusId\}/g) ?? []).length, 3);
  const buttonCount = (source.match(/<button type="button"/g) ?? []).length;
  assert.equal((source.match(/focus-visible:outline-offset-2/g) ?? []).length, buttonCount);
  assert.match(source, /id=\{statusId\} role="status"/);
});

test("guided comparison uses validated target and exact semantic relation", () => {
  assert.match(source, /isValidFractionParts\(compareWith\)/);
  assert.match(source, /compareFractions\(left, target\)/);
  assert.match(source, /type: "FRACTION_COMPARED"/);
  assert.match(source, /describeFractionComparison\(/);
  assert.match(source, /if \(props\.independentAssessment !== false\) return null/);
});

test("example and comparison identity reset all local exploration state", () => {
  assert.match(source, /const lifecycleKey = `\$\{initial\.numerator\}\/\$\{initial\.denominator\}\|/);
  assert.match(source, /target \? `\$\{target\.numerator\}\/\$\{target\.denominator\}` : "none"/);
  assert.match(source, /<GuidedFractionBars key=\{lifecycleKey\}/);
  assert.doesNotMatch(source, /previousDenominator|lastTargetKey|setPreviousDenominator|setLastTargetKey/);
  assert.match(source, /id=\{comparisonStatusId\} role="status"/);
});

test("equivalence construction uses validated scaling and resets with state", () => {
  assert.match(source, /validScaleFactors\(currentParts\)/);
  assert.match(source, /scaleFraction\(currentParts, factor\)/);
  assert.match(source, /type: "FRACTION_EQUIVALENCE_EXPLORED"/);
  assert.match(source, /setEquivalence\(null\)/);
  assert.match(source, /id=\{equivalenceStatusId\} role="status"/);
  assert.match(source, /if \(props\.independentAssessment !== false\) return null/);
});

test("simplification control is fail-closed and emits a semantic event", () => {
  assert.match(source, /describeSimplification\(currentParts\)/);
  assert.match(source, /simplifyFraction\(currentParts\)/);
  assert.match(source, /type: "FRACTION_SIMPLIFIED"/);
  assert.match(source, /disabled=\{simplification === null\}/);
});
