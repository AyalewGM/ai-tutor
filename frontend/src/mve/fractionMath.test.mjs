import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const source = await readFile(new URL("./fractionMath.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { normalizeFractionParts, changeShadedParts } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);

test("normalization bounds numerator and denominator", () => {
  assert.deepEqual(normalizeFractionParts(20, 20), { numerator: 12, denominator: 12 });
  assert.deepEqual(normalizeFractionParts(-3, -2), { numerator: 0, denominator: 1 });
  assert.deepEqual(normalizeFractionParts(3, 4), { numerator: 3, denominator: 4 });
});

test("invalid and non-finite inputs fail to safe deterministic defaults", () => {
  assert.deepEqual(normalizeFractionParts(NaN, Infinity), { numerator: 0, denominator: 4 });
  assert.deepEqual(normalizeFractionParts(1.5, 3.5), { numerator: 0, denominator: 4 });
  assert.deepEqual(normalizeFractionParts(Number.MAX_SAFE_INTEGER + 1, 4), { numerator: 0, denominator: 4 });
});

test("shading changes saturate at both boundaries", () => {
  assert.deepEqual(changeShadedParts({ numerator: 0, denominator: 4 }, -1), { numerator: 0, denominator: 4 });
  assert.deepEqual(changeShadedParts({ numerator: 4, denominator: 4 }, 1), { numerator: 4, denominator: 4 });
  assert.deepEqual(changeShadedParts({ numerator: 2, denominator: 4 }, 1), { numerator: 3, denominator: 4 });
  assert.deepEqual(changeShadedParts({ numerator: 2, denominator: 4 }, -1), { numerator: 1, denominator: 4 });
});

test("input objects remain unchanged and no floating point drift occurs", () => {
  const current = Object.freeze({ numerator: 2, denominator: 3 });
  assert.deepEqual(changeShadedParts(current, 1), { numerator: 3, denominator: 3 });
  assert.deepEqual(current, { numerator: 2, denominator: 3 });
});
