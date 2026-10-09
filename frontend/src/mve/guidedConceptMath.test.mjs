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

test("interactive teaching is gated and does not award mastery", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
  assert.match(ui, /if \(props\.independentAssessment\) return null/);
  assert.match(ui, /role="status" aria-live="polite"/);
  assert.match(ui, /type="submit"/);
  assert.match(ui, /Show another representation/);
  assert.match(ui, /ProblemVisual/);
  assert.match(workspace, /VITE_ENABLE_CONCEPT_GUIDED_PILOT === "true"/);
  assert.match(workspace, /conceptGuidedPilotEnabled &&/);
  assert.match(workspace, /workspace\.state === "GUIDED_PRACTICE"/);
  assert.match(workspace, /workspace\.state === "REMEDIATION"/);
  assert.match(workspace, /concept="fraction-equivalence"/);
  assert.match(workspace, /concept="ratio-partition"/);
  assert.doesNotMatch(ui, /updateMastery|setMastery|recordAssessment|fetch\(|post\(/);
});
