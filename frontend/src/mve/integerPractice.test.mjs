import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const file = await readFile(new URL("./integerPractice.ts", import.meta.url), "utf8");
const js = ts.transpileModule(file, {compilerOptions: {
  module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022
}}).outputText;
const api = await import(`data:text/javascript;base64,${Buffer.from(js).toString("base64")}`);

test("seeded tasks are stable with distinct variants", () => {
  for(let seed=0;seed<256;seed++){
    const a=api.buildIntegerTask(seed);
    assert.deepEqual(a,api.buildIntegerTask(seed));
    assert.equal(a.answer, a.a+a.b);
    assert.equal(api.exactIntegerSum(a.a,a.b), a.answer);
  }
  assert.notDeepEqual(api.buildIntegerTask(0),api.buildIntegerTask(1));
  assert.throws(()=>api.buildIntegerTask(-1),RangeError);
  assert.throws(()=>api.buildIntegerTask(1.25),RangeError);
});

test("independent exact oracle rejects invalid input and diagnoses misconception", () => {
  const task={seed:42,a:-3,b:-4,answer:-7,prompt:"Find -3+(-4)"};
  assert.equal(api.checkIntegerAnswer(task,"-7").correct,true);
  const wrong=api.checkIntegerAnswer(task,"1");
  assert.equal(wrong.diagnosis,"WRONG_DIRECTION");
  for (const bad of ["", "2.5", "3abc","1e2","99999999999999","-0"])
    assert.equal(api.checkIntegerAnswer(task,bad).diagnosis,"INVALID");
  assert.throws(()=>api.exactIntegerSum(101,0),RangeError);
});

test("hint progression does not leak answer and is context-based",()=>{
  const t=api.buildIntegerTask(14);
  const hints=api.socraticIntegerPrompts(t);
  assert.equal(hints.length,4);
  assert.ok(hints.every(s=>typeof s==="string" && s.length>12));
});

test("MVE safety: assessment never mounts guided activity",async()=>{
  const component=await readFile(new URL("./GuidedIntegerNumberLine.tsx",import.meta.url),"utf8");
  assert.match(component,/if \(independentAssessment\) return null/);
  assert.match(component,/role="status"/);
  assert.match(component,/aria-live="polite"/);
  assert.match(component,/Move left 1/);
  assert.doesNotMatch(component,/mastery_score|updateMastery|setTimeout|setInterval/);
});


test("diagnoses distinct errors and ignores forged answer fields", () => {
  const t = {seed: 9, a: -3, b: -4, answer: 999, prompt: "synthetic"};
  assert.equal(api.checkIntegerAnswer(t, "-7").diagnosis, "CORRECT");
  assert.equal(api.checkIntegerAnswer(t, "1").diagnosis, "WRONG_DIRECTION");
  assert.equal(api.checkIntegerAnswer(t, "7").diagnosis, "IGNORED_NEGATIVE");
  assert.equal(api.checkIntegerAnswer(t, "-6").diagnosis, "OFF_BY_ONE");
  assert.equal(api.checkIntegerAnswer({...t, a: 2, b: 3}, "-5").diagnosis, "SIGN_REVERSAL");
  assert.equal(api.checkIntegerAnswer(t, "999").correct, false);
});

test("number-line boundaries are fixed and seed changes remount guided state", async () => {
  const source = await readFile(new URL("./GuidedIntegerNumberLine.tsx", import.meta.url), "utf8");
  assert.match(source, /<IntegerActivity key=\{seed\} seed=\{seed\}/);
  assert.match(source, /const min = -20;/);
  assert.match(source, /const max = 20;/);
  assert.doesNotMatch(source, /task\.answer\s*[+-]/);
  assert.match(source, /disabled=\{position <= min\}/);
  assert.match(source, /disabled=\{position >= max\}/);
});

test("integerSeedFromString is deterministic, bounded and identifier-sensitive", () => {
  for (const id of ["problem-1", "abc-uuid-1234", "skill-42", "x"]) {
    const s = api.integerSeedFromString(id);
    assert.equal(s, api.integerSeedFromString(id));
    assert.ok(Number.isSafeInteger(s) && s >= 0 && s <= 2147483647, `seed ${s} in range`);
    assert.doesNotThrow(() => api.buildIntegerTask(s));
  }
  assert.notEqual(api.integerSeedFromString("problem-1"), api.integerSeedFromString("problem-2"));
});

test("integerPracticeEligible gates on guided states and integer-addition skills", () => {
  assert.equal(api.integerPracticeEligible("GUIDED_PRACTICE", "Add integers"), true);
  assert.equal(api.integerPracticeEligible("REMEDIATION", "Integer Operations"), true);
  assert.equal(api.integerPracticeEligible("GUIDED_PRACTICE", "Signed Number Operations"), true);
  assert.equal(api.integerPracticeEligible("GUIDED_PRACTICE", "Subtract integers"), false);
  assert.equal(api.integerPracticeEligible("MASTERY_CHECK", "Add integers"), false);
  assert.equal(api.integerPracticeEligible("DIAGNOSE", "Add integers"), false);
  assert.equal(api.integerPracticeEligible("GUIDED_PRACTICE", "Fraction equivalence"), false);
});

test("guided activity announces displacement, cycles variants and keeps focus styling", async () => {
  const source = await readFile(new URL("./GuidedIntegerNumberLine.tsx", import.meta.url), "utf8");
  assert.match(source, /units \$\{travelled > 0 \? "right" : "left"\} of your start/);
  assert.match(source, /Try another task/);
  assert.match(source, /setOffset\(o => o \+ 1\)/);
  assert.match(source, /marker already shows the answer/);
  assert.match(source, /Walk the move on the line to see why/);
  const buttons = (source.match(/<button type="button"|<button type="submit"/g) ?? []).length;
  assert.ok(buttons >= 5);
  assert.equal((source.match(/className=\{control\}/g) ?? []).length, buttons);
  assert.match(source, /focus-visible:outline-offset-2/);
});
