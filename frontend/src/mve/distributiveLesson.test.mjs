import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

// The frontend intentionally uses node:test, not Vitest. Transpile the
// TypeScript module in memory so these are executable behavioral tests.
const source = await readFile(new URL("./distributiveLesson.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { buildDistributiveLesson, checkDistributiveCoefficients } =
  await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);

test("distributive lesson uses existing semantic animation contract", () => {
  const lesson = buildDistributiveLesson(3, 4);
  assert.equal(lesson.original, "3(x + 4)");
  assert.equal(lesson.expanded, "3 × x + 3 × (4)");
  assert.equal(lesson.simplified, "3x + 12");
  assert.equal(lesson.animation.schema_version, 1);
  assert.equal(lesson.animation.steps.length, 4);
  assert.equal(lesson.animation.reduced_motion, "step_without_motion");
  assert.equal(lesson.areaModel.a, 3);
  assert.equal(lesson.areaModel.b, 4);
  assert.equal(lesson.algebraTiles.type, "algebra_tiles");
});

test("distributive validation classifies errors deterministically", () => {
  const lesson = buildDistributiveLesson(5, 3);
  assert.equal(checkDistributiveCoefficients(lesson, 5, 3).misconception, "MISSED_SECOND_TERM");
  assert.equal(checkDistributiveCoefficients(lesson, 5, 15).correct, true);
  assert.equal(checkDistributiveCoefficients(lesson, 4, 15).misconception, "COEFFICIENT_ERROR");
  assert.equal(checkDistributiveCoefficients(lesson, 5, 12).misconception, "CONSTANT_ERROR");
});

test("signed distribution preserves every term and classifies a dropped outside negative", () => {
  const lesson = buildDistributiveLesson(-2, -4);
  assert.equal(lesson.original, "-2(x − 4)");
  assert.equal(lesson.simplified, "-2x + 8");
  assert.deepEqual(lesson.algebraTiles.groups.map((group) => group.terms[0].coefficient), [-2, 8]);
  assert.equal(checkDistributiveCoefficients(lesson, -2, 8).correct, true);
  assert.equal(checkDistributiveCoefficients(lesson, 2, -8).misconception, "DROPPED_NEGATIVE");
  assert.equal(checkDistributiveCoefficients(lesson, -2, -4).misconception, "MISSED_SECOND_TERM");
});

test("all bounded signed lessons have exact products and deterministic safe tile models", () => {
  for (let factor = -12; factor <= 12; factor += 1) {
    if (factor === 0) continue;
    for (let constant = -12; constant <= 12; constant += 1) {
      const lesson = buildDistributiveLesson(factor, constant);
      assert.equal(checkDistributiveCoefficients(lesson, factor, factor * constant).correct, true);
      assert.equal(lesson.algebraTiles.groups[0].terms[0].coefficient, factor);
      assert.equal(lesson.algebraTiles.groups[1].terms[0].coefficient, factor * constant);
      assert.equal(lesson.animation.reduced_motion, "step_without_motion");
    }
  }
});

test("distributive builder rejects invalid input", () => {
  assert.throws(() => buildDistributiveLesson(0, 4));
  assert.throws(() => buildDistributiveLesson(-13, 4));
  assert.throws(() => buildDistributiveLesson(3, 13));
  assert.throws(() => buildDistributiveLesson(3, 4, "<script>"));
});
