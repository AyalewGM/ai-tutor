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
  assert.equal(lesson.expanded, "3 × x + 3 × 4");
  assert.equal(lesson.simplified, "3x + 12");
  assert.equal(lesson.animation.schema_version, 1);
  assert.equal(lesson.animation.steps.length, 4);
  assert.equal(lesson.animation.reduced_motion, "step_without_motion");
  assert.equal(lesson.areaModel.a, 3);
  assert.equal(lesson.areaModel.b, 4);
});

test("distributive validation classifies errors deterministically", () => {
  const lesson = buildDistributiveLesson(5, 3);
  assert.equal(checkDistributiveCoefficients(lesson, 5, 3).misconception, "MISSED_SECOND_TERM");
  assert.equal(checkDistributiveCoefficients(lesson, 5, 15).correct, true);
  assert.equal(checkDistributiveCoefficients(lesson, 4, 15).misconception, "COEFFICIENT_ERROR");
  assert.equal(checkDistributiveCoefficients(lesson, 5, 12).misconception, "CONSTANT_ERROR");
});

test("distributive builder rejects invalid input", () => {
  assert.throws(() => buildDistributiveLesson(0, 4));
  assert.throws(() => buildDistributiveLesson(3, -4));
  assert.throws(() => buildDistributiveLesson(3, 4, "<script>"));
});
