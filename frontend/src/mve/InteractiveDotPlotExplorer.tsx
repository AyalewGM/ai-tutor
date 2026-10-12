import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import { checkDatasetAnswer, datasetModel, DOT_PRACTICE, replaceObservation } from "./dotPlotExplorer";
import { formatRational } from "./linearExplorer";
import type { MathInteractionEvent } from "./interactions";

export interface InteractiveDotPlotExplorerProps {
  independentAssessment: boolean;
  onMathEvent?: (event: MathInteractionEvent) => void;
}
export function InteractiveDotPlotExplorer(props: InteractiveDotPlotExplorerProps) {
  if (props.independentAssessment !== false) return null;
  return <GuidedDotPlotExplorer {...props} />;
}
function GuidedDotPlotExplorer({ onMathEvent }: InteractiveDotPlotExplorerProps) {
  const id = useId();
  const [values, setValues] = useState([2, 3, 3, 4, 5]);
  const [selected, setSelected] = useState(4);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const model = datasetModel(values);
  const item = DOT_PRACTICE[index];
  const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50";
  function update(next: number[]) {
    datasetModel(next);
    setValues(next);
    if (selected >= next.length) setSelected(next.length - 1);
    onMathEvent?.({ schema_version: 1, type: "EXPLORER_DATASET_CHANGED", values: [...next] });
  }
  return <section aria-label="Guided dot plot exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: each dot is one observation</h3>
    <p>This separate synthetic example does not count toward mastery. Repeated values make a stack of dots.</p>
    <ProblemVisual spec={{ type: "dot_plot", data: values, min: 0, max: 12,
      aria_label: `Dot plot: ${values.join(", ")}. Each dot is one observation.` }} />
    <h3 className="font-semibold">Manipulate</h3>
    <label className="block" htmlFor={`${id}-selected`}>Observation to move</label>
    <select id={`${id}-selected`} className={control} value={selected} onChange={e => setSelected(Number(e.target.value))}>
      {values.map((value, i) => <option key={i} value={i}>Observation {i + 1}: {value}</option>)}
    </select>
    <label className="block" htmlFor={`${id}-value`}>Observation value: {values[selected]}</label>
    <input id={`${id}-value`} className={`w-full ${control}`} type="range" min={0} max={12} step={1} value={values[selected]}
      onChange={e => update(replaceObservation(values, selected, Number(e.target.value)))} />
    <p>Use arrow keys to move one unit. Try moving the largest observation to 12 and then back to 5.</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={control} disabled={values.length === 6} onClick={() => { if (values.length < 6) update([...values, values[selected]]); }}>Add another observation at this value</button>
      <button type="button" className={control} disabled={values.length === 1} onClick={() => { if (values.length > 1) update(values.filter((_, i) => i !== selected)); }}>Remove selected observation</button>
      <button type="button" className={control} onClick={() => { update([2, 3, 3, 4, 5]); setSelected(4); }}>Reset data</button>
    </div>
    <h3 className="font-semibold">Explain</h3>
    <p role="status" aria-live="polite" aria-atomic="true">Count {model.count}; total {model.sum}; mean {formatRational(model.mean)}; median {formatRational(model.median)}; range {model.range}.</p>
    <p>Ordered observations: {model.sorted.join(", ")}. Mean is total ÷ count. Median is the middle after sorting, or the mean of the two middle observations for an even count. Range is largest minus smallest.</p>
    <p>Moving a largest observation farther right changes the mean. With at least two observations, moving it beyond all the others also increases the range. The median can stay the same; it can also change if a middle observation changes. Compare what happens when you move a middle dot.</p>
    <table className="w-full text-left"><caption>Frequency table: count every dot</caption><thead><tr><th scope="col">Value</th><th scope="col">Frequency</th></tr></thead>
      <tbody>{model.frequencies.filter(row => row.count > 0).map(row => <tr key={row.value}><th scope="row">{row.value}</th><td>{row.count}</td></tr>)}</tbody></table>
    <h3 className="font-semibold">Practice</h3>
    <p>Separate practice {index + 1} of {DOT_PRACTICE.length}: find the {item.measure} of {item.values.join(", ")}. Use an exact fraction if needed.</p>
    <label className="block" htmlFor={`${id}-answer`}>Data practice answer</label>
    <input id={`${id}-answer`} className={control} value={answer} maxLength={10} aria-describedby={`${id}-feedback`}
      onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
    <div className="flex gap-2"><button type="button" className={control} onClick={() => setFeedback(checkDatasetAnswer(index, answer).feedback)}>Check data practice</button>
      <button type="button" className={control} onClick={() => { setIndex((index + 1) % DOT_PRACTICE.length); setAnswer(""); setFeedback(""); }}>Next data practice</button></div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
  </section>;
}
