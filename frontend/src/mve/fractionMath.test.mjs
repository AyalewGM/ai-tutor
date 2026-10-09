import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const source = await readFile(new URL("./fractionMath.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { normalizeFractionParts, changeShadedParts, simplifyFraction, describeFraction } = await import(
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

test("equivalent fractions simplify exactly and preserve original shading", () => {
  assert.deepEqual(simplifyFraction({ numerator: 2, denominator: 4 }), { numerator: 1, denominator: 2 });
  assert.deepEqual(simplifyFraction({ numerator: 0, denominator: 12 }), { numerator: 0, denominator: 1 });
  assert.deepEqual(simplifyFraction({ numerator: 12, denominator: 12 }), { numerator: 1, denominator: 1 });
  assert.deepEqual(simplifyFraction({ numerator: 3, denominator: 4 }), { numerator: 3, denominator: 4 });
});

test("accessible explanations are deterministic and do not grade mastery", () => {
  assert.equal(describeFraction({ numerator: 2, denominator: 4 }),
    "2 out of 4 equal parts are shaded. This is equivalent to 1/2.");
  assert.equal(describeFraction({ numerator: 3, denominator: 4 }),
    "3 out of 4 equal parts are shaded.");
});
