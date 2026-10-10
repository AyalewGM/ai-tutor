import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import { applyBalanceOperation, BALANCE_EXAMPLES, BALANCE_LABELS, BALANCE_OPERATIONS, BALANCE_PRACTICE,
  balanceExpression, checkBalanceAnswer, isIsolated, type BalanceEquation, type BalanceOperation } from "./equationBalance";
import type { MathInteractionEvent } from "./interactions";

export interface InteractiveEquationBalanceProps {
  independentAssessment: boolean;
  onMathEvent?: (event: MathInteractionEvent) => void;
}
export function InteractiveEquationBalance(props: InteractiveEquationBalanceProps) {
  if (props.independentAssessment !== false) return null;
  return <GuidedEquationBalance {...props} />;
}
function GuidedEquationBalance({ onMathEvent }: InteractiveEquationBalanceProps) {
  const id = useId();
  const [example, setExample] = useState(0);
  const [history, setHistory] = useState<Array<{ equation: BalanceEquation; operation: BalanceOperation }>>([]);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const equation = history[history.length - 1]?.equation ?? BALANCE_EXAMPLES[example];
  const expression = balanceExpression(equation);
  const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50";
  function apply(operation: BalanceOperation) {
    const next = applyBalanceOperation(equation, operation);
    if (!next || history.length >= 30) return;
    setHistory([...history, { equation: next, operation }]);
    onMathEvent?.({ schema_version: 1, type: "BALANCE_OPERATION_APPLIED", operation,
      left_x: equation.left.x_count, left_units: equation.left.units,
      right_x: equation.right.x_count, right_units: equation.right.units });
  }
  return <section aria-label="Guided equation balance exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: equality is a balance</h3>
    <p>Each x-box stands for the same unknown amount. Each small tile is 1. This separate example does not count toward mastery.</p>
    <ProblemVisual spec={{ type: "balance_scale", left: equation.left, right: equation.right,
      aria_label: `Balanced equation: ${expression}. Equal operations on both sides preserve the solution.` }} />
    <p role="status" aria-live="polite" aria-atomic="true">{expression}. {isIsolated(equation) ? "x is isolated. Substitute this value in the original equation to check it." : "Keep both sides equal while isolating x."}</p>
    <h3 className="font-semibold">Manipulate</h3>
    <p id={`${id}-bounds`}>This concrete model uses whole tiles only: 0–3 x-boxes and 0–12 unit tiles per side. An unavailable operation would remove absent tiles, split tiles, or exceed these limits; it is not necessarily invalid in algebra.</p>
    <div className="flex flex-wrap gap-2">{BALANCE_OPERATIONS.map(operation => <button key={operation} type="button" className={control}
      aria-describedby={`${id}-bounds`} disabled={!applyBalanceOperation(equation, operation) || history.length >= 30}
      onClick={() => apply(operation)}>{BALANCE_LABELS[operation]}</button>)}</div>
    {history.length >= 30 && <p role="status">Step limit reached. Undo or reset to keep exploring.</p>}
    <div className="flex flex-wrap gap-2">
      <button type="button" className={control} disabled={!history.length} onClick={() => setHistory(history.slice(0, -1))}>Undo balance step</button>
      <button type="button" className={control} disabled={!history.length} onClick={() => setHistory([])}>Reset balance</button>
      <button type="button" className={control} onClick={() => { setExample((example + 1) % BALANCE_EXAMPLES.length); setHistory([]); }}>Next balance example</button>
    </div>
    <h3 className="font-semibold">Explain</h3>
    <p>Adding or subtracting the same quantity on both sides preserves equality. Dividing both sides by the same nonzero number preserves it too. Why would changing just one side break the balance?</p>
    <ol aria-label="Balance step history" className="list-decimal pl-6">
      <li>{balanceExpression(BALANCE_EXAMPLES[example])}</li>
      {history.map((step, i) => <li key={i}>{BALANCE_LABELS[step.operation]}: {balanceExpression(step.equation)}</li>)}
    </ol>
    <h3 className="font-semibold">Practice</h3>
    <p>Separate practice {index + 1} of {BALANCE_PRACTICE.length}: solve {balanceExpression(BALANCE_PRACTICE[index])}. Your answer may be a fraction, even though the concrete explorer uses whole tiles.</p>
    <label className="block" htmlFor={`${id}-answer`}>Value of x</label>
    <input id={`${id}-answer`} className={control} maxLength={10} value={answer} aria-describedby={`${id}-feedback`}
      onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
    <div className="flex gap-2"><button type="button" className={control} onClick={() => setFeedback(checkBalanceAnswer(index, answer).feedback)}>Check equation</button>
      <button type="button" className={control} onClick={() => { setIndex((index + 1) % BALANCE_PRACTICE.length); setAnswer(""); setFeedback(""); }}>Next equation practice</button></div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
  </section>;
}
