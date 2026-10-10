import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import { checkIntegerPractice, INTEGER_PRACTICE, integerModel, integerPracticeIndexFromSeed, type IntegerOperation } from "./integerNumberLine";
import type { MathInteractionEvent } from "./interactions";

export interface InteractiveIntegerNumberLineProps {
  independentAssessment: boolean;
  seed?: number;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function InteractiveIntegerNumberLine(props: InteractiveIntegerNumberLineProps) {
  // Fail closed even for absent/malformed runtime mode values. Unmount all local state.
  if (props.independentAssessment !== false) return null;
  return <GuidedIntegerNumberLine {...props} />;
}

function GuidedIntegerNumberLine({ seed = 0, onMathEvent }: InteractiveIntegerNumberLineProps) {
  const id = useId();
  const [start, setStart] = useState(-2);
  const [operand, setOperand] = useState(-3);
  const [operation, setOperation] = useState<IntegerOperation>("subtract");
  const seededIndex = integerPracticeIndexFromSeed(seed);
  const [index, setIndex] = useState(seededIndex);
  const [previousSeed, setPreviousSeed] = useState(seed);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  if (previousSeed !== seed) {
    setPreviousSeed(seed);
    setIndex(seededIndex);
    setAnswer("");
    setFeedback("");
  }
  const model = integerModel(start, operand, operation);
  const practice = INTEGER_PRACTICE[index];
  const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600";
  function update(a: number, b: number, op: IntegerOperation) {
    const next = integerModel(a, b, op);
    setStart(a); setOperand(b); setOperation(op);
    onMathEvent?.({ schema_version: 1, type: "INTEGER_DISPLACEMENT_CHANGED",
      start: next.start, operand: next.operand, operation: next.operation,
      displacement: next.displacement, result: next.result });
  }
  return <section aria-label="Guided integer number line exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: signed movement</h3>
    <p>This separate guided example does not count toward mastery. Numbers increase to the right and decrease to the left.</p>
    <ProblemVisual spec={{ type: "number_line", a: start, b: model.displacement,
      result: model.result, min: Math.min(0, start, model.result) - 1,
      max: Math.max(0, start, model.result) + 1, aria_label: model.explanation }} />
    <h3 className="font-semibold">Manipulate</h3>
    <p>Use the arrow keys on each slider to move one unit at a time.</p>
    <label className="block" htmlFor={`${id}-start`}>Starting integer: {start}</label>
    <input className={`w-full ${control}`} id={`${id}-start`} type="range" min={-10} max={10} step={1}
      value={start} onChange={e => update(Number(e.target.value), operand, operation)} />
    <label className="block" htmlFor={`${id}-operation`}>Operation</label>
    <select id={`${id}-operation`} className={control} value={operation}
      onChange={e => update(start, operand, e.target.value === "add" ? "add" : "subtract")}>
      <option value="add">Add</option><option value="subtract">Subtract</option>
    </select>
    <label className="block" htmlFor={`${id}-operand`}>Second integer: {operand}</label>
    <input className={`w-full ${control}`} id={`${id}-operand`} type="range" min={-10} max={10} step={1}
      value={operand} onChange={e => update(start, Number(e.target.value), operation)} />
    <h3 className="font-semibold">Explain</h3>
    <p role="status" aria-live="polite" aria-atomic="true">{model.expression} = {model.result}. {model.explanation}</p>
    <p>Why does subtracting a negative move right? Compare adding a number with subtracting its opposite. The movements are equal.</p>
    <h3 className="font-semibold">Practice</h3>
    <p>Separate practice {index + 1} of {INTEGER_PRACTICE.length}: {integerModel(practice.start, practice.operand, practice.operation).expression} = ?</p>
    <label className="block" htmlFor={`${id}-answer`}>Your practice answer</label>
    <input id={`${id}-answer`} className={control} value={answer} maxLength={4}
      aria-describedby={`${id}-feedback`} onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
    <div className="flex gap-2">
      <button className={control} type="button" onClick={() => setFeedback(checkIntegerPractice(index, answer).feedback)}>Check practice</button>
      <button className={control} type="button" onClick={() => { setIndex((index + 1) % INTEGER_PRACTICE.length); setAnswer(""); setFeedback(""); }}>Next practice</button>
    </div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
  </section>;
}
