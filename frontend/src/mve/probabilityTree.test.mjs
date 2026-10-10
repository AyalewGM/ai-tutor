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

test('practice checks exact fractions and rejects ambiguous answers', () => {
  for (const [index, answer] of ['1/5','23/48','3/14','1/8'].entries()) {
    assert.equal(math.checkProbabilityTreeAnswer(index, answer).correct, true);
  }
  assert.equal(math.checkProbabilityTreeAnswer(0, '2/10').correct, true);
  for (const answer of ['', '0.2', '1/0', '-1/5', 'one fifth']) {
    assert.equal(math.checkProbabilityTreeAnswer(0, answer).correct, false);
  }
  assert.throws(() => math.checkProbabilityTreeAnswer(20, '1'));
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
  for (const term of ['Guided probability tree exploration','<svg','Path probabilities','scope="col"','aria-live="polite"','focus-visible:outline','At least one favorable','Sample space: 16','Observe','Manipulate','Explain','Practice']) {
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
