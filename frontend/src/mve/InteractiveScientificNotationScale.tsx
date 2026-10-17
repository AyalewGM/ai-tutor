import { useId, useState } from "react";
import type { MathInteractionEvent } from "./interactions";
import {
  evaluateScaleReasoning,
  evaluateScientificTransfer,
  formatScaleCoefficient,
  formatScaleExpression,
  formatScaleOrdinaryValue,
  initialScientificScaleState,
  isNormalizedScientificState,
  movePowerOfTen,
  scientificScaleExampleFromSeed,
  type ScaleExplanation,
  type ScalePrediction,
  type ScientificScaleState,
} from "./scientificNotationScale";

export interface InteractiveScientificNotationScaleProps {
  independentAssessment: boolean;
  seed?: number;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

const CONTROL = "rounded border p-2 transition-colors motion-reduce:transition-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50";

export function InteractiveScientificNotationScale(props: InteractiveScientificNotationScaleProps) {
  const seed = props.seed ?? 0;
  if (props.independentAssessment !== false || !Number.isSafeInteger(seed) || seed < 0) return null;
  return <GuidedScientificNotationScale key={seed} {...props} seed={seed} />;
}

function GuidedScientificNotationScale({ seed = 0, onMathEvent }: InteractiveScientificNotationScaleProps) {
  const id = useId();
  const example = scientificScaleExampleFromSeed(seed);
  const transfer = scientificScaleExampleFromSeed(seed + 1);
  const [state, setState] = useState<ScientificScaleState>(() => initialScientificScaleState(example));
  const [predictionLocked, setPredictionLocked] = useState(false);
  const [manipulated, setManipulated] = useState(false);
  const [reasoningVerified, setReasoningVerified] = useState(false);
  const [prediction, setPrediction] = useState<ScalePrediction>("");
  const [explanation, setExplanation] = useState<ScaleExplanation>("");
  const [reflection, setReflection] = useState("");
  const [feedback, setFeedback] = useState("Predict the inverse scale relationship before manipulating.");
  const [transferCoefficient, setTransferCoefficient] = useState("");
  const [transferExponent, setTransferExponent] = useState("");
  const [transferFeedback, setTransferFeedback] = useState("");

  function update(direction: "COEFFICIENT_DIVIDE_BY_TEN" | "COEFFICIENT_MULTIPLY_BY_TEN") {
    if (!predictionLocked) return;
    try {
      const next = movePowerOfTen(state, direction);
      setState(next);
      setManipulated(true);
      setReasoningVerified(false);
      setTransferFeedback("");
      setFeedback("Scale changed. The coefficient and power moved inversely, so the exact value stayed fixed.");
      onMathEvent?.({
        schema_version: 1,
        type: "SCIENTIFIC_NOTATION_SCALE_CHANGED",
        significant_digits: next.significant_digits,
        coefficient_power: next.coefficient_power,
        exponent: next.exponent,
        invariant_power: next.invariant_power,
      });
    } catch {
      setFeedback("That move would leave the bounded exponent scale. Reverse direction or reset.");
    }
  }

  function reset() {
    setState(initialScientificScaleState(example));
    setPredictionLocked(false);
    setManipulated(false);
    setReasoningVerified(false);
    setPrediction("");
    setExplanation("");
    setReflection("");
    setFeedback("Predict the inverse scale relationship before manipulating.");
    setTransferCoefficient("");
    setTransferExponent("");
    setTransferFeedback("");
  }

  const scaleValues = Array.from({ length: 17 }, (_, index) => index - 8);

  return <section aria-label="Guided scientific notation exponent scale" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: one value, two inverse scales</h3>
    <p>This draft guided model does not count toward mastery. It covers positive, nonzero exact values without rounding.</p>
    <p role="img" aria-label={`Starting value ${formatScaleOrdinaryValue(example)} represented as ${formatScaleExpression(state)}.`}>
      Starting value: <strong>{formatScaleOrdinaryValue(example)}</strong>
    </p>

    <h3 className="font-semibold">Predict</h3>
    <label className="block" htmlFor={`${id}-prediction`}>If the coefficient is divided by 10, what must happen to the exponent?</label>
    <select id={`${id}-prediction`} className={CONTROL} value={prediction} disabled={predictionLocked}
      onChange={(event) => { if (predictionLocked) return; setPrediction(event.target.value as ScalePrediction); setFeedback(""); }}>
      <option value="">Choose a relationship</option>
      <option value="INVERSE_CHANGES_PRESERVE_VALUE">Increase the exponent by 1 so the value stays fixed</option>
      <option value="SAME_DIRECTION_PRESERVES_VALUE">Decrease the exponent by 1 with the coefficient</option>
    </select>

    <button type="button" className={CONTROL} disabled={!prediction || predictionLocked}
      onClick={() => { if (!prediction || predictionLocked) return; setPredictionLocked(true); setFeedback("Prediction recorded. Now manipulate and compare the result with your prediction. Reset to make a new prediction."); }}>Record prediction</button>

    <h3 className="font-semibold">Manipulate: shift one factor of ten</h3>
    <p>Use either button with a keyboard or pointer. Normalize the coefficient while keeping the starting value unchanged.</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={CONTROL} disabled={!predictionLocked} onClick={() => update("COEFFICIENT_DIVIDE_BY_TEN")}>Divide coefficient by 10; increase exponent</button>
      <button type="button" className={CONTROL} disabled={!predictionLocked} onClick={() => update("COEFFICIENT_MULTIPLY_BY_TEN")}>Multiply coefficient by 10; decrease exponent</button>
      <button type="button" className={CONTROL} onClick={reset}>Reset this scale</button>
    </div>
    <div hidden={reasoningVerified}>
    <p className="text-lg" aria-live="polite" aria-atomic="true">Current exact form: {formatScaleExpression(state)}. Coefficient {isNormalizedScientificState(state) ? "is normalized" : "is not normalized"}.</p>
    <ol aria-label="Power-of-ten exponent scale" className="grid grid-cols-5 gap-1 sm:grid-cols-9">
      {scaleValues.map((value) => <li key={value} aria-current={value === state.exponent ? "step" : undefined}
        className={`rounded border p-1 text-center motion-reduce:transition-none ${value === state.exponent ? "border-blue-700 bg-blue-100 font-semibold" : ""}`}>
        10^{value}
      </li>)}
    </ol>
    <table className="w-full text-left">
      <caption>Nonvisual equivalent state</caption>
      <thead><tr><th scope="col">Coefficient</th><th scope="col">Power of ten</th><th scope="col">Ordinary value</th></tr></thead>
      <tbody><tr><td>{formatScaleCoefficient(state.significant_digits, state.coefficient_power)}</td><td>10^{state.exponent}</td><td>{formatScaleOrdinaryValue(example)}</td></tr></tbody>
    </table>
    </div>
    {reasoningVerified && <p role="status">Your prediction and explanation preserved the exact value. The worked scale is hidden; try the fresh transfer without it.</p>}

    <h3 className="font-semibold">Explain</h3>
    <label className="block" htmlFor={`${id}-evidence`}>Mathematical explanation evidence</label>
    <select id={`${id}-evidence`} className={CONTROL} value={explanation}
      onChange={(event) => { setExplanation(event.target.value as ScaleExplanation); setReasoningVerified(false); setTransferFeedback(""); setFeedback(""); }}>
      <option value="">Choose evidence</option>
      <option value="COEFFICIENT_AND_POWER_ARE_INVERSE_FACTORS">A factor of 10 moved from one factor to the other, preserving the product</option>
      <option value="DECIMAL_MOVES_WITHOUT_POWER_CHANGE">The decimal point moves without changing the power of ten</option>
    </select>
    <label className="block" htmlFor={`${id}-reflection`}>Explain the inverse relationship in your own words (reflection only)</label>
    <textarea id={`${id}-reflection`} className={`${CONTROL} block w-full`} rows={2} value={reflection}
      onChange={(event) => setReflection(event.target.value)} />
    <button type="button" className={CONTROL} disabled={!predictionLocked || !manipulated} onClick={() => {
      if (!predictionLocked || !manipulated) return;
      const result = evaluateScaleReasoning(state, prediction, explanation);
      setReasoningVerified(result.correct);
      setFeedback(result.feedback + (prediction === "SAME_DIRECTION_PRESERVES_VALUE" ? " Compare your recorded prediction with the scale; reset to predict again before another exploration." : ""));
    }}>Check guided reasoning</button>
    <p id={`${id}-feedback`} role="status" aria-live="polite" aria-atomic="true">{feedback}</p>

    <h3 className="font-semibold">Transfer and verify</h3>
    <p>Write {formatScaleOrdinaryValue(transfer)} in normalized scientific notation. No answer card is shown.</p>
    <fieldset disabled={!reasoningVerified} className="flex flex-wrap gap-2">
      <legend>Fresh transfer — unlock by verifying guided reasoning</legend>
      <label htmlFor={`${id}-transfer-coefficient`}>Coefficient</label>
      <input id={`${id}-transfer-coefficient`} className={CONTROL} inputMode="decimal" maxLength={12} value={transferCoefficient}
        onChange={(event) => { setTransferCoefficient(event.target.value); setTransferFeedback(""); }} />
      <label htmlFor={`${id}-transfer-exponent`}>Exponent</label>
      <input id={`${id}-transfer-exponent`} className={CONTROL} inputMode="numeric" maxLength={3} value={transferExponent}
        onChange={(event) => { setTransferExponent(event.target.value); setTransferFeedback(""); }} />
      <button type="button" className={CONTROL} onClick={() => { if (!reasoningVerified) return; setTransferFeedback(evaluateScientificTransfer(transfer, transferCoefficient, transferExponent).feedback); }}>Verify fresh transfer</button>
    </fieldset>
    <p role="status" aria-live="polite" aria-atomic="true">{transferFeedback}</p>
  </section>;
}
