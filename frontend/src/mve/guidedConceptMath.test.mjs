import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  classifyEquivalentAnswer,
  classifyRatioAnswer,
  equivalenceModel,
  ratioPartitionModel,
} from "./guidedConceptMath.mjs";

test("equivalence is exact and distinguishes two misconceptions", () => {
  const model = equivalenceModel(2, 3, 3);
  assert.deepEqual(model, {
    numerator: 2, denominator: 3, scale: 3,
    expandedNumerator: 6, expandedDenominator: 9,
  });
  assert.deepEqual(classifyEquivalentAnswer(model, "6"), {
    correct: true, misconception: null,
  });
  assert.equal(classifyEquivalentAnswer(model, "2").misconception, "NUMERATOR_NOT_SCALED");
  assert.equal(classifyEquivalentAnswer(model, "5").misconception, "ADDITIVE_SCALING");
  for (const invalid of ["6.0", "6/9", "Infinity", "-6", "6e0", ""]) {
    assert.equal(classifyEquivalentAnswer(model, invalid).correct, false);
  }
});

test("ratio partition computes the unit before shares", () => {
  const model = ratioPartitionModel(2, 3, 4);
  assert.equal(model.totalParts, 5);
  assert.equal(model.total, 20);
  assert.equal(model.firstShare, 8);
  assert.equal(classifyRatioAnswer(model, "8").correct, true);
  assert.equal(classifyRatioAnswer(model, "20").misconception, "WHOLE_INSTEAD_OF_SHARE");
  assert.equal(classifyRatioAnswer(model, "10").misconception, "WRONG_PART_COUNT");
});

test("all supported parameter combinations preserve mathematical invariants", () => {
  for (let denominator = 2; denominator <= 6; denominator++) {
    for (let numerator = 1; numerator < denominator; numerator++) {
      for (let scale = 2; scale <= 3; scale++) {
        if (denominator * scale > 12) continue;
        const model = equivalenceModel(numerator, denominator, scale);
        assert.equal(
          model.numerator * model.expandedDenominator,
          model.denominator * model.expandedNumerator,
        );
      }
    }
  }
  for (let first = 1; first <= 5; first++) {
    for (let second = 1; second <= 5; second++) {
      for (let unit = 1; unit <= 20; unit++) {
        const model = ratioPartitionModel(first, second, unit);
        assert.equal(model.firstShare + model.secondParts * unit, model.total);
        assert.equal(model.total / model.totalParts, unit);
      }
    }
  }
});

test("invalid parameters fail closed", () => {
  for (const args of [[0, 3, 2], [2, 2, 2], [2, 3, 5], [2, 6, 3], [2.5, 3, 2]]) {
    assert.throws(() => equivalenceModel(...args), RangeError);
  }
  for (const args of [[0, 2, 4], [2, 0, 4], [2, 3, 0], [2, 3, 21], [2, 3, 2.5]]) {
    assert.throws(() => ratioPartitionModel(...args), RangeError);
  }
});

test("interactive lessons remain unmounted until a trusted capability and pedagogy acceptance", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
  assert.match(ui, /if \(props\.independentAssessment !== false\) return null/);
  assert.match(ui, /role="status" aria-live="polite"/);
  assert.match(ui, /type="submit"/);
  assert.match(ui, /Lock prediction/);
  assert.match(ui, /Check explanation/);
  assert.match(ui, /Repair and verify/);
  assert.match(ui, /Transfer without/);
  assert.match(ui, /ProblemVisual/);
  // No accepted server-owned fraction-equivalence or ratio-partition
  // capability exists. Build flags and mutable display-name regexes are
  // explicitly NOT authority to mount the guided component.
  assert.doesNotMatch(workspace, /VITE_ENABLE_CONCEPT_GUIDED_PILOT/);
  assert.doesNotMatch(workspace, /conceptGuidedPilotEnabled/);
  assert.doesNotMatch(workspace, /<GuidedConceptPractice\b/);
  assert.doesNotMatch(ui, /updateMastery|setMastery|recordAssessment|fetch\(|post\(/);
});

test("concept lessons implement real scaffold fading and transfer surfaces", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  assert.match(ui, /!explanationVerified && <ProblemVisual/);
  assert.match(ui, /!explanationVerified && <div aria-label="Five equal ratio parts"/);
  assert.match(ui, /Fraction misconception repair/);
  assert.match(ui, /Ratio misconception repair/);
  assert.match(ui, /Fraction transfer/);
  assert.match(ui, /Ratio transfer/);
  assert.match(ui, /worked answer|stays unworked|without counters|without the completed bar/i);
});

test("repairs do not reveal expected ratio shares and completed fraction model waits for numeric evidence", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(ui, /Enter both shares as 6,18|Enter both shares as 12,18|Enter both shares as 12,16/);
  assert.match(ui, /Ratio repair common unit/);
  assert.match(ui, /numericVerified && !explanationVerified && <ProblemVisual/);
});

test("concept predictions are evaluated with targeted reflection", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  assert.match(ui, /Your prediction matches the mathematical relationship/);
  assert.match(ui, /same whole is repartitioned/);
  assert.match(ui, /2 of 5 equal parts is less than one half/);
  assert.match(ui, /predictionFeedback/);
});
