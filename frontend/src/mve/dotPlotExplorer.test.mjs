import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
function load(path, imports = {}) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  const js = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021,
    jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true,
  } }).outputText;
  const module = { exports: {} };
  new Function("require", "module", "exports", js)(name => imports[name] ?? require(name), module, module.exports);
  return module.exports;
}
const rational = load('./linearExplorer.ts');
const math = load('./dotPlotExplorer.ts', { './linearExplorer': rational });
const events = load('./interactions.ts');
const registry = load('./rendererRegistry.ts');
const visual = load('../components/ProblemVisual.tsx', { '../mve/rendererRegistry': registry });
const imports = { './dotPlotExplorer': math, './linearExplorer': rational, '../components/ProblemVisual': visual };
const { InteractiveDotPlotExplorer: Component } = load('./InteractiveDotPlotExplorer.tsx', imports);

test('exact known statistics: unsorted, repeated, even, odd, singleton and all-zero data', () => {
  for (const [values, mean, median, range] of [
    [[9,2,4,3], '9/2', '7/2', 7], [[2,3,3,4,5], '17/5', '3', 3],
    [[0], '0', '0', 0], [[12,12,12,12,12,12], '12', '12', 0],
    [[0,0,0], '0', '0', 0], [[1,1,1,9], '3', '1', 8],
  ]) {
    const snapshot = [...values];
    const model = math.datasetModel(values);
    assert.equal(rational.formatRational(model.mean), mean);
    assert.equal(rational.formatRational(model.median), median);
    assert.equal(model.range, range);
    assert.equal(model.frequencies.reduce((n,row) => n + row.count, 0), values.length);
    assert.deepEqual(values, snapshot);
  }
});
test('all bounded two-observation means and medians agree; extreme movement affects measures', () => {
  for (let a=0; a<=12; a++) for (let b=0; b<=12; b++) {
    const m = math.datasetModel([a,b]);
    assert.deepEqual(m.mean, m.median);
    assert.equal(m.mean.numerator * 2, (a+b) * m.mean.denominator);
    assert.equal(m.range, Math.abs(a-b));
  }
  const base = [2,3,3,4,5];
  const changed = math.replaceObservation(base,4,12);
  assert.deepEqual(base,[2,3,3,4,5]);
  assert.deepEqual(math.datasetModel(changed).median, math.datasetModel(base).median);
  assert.deepEqual(math.datasetModel(changed).mean, { numerator:24, denominator:5 });
});
test('invalid datasets, indexes and private event fields fail closed', () => {
  for (const values of [[], Array(2), [NaN], [0.5], [-1], [13], Array(7).fill(1), ['2']]) {
    assert.equal(math.isExplorerDataset(values), false);
    assert.throws(() => math.datasetModel(values));
    assert.equal(events.isMathInteractionEvent({schema_version:1,type:'EXPLORER_DATASET_CHANGED',values}),false);
  }
  assert.throws(() => math.replaceObservation([2],1,3));
  assert.throws(() => math.replaceObservation([2],0,13));
  const event = {schema_version:1,type:'EXPLORER_DATASET_CHANGED',values:[2,3,3]};
  assert.equal(events.isMathInteractionEvent(event),true);
  assert.equal(events.isMathInteractionEvent({...event,student_id:'test'}),false);
});
test('practice checks exact fractions and rejects ambiguous inputs', () => {
  for (const [i,answer] of ['3','7/2','3','0'].entries()) assert.equal(math.checkDatasetAnswer(i,answer).correct,true);
  assert.equal(math.checkDatasetAnswer(1,'14/4').correct,true);
  for (const answer of ['', '3.5','7/0','3','2e0','-1']) assert.equal(math.checkDatasetAnswer(1,answer).correct,false);
  assert.throws(() => math.checkDatasetAnswer(10,'1'));
});
test('real dot renderer, frequency table and labeled controls; assessment renders nothing', () => {
  const html=renderToStaticMarkup(React.createElement(Component,{independentAssessment:false}));
  for (const term of ['<svg','Frequency table','scope="col"','aria-live="polite"','focus-visible:outline','17/5','Observe','Manipulate','Explain','Practice']) assert.ok(html.includes(term),term);
  for (const [,id] of html.matchAll(/<label[^>]*for="([^"]+)"/g)) assert.ok(html.includes(`id="${id}"`));
  for (const mode of [true,undefined,null]) assert.equal(renderToStaticMarkup(React.createElement(Component,{independentAssessment:mode})), '');
  assert.equal(math.showDotPlotExploration('GUIDED_PRACTICE','Center and Spread'),true);
  for (const mode of ['INDEPENDENT_PRACTICE','ASSESSMENT','MASTERY_CHECK','']) assert.equal(math.showDotPlotExploration(mode,'Center and Spread'),false);
});
test('actual handlers move data, enforce observation counts, reset and emit only math', () => {
  let state=[], cursor=0; const emitted=[];
  const hooked=load('./InteractiveDotPlotExplorer.tsx',{...imports,react:{
    useId:()=> 'data', useState:initial=>{const i=cursor++; if(!(i in state)) state[i]=initial; return [state[i],value=>{state[i]=value;}];},
  }});
  function render(){cursor=0;const wrapper=hooked.InteractiveDotPlotExplorer({independentAssessment:false,onMathEvent:e=>emitted.push(e)});return wrapper.type(wrapper.props);}
  function nodes(node){return !node||typeof node!=='object'?[]:[node,...React.Children.toArray(node.props?.children).flatMap(nodes)];}
  const click=name=>nodes(render()).find(n=>n.type==='button'&&n.props.children===name).props.onClick();
  nodes(render()).find(n=>n.props.id==='data-value').props.onChange({target:{value:'12'}});
  assert.deepEqual(emitted.at(-1).values,[2,3,3,4,12]);
  assert.equal(events.isMathInteractionEvent(emitted.at(-1)),true);
  click('Add another observation at this value');
  assert.equal(nodes(render()).find(n=>n.type==='button'&&n.props.children==='Add another observation at this value').props.disabled,true);
  for(let i=0;i<5;i++) click('Remove selected observation');
  assert.equal(nodes(render()).find(n=>n.type==='button'&&n.props.children==='Remove selected observation').props.disabled,true);
  click('Reset data');
  assert.deepEqual(nodes(render()).find(n=>n.props.spec).props.spec.data,[2,3,3,4,5]);
});
