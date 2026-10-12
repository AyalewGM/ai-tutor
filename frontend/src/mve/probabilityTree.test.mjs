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
const math = load('./probabilityTree.ts', { './linearExplorer': rational });
const events = load('./interactions.ts');
const registry = load('./rendererRegistry.ts');
const visual = load('../components/ProblemVisual.tsx', { '../mve/rendererRegistry': registry });
const imports = { './probabilityTree': math, './linearExplorer': rational, '../components/ProblemVisual': visual };
const { InteractiveProbabilityTree: Component } = load('./InteractiveProbabilityTree.tsx', imports);

test('exact tree probabilities reduce and partition the sample space', () => {
  const state = { first: { label: 'red', favorable: 3, total: 8 }, second: { label: 'heads', favorable: 1, total: 2 } };
  const model = math.probabilityTreeModel(state);
  assert.equal(rational.formatRational(model.bothProbability), '3/16');
  assert.equal(rational.formatRational(model.atLeastOneProbability), '11/16');
  assert.equal(rational.formatRational(model.neitherProbability), '5/16');
  assert.equal(model.sampleSpaceSize, 16);
  assert.equal(model.outcomes.reduce((sum, outcome) => sum + outcome.probability.numerator * (16 / outcome.probability.denominator), 0), 16);
});

test('all bounded independent event pairs agree with complement identities', () => {
  for (let firstTotal = 2; firstTotal <= 12; firstTotal++) {
    for (let first = 1; first < firstTotal; first++) {
      for (let secondTotal = 2; secondTotal <= 12; secondTotal++) {
        for (let second = 1; second < secondTotal; second++) {
          const model = math.probabilityTreeModel({
            first: { label: 'A', favorable: first, total: firstTotal },
            second: { label: 'B', favorable: second, total: secondTotal },
          });
          const denominator = firstTotal * secondTotal;
          assert.equal(model.bothProbability.numerator * denominator / model.bothProbability.denominator, first * second);
          assert.equal(
            model.atLeastOneProbability.numerator * denominator / model.atLeastOneProbability.denominator,
            denominator - (firstTotal - first) * (secondTotal - second),
          );
        }
      }
    }
  }
});

test('updates clamp favorable count and invalid states fail closed', () => {
  const state = { first: { label: 'A', favorable: 5, total: 8 }, second: { label: 'B', favorable: 3, total: 6 } };
  assert.equal(math.updateProbabilityStage(state, 'first', 'total', 4).first.favorable, 3);
  for (const invalid of [
    null, {}, { first: { label: '', favorable: 1, total: 2 }, second: state.second },
    { first: { label: 'A', favorable: 0, total: 2 }, second: state.second },
    { first: { label: 'A', favorable: 2, total: 2 }, second: state.second },
    { first: { label: 'A', favorable: 1, total: 13 }, second: state.second },
  ]) {
    assert.equal(math.isProbabilityTreeState(invalid), false);
    assert.throws(() => math.probabilityTreeModel(invalid));
  }
});

test('practice checks exact fractions and diagnoses observable misconceptions without leaking answers', () => {
  for (const [index, answer] of ['1/5','23/48','3/14','1/8'].entries()) {
    assert.equal(math.checkProbabilityTreeAnswer(index, answer).correct, true);
  }
  const addError = math.classifyProbabilityTreeAnswer(0, '9/10');
  assert.equal(addError.misconception, 'ADD_BRANCH_PROBABILITIES');
  assert.equal(addError.feedback.includes('1/5'), false);
  const atLeastAsBoth = math.classifyProbabilityTreeAnswer(1, '1/16');
  assert.equal(atLeastAsBoth.misconception, 'AT_LEAST_ONE_AS_BOTH');
  assert.equal(atLeastAsBoth.feedback.includes('23/48'), false);
  const complementError = math.classifyProbabilityTreeAnswer(2, '2/7');
  assert.equal(complementError.misconception, 'BRANCH_COMPLEMENT_CONFUSION');
  assert.equal(complementError.feedback.includes('3/14'), false);
  assert.equal(math.checkProbabilityTreeAnswer(0, '2/10').correct, true);
  for (const answer of ['', '0.2', '1/0', '-1/5', 'one fifth']) {
    assert.equal(math.checkProbabilityTreeAnswer(0, answer).correct, false);
  }
  assert.throws(() => math.checkProbabilityTreeAnswer(20, '1'));
});

test('repair exact-fraction checks accept equivalent forms and reject unequal values', () => {
  for (const answer of ['1/8', '2/16', '3/24']) {
    assert.equal(math.isEquivalentProbabilityAnswer(answer, 1, 8), true);
  }
  for (const answer of ['5/8', '10/16', '15/24']) {
    assert.equal(math.isEquivalentProbabilityAnswer(answer, 5, 8), true);
  }
  for (const answer of ['8/15', '16/30', '24/45']) {
    assert.equal(math.isEquivalentProbabilityAnswer(answer, 8, 15), true);
  }
  for (const answer of ['1/7', '5/9', '8/16', '', '1/0', '0.125']) {
    assert.equal(math.isEquivalentProbabilityAnswer(answer, 1, 8), false);
  }
});

test('event validation rejects extra fields and impossible probabilities', () => {
  const event = { schema_version: 1, type: 'PROBABILITY_TREE_CHANGED', first_favorable: 3, first_total: 8, second_favorable: 1, second_total: 2 };
  assert.equal(events.isMathInteractionEvent(event), true);
  assert.equal(events.isMathInteractionEvent({ ...event, student_id: 'test' }), false);
  assert.equal(events.isMathInteractionEvent({ ...event, first_favorable: 8 }), false);
  assert.equal(events.isMathInteractionEvent({ ...event, second_total: 13 }), false);
});

