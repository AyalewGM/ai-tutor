import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import { checkSlope, formatRational, LINEAR_PRACTICE, linearModel } from "./linearExplorer";
import type { MathInteractionEvent } from "./interactions";

export interface InteractiveLinearExplorerProps {
  independentAssessment: boolean;
  onMathEvent?: (event: MathInteractionEvent) => void;
}
export function InteractiveLinearExplorer(props: InteractiveLinearExplorerProps) {
  if (props.independentAssessment !== false) return null;
  return <GuidedLinearExplorer {...props} />;
}
function GuidedLinearExplorer({ onMathEvent }: InteractiveLinearExplorerProps) {
  const id = useId();
  const [rise, setRise] = useState(2);
  const [run, setRun] = useState(3);
  const [intercept, setIntercept] = useState(1);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const model = linearModel(rise, run, intercept);
  const item = LINEAR_PRACTICE[index];
  const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600";
  function update(nextRise: number, nextRun: number, nextIntercept: number) {
    linearModel(nextRise, nextRun, nextIntercept);
    setRise(nextRise); setRun(nextRun); setIntercept(nextIntercept);
    onMathEvent?.({ schema_version: 1, type: "LINEAR_PARAMETERS_CHANGED", rise: nextRise, run: nextRun, intercept: nextIntercept });
  }
  return <section aria-label="Guided slope and intercept exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: a line, its equation, and its table</h3>
    <p>This separate guided example does not count toward mastery.</p>
    <ProblemVisual spec={{ type: "linear_graph", m_num: rise, m_den: run, b: intercept,
      min: -10, max: 10, mark_lattice: true, show_slope_triangle: true, aria_label: `${model.equation}. ${model.explanation}` }} />
    <h3 className="font-semibold">Manipulate</h3>
    <p>Use arrow keys on the sliders. Hold rise and run fixed while changing the intercept. Then hold the intercept fixed while changing the slope.</p>
    <label className="block" htmlFor={`${id}-rise`}>Rise (signed change in y): {rise}</label>
    <input className={`w-full ${control}`} id={`${id}-rise`} type="range" min={-6} max={6} step={1} value={rise}
      onChange={e => update(Number(e.target.value), run, intercept)} />
    <label className="block" htmlFor={`${id}-run`}>Run (positive change in x): {run}</label>
    <input className={`w-full ${control}`} id={`${id}-run`} type="range" min={1} max={6} step={1} value={run}
      onChange={e => update(rise, Number(e.target.value), intercept)} />
    <label className="block" htmlFor={`${id}-intercept`}>Y-intercept: {intercept}</label>
    <input className={`w-full ${control}`} id={`${id}-intercept`} type="range" min={-4} max={4} step={1} value={intercept}
      onChange={e => update(rise, run, Number(e.target.value))} />
    <h3 className="font-semibold">Explain</h3>
    <p role="status" aria-live="polite" aria-atomic="true">{model.equation}. {model.explanation}</p>
    <p>Marked points include (0, {intercept}) and ({run}, {intercept + rise}). Changing the intercept shifts the line without changing its slope. Run is never zero here: a vertical line has undefined slope and cannot be written as y = mx + b.</p>
    <table className="w-full text-left"><caption>Exact values for the current line</caption>
      <thead><tr><th scope="col">x</th><th scope="col">y</th></tr></thead>
      <tbody>{model.rows.map(row => <tr key={row.x}><th scope="row">{row.x}</th><td>{formatRational(row.y)}</td></tr>)}</tbody>
    </table>
    <h3 className="font-semibold">Practice</h3>
    <p>Separate practice {index + 1} of {LINEAR_PRACTICE.length}: a line passes through (0, {item.intercept}) and ({item.run}, {item.intercept + item.rise}). What is its slope?</p>
    <label className="block" htmlFor={`${id}-answer`}>Slope as an integer or fraction</label>
    <input id={`${id}-answer`} className={control} value={answer} maxLength={12} aria-describedby={`${id}-feedback`}
      onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
    <div className="flex gap-2"><button className={control} type="button" onClick={() => setFeedback(checkSlope(index, answer).feedback)}>Check slope</button>
      <button className={control} type="button" onClick={() => { setIndex((index + 1) % LINEAR_PRACTICE.length); setAnswer(""); setFeedback(""); }}>Next practice</button></div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
  </section>;
}
