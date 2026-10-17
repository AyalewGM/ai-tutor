import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import React from "react";
import ts from "typescript";
import {
  classifyEquivalentAnswer,
  classifyRatioAnswer,
  equivalenceModel,
  ratioPartitionModel,
} from "./guidedConceptMath.mjs";

test("equivalence is exact and distinguishes two misconceptions", () => {
  const model = equivalenceModel(2, 3, 3);
  assert.deepEqual(model, {
    numerator: 2, denominator: 3, scale: 3,
    expandedNumerator: 6, expandedDenominator: 9,
  });
  assert.deepEqual(classifyEquivalentAnswer(model, "6"), {
    correct: true, misconception: null,
  });
  assert.equal(classifyEquivalentAnswer(model, "2").misconception, "NUMERATOR_NOT_SCALED");
  assert.equal(classifyEquivalentAnswer(model, "5").misconception, "ADDITIVE_SCALING");
  for (const invalid of ["6.0", "6/9", "Infinity", "-6", "6e0", ""]) {
    assert.equal(classifyEquivalentAnswer(model, invalid).correct, false);
  }
});

test("ratio partition computes the unit before shares", () => {
  const model = ratioPartitionModel(2, 3, 4);
  assert.equal(model.totalParts, 5);
  assert.equal(model.total, 20);
  assert.equal(model.firstShare, 8);
  assert.equal(classifyRatioAnswer(model, "8").correct, true);
  assert.equal(classifyRatioAnswer(model, "20").misconception, "WHOLE_INSTEAD_OF_SHARE");
  assert.equal(classifyRatioAnswer(model, "10").misconception, "WRONG_PART_COUNT");
});

test("all supported parameter combinations preserve mathematical invariants", () => {
  for (let denominator = 2; denominator <= 6; denominator++) {
    for (let numerator = 1; numerator < denominator; numerator++) {
      for (let scale = 2; scale <= 3; scale++) {
        if (denominator * scale > 12) continue;
        const model = equivalenceModel(numerator, denominator, scale);
        assert.equal(
          model.numerator * model.expandedDenominator,
          model.denominator * model.expandedNumerator,
        );
      }
    }
  }
  for (let first = 1; first <= 5; first++) {
    for (let second = 1; second <= 5; second++) {
      for (let unit = 1; unit <= 20; unit++) {
        const model = ratioPartitionModel(first, second, unit);
        assert.equal(model.firstShare + model.secondParts * unit, model.total);
        assert.equal(model.total / model.totalParts, unit);
      }
    }
  }
});

test("invalid parameters fail closed", () => {
  for (const args of [[0, 3, 2], [2, 2, 2], [2, 3, 5], [2, 6, 3], [2.5, 3, 2]]) {
    assert.throws(() => equivalenceModel(...args), RangeError);
  }
  for (const args of [[0, 2, 4], [2, 0, 4], [2, 3, 0], [2, 3, 21], [2, 3, 2.5]]) {
    assert.throws(() => ratioPartitionModel(...args), RangeError);
  }
});

test("interactive lessons remain unmounted until a trusted capability and pedagogy acceptance", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
  assert.match(ui, /if \(props\.independentAssessment !== false\) return null/);
  assert.match(ui, /role="status" aria-live="polite"/);
  assert.match(ui, /type="submit"/);
  assert.match(ui, /Lock prediction/);
  assert.match(ui, /Check explanation/);
  assert.match(ui, /Repair and verify/);
  assert.match(ui, /Transfer without/);
  assert.match(ui, /ProblemVisual/);
  // No accepted server-owned fraction-equivalence or ratio-partition
  // capability exists. Build flags and mutable display-name regexes are
  // explicitly NOT authority to mount the guided component.
  assert.doesNotMatch(workspace, /VITE_ENABLE_CONCEPT_GUIDED_PILOT/);
  assert.doesNotMatch(workspace, /conceptGuidedPilotEnabled/);
  assert.doesNotMatch(workspace, /<GuidedConceptPractice\b/);
  assert.doesNotMatch(ui, /updateMastery|setMastery|recordAssessment|fetch\(|post\(/);
});

test("concept lessons implement real scaffold fading and transfer surfaces", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  assert.match(ui, /!explanationVerified && <ProblemVisual/);
  assert.match(ui, /!explanationVerified && <div aria-label="Five equal ratio parts"/);
  assert.match(ui, /Fraction misconception repair/);
  assert.match(ui, /Ratio misconception repair/);
  assert.match(ui, /Fraction transfer/);
  assert.match(ui, /Ratio transfer/);
  assert.match(ui, /worked answer|stays unworked|without counters|without the completed bar/i);
});

test("repairs do not reveal expected ratio shares and completed fraction model waits for numeric evidence", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(ui, /Enter both shares as 6,18|Enter both shares as 12,18|Enter both shares as 12,16/);
  assert.match(ui, /Ratio repair common unit/);
  assert.match(ui, /numericVerified && !explanationVerified && <ProblemVisual/);
});

test("concept predictions are evaluated with targeted reflection", async () => {
  const ui = await readFile(new URL("./GuidedConceptPractice.tsx", import.meta.url), "utf8");
  assert.match(ui, /Your prediction matches the mathematical relationship/);
  assert.match(ui, /same whole is repartitioned/);
  assert.match(ui, /2 of 5 equal parts is less than one half/);
  assert.match(ui, /predictionFeedback/);
});


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