test('real renderer, labeled controls, status and assessment guard render correctly', () => {
  const html = renderToStaticMarkup(React.createElement(Component, { independentAssessment: false }));
  for (const term of ['Guided probability tree exploration','Path probabilities for independent stages','scope="col"','aria-live="polite"','focus-visible:outline','At least one favorable','Sample space: 16','Observe','Predict','Manipulate','Explain','Practice','Lock prediction','Check explanation']) {
    assert.ok(html.includes(term), term);
  }
  for (const term of ['second-stage probabilities stay the same','conditional branch probabilities','this model is independent']) {
    assert.ok(html.includes(term), term);
  }
  for (const [, id] of html.matchAll(/<label[^>]*for="([^"]+)"/g)) assert.ok(html.includes(`id="${id}"`));
  for (const mode of [true, undefined, null]) assert.equal(renderToStaticMarkup(React.createElement(Component, { independentAssessment: mode })), '');
  assert.equal(math.showProbabilityTreeExploration('GUIDED_PRACTICE', 'Compound Probability'), true);
  assert.equal(math.showProbabilityTreeExploration('REMEDIATION', 'Probability Trees'), true);
  assert.equal(math.showProbabilityTreeExploration('MASTERY_CHECK', 'Compound Probability'), false);
});

test('actual handlers update the tree and emit strict math events', () => {
  let state = [], cursor = 0; const emitted = [];
  const hooked = load('./InteractiveProbabilityTree.tsx', { ...imports, react: {
    useId: () => 'prob', useState: initial => { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
  }});
  function render() { cursor = 0; const wrapper = hooked.InteractiveProbabilityTree({ independentAssessment: false, onMathEvent: e => emitted.push(e) }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== 'object' ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  // The learner must commit a prediction before the visual tree is rendered.
  // Without this step, looking for the ProblemVisual spec later is invalid.
  nodes(render()).find(n => n.props.id === 'prob-prediction').props.onChange({ target: { value: 'increase' } });
  nodes(render()).find(n => n.type === 'button' && n.props.children === 'Lock prediction').props.onClick();
  nodes(render()).find(n => n.props.id === 'prob-first-total').props.onChange({ target: { value: '4' } });
  assert.equal(emitted.at(-1).first_total, 4);
  assert.equal(emitted.at(-1).first_favorable, 3);
  assert.equal(events.isMathInteractionEvent(emitted.at(-1)), true);
  nodes(render()).find(n => n.props.id === 'prob-second-total').props.onChange({ target: { value: '5' } });
  nodes(render()).find(n => n.props.id === 'prob-second-fav').props.onChange({ target: { value: '2' } });
  assert.equal(nodes(render()).find(n => n.props.spec).props.spec.second_favorable, 2);
  nodes(render()).find(n => n.props.id === 'prob-answer').props.onChange({ target: { value: '1/5' } });
  nodes(render()).find(n => n.type === 'button' && n.props.children === 'Check probability').props.onClick();
  assert.match(nodes(render()).find(n => n.props.id === 'prob-feedback').props.children, /^Correct/);
});

test('prediction gates manipulation and explanation evidence drives scaffold fading', () => {
  let state = [], cursor = 0;
  const hooked = load('./InteractiveProbabilityTree.tsx', { ...imports, react: {
    useId: () => 'ped', useState: initial => { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
  }});
  function render() { cursor = 0; const wrapper = hooked.InteractiveProbabilityTree({ independentAssessment: false }); return wrapper.type(wrapper.props); }
  function nodes(node) { return !node || typeof node !== 'object' ? [] : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)]; }
  let tree = nodes(render());
  assert.equal(tree.find(n => n.type === 'fieldset').props.disabled, true);
  tree.find(n => n.props.id === 'ped-prediction').props.onChange({ target: { value: 'increase' } });
  tree = nodes(render());
  tree.find(n => n.type === 'button' && n.props.children === 'Lock prediction').props.onClick();
  tree = nodes(render());
  assert.equal(tree.find(n => n.type === 'fieldset').props.disabled, false);
  tree.find(n => n.props.id === 'ped-reasoning').props.onChange({ target: { value: 'add' } });
  tree = nodes(render());
  tree.find(n => n.type === 'button' && n.props.children === 'Check explanation').props.onClick();
  tree = nodes(render());
  assert.match(tree.find(n => n.props.children === 'Not yet. Adding stage probabilities mixes separate stages. Complete a different path repair before continuing.').props.children, /Not yet/);
  tree.find(n => n.props.id === 'ped-reasoning').props.onChange({ target: { value: 'multiply' } });
  tree = nodes(render());
  tree.find(n => n.type === 'button' && n.props.children === 'Check explanation').props.onClick();
  tree = nodes(render());
  assert.ok(tree.some(n => n.props.children === 'Scaffold faded: use the next practice without relying on the path table first.'));
});

test('scaffold really hides revealing probability support after verified reasoning', () => {
  const source = readFileSync(new URL('./InteractiveProbabilityTree.tsx', import.meta.url), 'utf8');
  assert.match(source, /!scaffoldFaded && <p role="status"/);
  assert.match(source, /!scaffoldFaded && <table/);
  assert.match(source, /Repair and verify/);
  assert.match(source, /Probability model transfer/);
  assert.match(source, /worked answer stays hidden/);
});

test("prediction evidence is evaluated only for the stated favorable-outcome increase", () => {
  const source = readFileSync(new URL("./InteractiveProbabilityTree.tsx", import.meta.url), "utf8");
  assert.match(source, /stage === "first" && field === "favorable" && value > state\.first\.favorable/);
  assert.match(source, /if the first-event favorable chance increases while the second stage stays fixed/);
  assert.match(source, /min=\{predictionCommitted && !predictionEvidence \? state\.first\.favorable : 1\}/);
});
