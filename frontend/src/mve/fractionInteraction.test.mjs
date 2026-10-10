import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const source = await readFile(new URL("./interactions.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { isMathInteractionEvent } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);
const fraction = (numerator, denominator) => ({ numerator, denominator });
const event = (left, right, relation) => ({
  schema_version: 1, type: "FRACTION_COMPARED", left, right, relation,
});

test("semantic comparison accepts exact equivalence across denominators", () => {
  assert.equal(isMathInteractionEvent(event(fraction(1, 2), fraction(2, 4), "EQUAL_TO")), true);
  assert.equal(isMathInteractionEvent(event(fraction(1, 4), fraction(1, 2), "LESS_THAN")), true);
  assert.equal(isMathInteractionEvent(event(fraction(3, 4), fraction(1, 2), "GREATER_THAN")), true);
});

test("semantic comparison rejects forged relations and invalid bounds", () => {
  assert.equal(isMathInteractionEvent(event(fraction(1, 2), fraction(2, 4), "LESS_THAN")), false);
  assert.equal(isMathInteractionEvent(event(fraction(1, 0), fraction(1, 2), "GREATER_THAN")), false);
  assert.equal(isMathInteractionEvent(event(fraction(2, 1), fraction(1, 2), "GREATER_THAN")), false);
  assert.equal(isMathInteractionEvent(event(fraction(NaN, 2), fraction(1, 2), "EQUAL_TO")), false);
  assert.equal(isMathInteractionEvent(event(fraction(1, 2), fraction(1, 2), "CORRECT")), false);
});
