import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import type { MathInteractionEvent } from "./interactions";
import { formatRational } from "./linearExplorer";
import {
  checkProbabilityTreeAnswer,
  MAX_PROBABILITY_TOTAL,
  MIN_PROBABILITY_TOTAL,
  probabilityTreeModel,
  PROBABILITY_TREE_PRACTICE,
  updateProbabilityStage,
  type ProbabilityTreeState,
} from "./probabilityTree";

export interface InteractiveProbabilityTreeProps {
  independentAssessment: boolean;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

const INITIAL_TREE: ProbabilityTreeState = {
  first: { label: "red", favorable: 3, total: 8 },
  second: { label: "heads", favorable: 1, total: 2 },
};

export function InteractiveProbabilityTree(props: InteractiveProbabilityTreeProps) {
  if (props.independentAssessment !== false) return null;
  return <GuidedProbabilityTree {...props} />;
}

function GuidedProbabilityTree({ onMathEvent }: InteractiveProbabilityTreeProps) {
  const id = useId();
  const [state, setState] = useState(INITIAL_TREE);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const model = probabilityTreeModel(state);
  const item = PROBABILITY_TREE_PRACTICE[index];
  const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50";

  function change(stage: "first" | "second", field: "favorable" | "total", value: number) {
    const next = updateProbabilityStage(state, stage, field, value);
    setState(next);
    onMathEvent?.({
      schema_version: 1,
      type: "PROBABILITY_TREE_CHANGED",
      first_favorable: next.first.favorable,
      first_total: next.first.total,
      second_favorable: next.second.favorable,
      second_total: next.second.total,
    });
  }

  return <section aria-label="Guided probability tree exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: a compound event has two stages</h3>
    <p>This separate synthetic model does not count toward mastery. Each path through the tree is one ordered outcome type.</p>
    <ProblemVisual spec={{
      type: "probability_tree",
      first_label: state.first.label,
      first_favorable: state.first.favorable,
      first_total: state.first.total,
      second_label: state.second.label,
      second_favorable: state.second.favorable,
      second_total: state.second.total,
      aria_label: `Probability tree for ${state.first.favorable} of ${state.first.total} ${state.first.label} outcomes followed by ${state.second.favorable} of ${state.second.total} ${state.second.label} outcomes.`,
    }} />
    <h3 className="font-semibold">Manipulate</h3>
    <div className="grid gap-3 md:grid-cols-2">
      <div>
        <label className="block" htmlFor={`${id}-first-total`}>First event total outcomes: {state.first.total}</label>
        <input id={`${id}-first-total`} className={`w-full ${control}`} type="range" min={MIN_PROBABILITY_TOTAL} max={MAX_PROBABILITY_TOTAL} step={1}
          value={state.first.total} onChange={e => change("first", "total", Number(e.target.value))} />
        <label className="block" htmlFor={`${id}-first-fav`}>First event favorable outcomes: {state.first.favorable}</label>
        <input id={`${id}-first-fav`} className={`w-full ${control}`} type="range" min={1} max={state.first.total - 1} step={1}
          value={state.first.favorable} onChange={e => change("first", "favorable", Number(e.target.value))} />
      </div>
      <div>
        <label className="block" htmlFor={`${id}-second-total`}>Second event total outcomes: {state.second.total}</label>
        <input id={`${id}-second-total`} className={`w-full ${control}`} type="range" min={MIN_PROBABILITY_TOTAL} max={MAX_PROBABILITY_TOTAL} step={1}
          value={state.second.total} onChange={e => change("second", "total", Number(e.target.value))} />
        <label className="block" htmlFor={`${id}-second-fav`}>Second event favorable outcomes: {state.second.favorable}</label>
        <input id={`${id}-second-fav`} className={`w-full ${control}`} type="range" min={1} max={state.second.total - 1} step={1}
          value={state.second.favorable} onChange={e => change("second", "favorable", Number(e.target.value))} />
      </div>
    </div>
    <p>Use arrow keys on any slider. Increasing a total adds possible outcomes; increasing favorable outcomes thickens the favorable branch.</p>
    <h3 className="font-semibold">Explain</h3>
    <p role="status" aria-live="polite" aria-atomic="true">
      Both favorable: {formatRational(model.bothProbability)}. At least one favorable: {formatRational(model.atLeastOneProbability)}. Neither: {formatRational(model.neitherProbability)}. Sample space: {model.sampleSpaceSize} ordered outcomes.
    </p>
    <table className="w-full text-left">
      <caption>Path probabilities: multiply along each branch</caption>
      <thead><tr><th scope="col">Path</th><th scope="col">Probability</th></tr></thead>
      <tbody>{model.outcomes.map(outcome => <tr key={outcome.label}><th scope="row">{outcome.label}</th><td>{formatRational(outcome.probability)}</td></tr>)}</tbody>
    </table>
    <p>The probability of both favorable events is one path. The probability of at least one favorable event is the sum of three paths, or one minus the neither path.</p>
    <h3 className="font-semibold">Practice</h3>
    <p>Separate practice {index + 1} of {PROBABILITY_TREE_PRACTICE.length}: find {item.measure.replaceAll("_", " ")} for {item.state.first.favorable}/{item.state.first.total} and {item.state.second.favorable}/{item.state.second.total}.</p>
    <label className="block" htmlFor={`${id}-answer`}>Probability practice answer</label>
    <input id={`${id}-answer`} className={control} value={answer} maxLength={10} aria-describedby={`${id}-feedback`}
      onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
    <div className="flex gap-2">
      <button type="button" className={control} onClick={() => setFeedback(checkProbabilityTreeAnswer(index, answer).feedback)}>Check probability</button>
      <button type="button" className={control} onClick={() => { setIndex((index + 1) % PROBABILITY_TREE_PRACTICE.length); setAnswer(""); setFeedback(""); }}>Next probability practice</button>
    </div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
  </section>;
}