function conceptHarness(concept) {
  let state = [];
  let cursor = 0;
  const hooked = load("./GuidedConceptPractice.tsx", {
    "./guidedConceptMath.mjs": {
      classifyEquivalentAnswer,
      classifyRatioAnswer,
      equivalenceModel,
      ratioPartitionModel,
    },
    "../components/ProblemVisual": props => React.createElement("div", {
      "data-visual-label": props.spec.aria_label,
    }),
    react: {
      useState: initial => {
        const index = cursor++;
        if (!(index in state)) state[index] = typeof initial === "function" ? initial() : initial;
        return [state[index], value => {
          state[index] = typeof value === "function" ? value(state[index]) : value;
        }];
      },
    },
  });

  function render() {
    cursor = 0;
    const wrapper = hooked.GuidedConceptPractice({ independentAssessment: false, concept });
    return wrapper.type(wrapper.props);
  }
  function nodes(node) {
    if (!node || typeof node !== "object") return [];
    const expanded = typeof node.type === "function" ? node.type(node.props) : null;
    return [node, ...nodes(expanded), ...React.Children.toArray(node.props?.children).flatMap(nodes)];
  }
  const all = () => nodes(render());
  const byId = id => all().find(node => node.props?.id === id);
  const byLabel = label => all().find(node => node.props?.["aria-label"] === label);
  const button = label => all().find(node => node.type === "button" && node.props.children === label);
  const change = (node, value) => node.props.onChange({ target: { value } });
  const click = label => button(label).props.onClick();
  const submit = () => all().find(node => node.type === "form").props.onSubmit({ preventDefault() {} });
  const hasText = value => all().some(node =>
    React.Children.toArray(node.props?.children).join("").includes(value));
  return { all, byId, byLabel, change, click, submit, hasText };
}

test("fraction verification is bound to the exact response snapshot", () => {
  const ui = conceptHarness("fraction-equivalence");
  ui.change(ui.byId("fraction-prediction"), "same");
  ui.click("Lock prediction");
  ui.change(ui.byId("equivalent-numerator"), "6");
  ui.submit();
  ui.change(ui.byId("fraction-scale"), "3");
  ui.change(ui.byId("fraction-new-numerator"), "6");
  ui.change(ui.byId("fraction-same-whole"), "same-factor");
  ui.click("Check explanation");
  assert.ok(ui.byLabel("Fraction transfer"));

  ui.change(ui.byLabel("Transfer numerator out of twelve"), "9");
  ui.change(ui.byLabel("Transfer scale factor"), "3");
  ui.change(ui.byLabel("Transfer reasoning"), "same-factor");
  ui.click("Check transfer");
  assert.ok(ui.hasText("Transfer verified: 3/4 = 9/12."));

  ui.change(ui.byId("fraction-scale"), " 3 ");
  assert.equal(ui.byLabel("Fraction transfer"), undefined);
  assert.equal(ui.hasText("Transfer verified: 3/4 = 9/12."), false);
  assert.ok(ui.hasText("Your verified explanation changed."));
  assert.ok(ui.all().some(node =>
    node.props?.["data-visual-label"] === "Six of nine equal parts shaded, same length as two thirds"));

  ui.click("Check explanation");
  assert.ok(ui.byLabel("Fraction transfer"));
  ui.change(ui.byId("equivalent-numerator"), " 6 ");
  assert.equal(ui.byLabel("Fraction transfer"), undefined);
  assert.equal(ui.hasText("Transfer verified: 3/4 = 9/12."), false);
  assert.ok(ui.hasText("Your numeric evidence changed."));
  assert.equal(ui.all().some(node =>
    node.props?.["data-visual-label"] === "Six of nine equal parts shaded, same length as two thirds"), false);
});

test("ratio verification is bound to the exact response snapshot", () => {
  const ui = conceptHarness("ratio-partition");
  ui.change(ui.byLabel("Ratio prediction"), "less");
  ui.click("Lock prediction");
  ui.change(ui.byId("ratio-first-share"), "8");
  ui.submit();
  ui.change(ui.byLabel("Total ratio parts"), "5");
  ui.change(ui.byLabel("Common unit value"), "4");
  ui.change(ui.byLabel("First share from two units"), "8");
  ui.change(ui.byLabel("Recomposition equation total"), "8 + 12 = 20");
  ui.click("Check explanation");
  assert.ok(ui.byLabel("Ratio transfer"));

  ui.change(ui.byLabel("Transfer parts"), "7");
  ui.change(ui.byLabel("Transfer unit"), "5");
  ui.change(ui.byLabel("Transfer first"), "10");
  ui.change(ui.byLabel("Transfer second"), "25");
  ui.click("Check transfer");
  assert.ok(ui.hasText("Transfer verified: 10 + 25 = 35 minutes."));

  ui.change(ui.byLabel("Common unit value"), " 4 ");
  assert.equal(ui.byLabel("Ratio transfer"), undefined);
  assert.equal(ui.hasText("Transfer verified: 10 + 25 = 35 minutes."), false);
  assert.ok(ui.hasText("Your verified explanation changed."));
  assert.ok(ui.byLabel("Five equal ratio parts"));

  ui.click("Check explanation");
  assert.ok(ui.byLabel("Ratio transfer"));
  ui.change(ui.byId("ratio-first-share"), " 8 ");
  assert.equal(ui.byLabel("Ratio transfer"), undefined);
  assert.equal(ui.hasText("Transfer verified: 10 + 25 = 35 minutes."), false);
  assert.ok(ui.hasText("Your numeric evidence changed."));
});
