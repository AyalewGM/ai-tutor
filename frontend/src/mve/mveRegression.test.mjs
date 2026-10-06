import assert from "node:assert/strict";
import test from "node:test";
import fs from "node:fs";

test("MVE trust-boundary modules remain deterministic and renderer-independent", () => {
  const transformation = fs.readFileSync(new URL("./applyTransformation.ts", import.meta.url), "utf8");
  const frames = fs.readFileSync(new URL("./animationFrames.ts", import.meta.url), "utf8");
  const persistence = fs.readFileSync(new URL("./persistence.ts", import.meta.url), "utf8");

  assert.match(frames, /applyMathTransformation/);
  assert.match(frames, /objects:/);
  assert.match(persistence, /schema_version: 1/);
  assert.match(persistence, /interaction_events/);

  const forbidden = /canvas|screenshot|pixel|openai|llm/i;
  assert.doesNotMatch(transformation, forbidden);
  assert.doesNotMatch(frames, forbidden);
});

test("persistence parser fails closed instead of accepting arbitrary JSON", () => {
  const persistence = fs.readFileSync(new URL("./persistence.ts", import.meta.url), "utf8");
  assert.match(persistence, /isPersistedMathWorkV1\(value\) \? value : null/);
  assert.match(persistence, /catch \{/);
  assert.match(persistence, /return null;/);
});
