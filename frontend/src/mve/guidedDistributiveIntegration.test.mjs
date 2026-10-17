import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
const workspace = await readFile(new URL("../pages/Workspace.tsx", import.meta.url), "utf8");
const guided = await readFile(new URL("./GuidedDistributivePractice.tsx", import.meta.url), "utf8");
const player = await readFile(new URL("./PedagogicalAnimation.tsx", import.meta.url), "utf8");
const lesson = await readFile(new URL("./distributiveLesson.ts", import.meta.url), "utf8");
const interactions = await readFile(new URL("./interactions.ts", import.meta.url), "utf8");

// Transpile real React components in memory, without adding a new test framework
// or touching the browser application. Stub only the SVG renderer.
function loadTypeScript(source, imports = {}) {
  const js = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const resolve = (name) => Object.hasOwn(imports, name) ? imports[name] : require(name);
  new Function("require", "module", "exports", js)(resolve, module, module.exports);
  return module.exports;
}

const lessonModule = loadTypeScript(lesson);
const interactionModule = loadTypeScript(interactions);
const playerModule = loadTypeScript(player);
const visualStub = {
  default: ({ spec }) => React.createElement("div", {
    role: "img", "aria-label": spec.aria_label,
  }),
};
const guidedModule = loadTypeScript(guided, {
  "../components/ProblemVisual": visualStub,
  "./PedagogicalAnimation": playerModule,
  "./distributiveLesson": lessonModule,
});

test("workspace keeps distributive lesson fail closed without an accepted capability", () => {
  assert.doesNotMatch(workspace, /<GuidedDistributivePractice\s/);
  assert.doesNotMatch(workspace, /\/distributive\|expand\.\*parenthes\/i/);
  assert.match(workspace, /Distributive, linear and balance lessons stay disabled/);
  assert.match(workspace, /integerAdditionEligible\(workspace\.state, learn\)/);
});

test("independent assessment renders no guided explanation, worked answer, or controls", () => {
  const { GuidedDistributivePractice } = guidedModule;
  for (const independentAssessment of [true, undefined, null]) {
    const html = renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
      independentAssessment, factor: 5, constant: 3,
    }));
    assert.equal(html, "");
  }
  // The fail-closed guard must run before lesson construction, even on invalid data.
  assert.equal(renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
    independentAssessment: true, factor: -1, constant: 3,
  })), "");
  assert.equal(renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
    independentAssessment: false, factor: 0, constant: 3,
  })), "");
});

test("guided state renders the real accessible player and separate worked example", () => {
  const { GuidedDistributivePractice } = guidedModule;
  const html = renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
    independentAssessment: false, factor: 5, constant: 3,
  }));
  assert.match(html, /Guided distributive property lesson/);
  assert.match(html, /5\(x \+ 3\)/);
  assert.match(html, /Worked example, separate from your current question/);
  assert.match(html, /aria-label="Animation playback controls"/);
  assert.match(html, /aria-label="Play animation"/);
  assert.match(html, /<button type="button"/);
  assert.match(html, /Previous step/);
  assert.match(html, /Next step/);
  assert.match(html, /Replay/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /Observe and predict/);
  assert.match(html, /aria-pressed="false"/);
  assert.match(html, /Coefficient of x/);
  assert.match(html, /Constant term/);
});

test("negative distribution uses signed algebra tiles and keeps state lifecycle keyed to the lesson", () => {
  const { GuidedDistributivePractice } = guidedModule;
  const html = renderToStaticMarkup(React.createElement(GuidedDistributivePractice, {
    independentAssessment: false, factor: -2, constant: -4,
  }));
  assert.match(html, /-2\(x − 4\)/);
  assert.match(guided, /key=\{`\$\{lesson\.factor\}\|\$\{lesson\.constant\}/);
  assert.match(guided, /lesson\.algebraTiles/);
  assert.match(guided, /DROPPED_NEGATIVE/);
});

test("shared player supports reduced-motion, keyboard-native controls, and timer cleanup", () => {
  assert.match(guided, /<PedagogicalAnimation/);
  assert.match(player, /prefers-reduced-motion: reduce/);
  assert.match(player, /if \(prefersReducedMotion\) setPlaying\(false\)/);
  assert.match(player, /clearTimeout\(timer\)/);
  assert.match(player, /onClick=/);
  assert.match(player, /aria-label="Animation playback controls"/);
});

test("guided checks use deterministic misconception classification", () => {
  assert.match(guided, /checkDistributiveCoefficients\(lesson/);
  assert.match(guided, /MISSED_SECOND_TERM/);
  assert.match(guided, /COEFFICIENT_ERROR/);
  assert.equal(lessonModule.checkDistributiveCoefficients(
    lessonModule.buildDistributiveLesson(5, 3), 5, 3,
  ).misconception, "MISSED_SECOND_TERM");
});

test("actual handlers announce sign feedback and emit a bounded dropped-negative diagnosis", () => {
  let state = [];
  let cursor = 0;
  const emitted = [];
  const hooked = loadTypeScript(guided, {
    ...{
      "../components/ProblemVisual": visualStub,
      "./PedagogicalAnimation": playerModule,
      "./distributiveLesson": lessonModule,
    },
    react: {
      useCallback: (callback) => callback,
      useId: () => "signed-distribution",
      useState: (initial) => {
        const index = cursor++;
        if (!(index in state)) state[index] = initial;
        return [state[index], (value) => { state[index] = typeof value === "function" ? value(state[index]) : value; }];
      },
    },
  });
  const render = () => {
    cursor = 0;
    const wrapper = hooked.GuidedDistributivePractice({
      independentAssessment: false, factor: -2, constant: -4,
      onMathEvent: (event) => emitted.push(event),
    });
    return wrapper.type(wrapper.props);
  };
  const nodes = (node) => !node || typeof node !== "object" ? []
    : [node, ...React.Children.toArray(node.props?.children).flatMap(nodes)];

  nodes(render()).find((node) => node.type === "button" && node.props.children === "Negative").props.onClick();
  assert.match(nodes(render()).find((node) => node.props.role === "status").props.children, /Recheck/);
  nodes(render()).find((node) => node.props.id === "signed-distribution-coefficient").props.onChange({ target: { value: "2" } });
  nodes(render()).find((node) => node.props.id === "signed-distribution-constant").props.onChange({ target: { value: "-8" } });
  nodes(render()).find((node) => node.type === "form").props.onSubmit({ preventDefault() {} });
  const feedback = nodes(render()).find((node) => node.props.id === "signed-distribution-feedback").props.children;
  assert.match(feedback, /outside negative/);
  assert.doesNotMatch(feedback, /-2x|\+ 8|answer is/i);
  assert.deepEqual(emitted.at(-1), {
    schema_version: 1,
    type: "DISTRIBUTIVE_COEFFICIENTS_CHECKED",
    variable_coefficient: 2,
    constant_term: -8,
    correct: false,
    misconception: "DROPPED_NEGATIVE",
  });
  assert.equal(interactionModule.isMathInteractionEvent(emitted.at(-1)), true);
  assert.equal(interactionModule.isMathInteractionEvent({ ...emitted.at(-1), correct: true }), false);
});
