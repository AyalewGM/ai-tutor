import { useId, useState } from "react";
import {
  applyEquationOperation,
  equationSolution,
  EQUATION_EQUIVALENCE_EXAMPLES,
  formatAffineEquation,
  formatAffineSide,
  formatEquationOperation,
  isEquationIsolated,
  nextEquationMoves,
  type AffineEquation,
  type EquationOperation,
} from "./equationEquivalence";
import type { EquationTransformationAppliedEvent, MathInteractionEvent } from "./interactions";

export interface InteractiveEquationEquivalenceProps {
  independentAssessment?: boolean;
  exampleIndex?: number;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function InteractiveEquationEquivalence(props: InteractiveEquationEquivalenceProps) {
  if (props.independentAssessment !== false) return null;
  const exampleIndex = props.exampleIndex ?? 0;
  if (!Number.isInteger(exampleIndex) || exampleIndex < 0 || exampleIndex >= EQUATION_EQUIVALENCE_EXAMPLES.length) return null;
  return <GuidedEquationEquivalence key={`equation-equivalence-${exampleIndex}`} {...props} exampleIndex={exampleIndex} />;
}

function operationEvent(operation: EquationOperation): EquationTransformationAppliedEvent {
  return {
    schema_version: 1,
    type: "EQUATION_TRANSFORMATION_APPLIED",
    operation: operation.kind === "add_constant" ? "ADD_CONSTANT_BOTH" :
      operation.kind === "add_variable" ? "ADD_VARIABLE_BOTH" : "SCALE_BOTH",
    amount_numerator: operation.amount.numerator,
    amount_denominator: operation.amount.denominator,
    preserved: true,
  };
}

function GuidedEquationEquivalence({ exampleIndex = 0, onMathEvent }: InteractiveEquationEquivalenceProps) {
  const id = useId();
  const original = EQUATION_EQUIVALENCE_EXAMPLES[exampleIndex];
  const [equation, setEquation] = useState<AffineEquation>(original);
  const [history, setHistory] = useState<Array<{ before: AffineEquation; after: AffineEquation; operation: EquationOperation }>>([]);
  const [announcement, setAnnouncement] = useState(`Starting equation: ${formatAffineEquation(original)}.`);
  const [prediction, setPrediction] = useState<"positive" | "negative" | "zero" | null>(null);
  const [predictionFeedback, setPredictionFeedback] = useState("");
  const [explanationFeedback, setExplanationFeedback] = useState("");
  const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 motion-reduce:transition-none";
  const moves = nextEquationMoves(equation);

  function apply(operation: EquationOperation) {
    const next = applyEquationOperation(equation, operation);
    if (!next || history.length >= 6) return;
    const beforeText = formatAffineEquation(equation);
    const afterText = formatAffineEquation(next);
    setEquation(next);
    setHistory([...history, { before: equation, after: next, operation }]);
    setAnnouncement(`${beforeText}. ${formatEquationOperation(operation)}. Result: ${afterText}. Equality and the solution set are preserved.`);
    onMathEvent?.(operationEvent(operation));
  }

  function predict(sign: "positive" | "negative" | "zero") {
    setPrediction(sign);
    const solution = equationSolution(original);
    const expected = solution.numerator === 0 ? "zero" : solution.numerator < 0 ? "negative" : "positive";
    setPredictionFeedback(sign === expected
      ? "That sign is consistent with the equation. Now preserve equality as you isolate x."
      : "Recheck the signs and relative sizes on the two sides; keep the exact value hidden while you revise.");
  }

  function rejectOneSidedChange() {
    setAnnouncement(`No change made. Changing only one side would produce a false equivalence, so ${formatAffineEquation(equation)} remains unchanged.`);
  }

  function reset() {
    setEquation(original);
    setHistory([]);
    setPrediction(null);
    setPredictionFeedback("");
    setExplanationFeedback("");
    setAnnouncement(`Reset to the starting equation: ${formatAffineEquation(original)}.`);
  }

  return <section aria-label="Guided exact equation equivalence exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: equivalent equations keep the same solution</h3>
    <p>This is a separate guided example and does not count toward mastery. Read each side before choosing an operation.</p>
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 rounded border p-4 text-center text-lg" role="img"
      aria-label={`Equation balance. Left side ${formatAffineSide(equation.left)}. Right side ${formatAffineSide(equation.right)}. Both sides are equal.`}>
      <span>{formatAffineSide(equation.left)}</span><span aria-hidden="true">=</span><span>{formatAffineSide(equation.right)}</span>
    </div>
    <p role="status" aria-live="polite" aria-atomic="true">{announcement}</p>

    <h3 className="font-semibold">Predict</h3>
    <p id={`${id}-predict-prompt`}>Before solving, predict the sign of the solution. This check will not reveal its value.</p>
    <div className="flex flex-wrap gap-2" role="group" aria-describedby={`${id}-predict-prompt`}>
      {(["negative", "zero", "positive"] as const).map(sign => <button key={sign} type="button" className={control}
        aria-pressed={prediction === sign} onClick={() => predict(sign)}>{sign[0].toUpperCase() + sign.slice(1)}</button>)}
    </div>
    <p role="status" aria-live="polite">{predictionFeedback}</p>

    <h3 className="font-semibold">Manipulate: operate on both sides</h3>
    <p id={`${id}-rule`}>Apply the displayed operation to the entire left side and the entire right side. Scaling by zero is never allowed.</p>
    <div className="flex flex-wrap gap-2">
      {moves.map((operation, index) => <button key={`${operation.kind}-${index}`} type="button" className={control}
        aria-describedby={`${id}-rule`} onClick={() => apply(operation)}>{formatEquationOperation(operation)}</button>)}
      <button type="button" className={control} aria-describedby={`${id}-rule`} onClick={rejectOneSidedChange}>Try changing only one side</button>
      <button type="button" className={control} disabled={history.length === 0} onClick={reset}>Reset equation</button>
    </div>
    {isEquationIsolated(equation) && <p>Isolated. Substitute this value into the original left and right sides to verify equality.</p>}

    <table className="w-full border-collapse text-left">
      <caption className="font-semibold">Equivalent-equation transformation table</caption>
      <thead><tr><th scope="col">Step</th><th scope="col">Operation</th><th scope="col">Left before</th><th scope="col">Right before</th><th scope="col">Left after</th><th scope="col">Right after</th><th scope="col">Preserved?</th></tr></thead>
      <tbody>
        <tr><th scope="row">0</th><td>Start</td><td>{formatAffineSide(original.left)}</td><td>{formatAffineSide(original.right)}</td><td>—</td><td>—</td><td>Yes</td></tr>
        {history.map((step, index) => <tr key={index}><th scope="row">{index + 1}</th><td>{formatEquationOperation(step.operation)}</td>
          <td>{formatAffineSide(step.before.left)}</td><td>{formatAffineSide(step.before.right)}</td>
          <td>{formatAffineSide(step.after.left)}</td><td>{formatAffineSide(step.after.right)}</td><td>Yes</td></tr>)}
      </tbody>
    </table>

    <h3 className="font-semibold">Explain</h3>
    <p>Which statement justifies every accepted transformation?</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={control} onClick={() => setExplanationFeedback("Yes. Applying the same addition or nonzero scale to both complete sides preserves exactly the same solutions.")}>The same valid operation was applied to both complete sides</button>
      <button type="button" className={control} onClick={() => setExplanationFeedback("Not quite. A term does not simply move; adding its opposite to both sides is the equality-preserving action.")}>A term moved across the equals sign</button>
    </div>
    <p id={`${id}-explain-feedback`} role="status" aria-live="polite">{explanationFeedback}</p>
  </section>;
}
