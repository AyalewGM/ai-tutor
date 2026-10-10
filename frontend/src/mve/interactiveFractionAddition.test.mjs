import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./InteractiveFractionAddition.tsx", import.meta.url), "utf8");

test("guided addition fails closed in independent assessment", () => {
  assert.match(source, /if \(props\.independentAssessment\) return null/);
  assert.match(source, /return <GuidedFractionAddition/);
});

test("addition reuses the fraction bar renderer and bounded math plan", () => {
  assert.match(source, /import ProblemVisual from/);
  assert.match(source, /type: "fraction_bar"/);
  assert.match(source, /planFractionAddition\(first, second\)/);
  assert.match(source, /isValidFractionParts\(first\)/);
});

test("staged controls are native buttons with a live status region", () => {
  assert.match(source, /<button type="button"/);
  assert.match(source, /disabled=\{showCommon\}/);
  assert.match(source, /disabled=\{current !== "common"\}/);
  assert.match(source, /aria-live="polite"/);
  assert.match(source, /aria-atomic="true"/);
  assert.doesNotMatch(source, /setInterval|setTimeout|autoPlay|requestAnimationFrame/);
});

test("combine emits the validated semantic event and never scores mastery", () => {
  assert.match(source, /type: "FRACTION_ADDITION_EXPLORED"/);
  assert.match(source, /common_denominator: plan\.common_denominator/);
  assert.match(source, /sum_numerator: plan\.sum_numerator/);
  assert.doesNotMatch(source, /mastery|correct_index|gradeAnswer/);
});

test("all addition buttons carry focus-visible styling", () => {
  const buttonCount = (source.match(/<button type="button"/g) ?? []).length;
  assert.equal((source.match(/focus-visible:outline-offset-2/g) ?? []).length, buttonCount);
});
