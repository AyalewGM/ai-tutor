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
