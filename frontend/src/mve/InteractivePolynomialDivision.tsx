import { useId, useState } from "react";
import {
  diagnosePolynomialDivisionAttempt,
  dividePolynomialTerm,
  formatPolynomial,
  formatPolynomialTerm,
  freshPolynomialDivisionVariant,
  multiplyPolynomialTerms,
  polynomialDivisionVariant,
  quotientTerms,
  reconstructsDividend,
  samePolynomialTerm,
  type PolynomialDivisionMisconception,
  type PolynomialDivisionVariant,
} from "./polynomialDivision";
import type { MathInteractionEvent } from "./interactions";

export interface InteractivePolynomialDivisionProps {
  independentAssessment?: boolean;
  seed?: number;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function InteractivePolynomialDivision(props: InteractivePolynomialDivisionProps) {
  if (props.independentAssessment !== false) return null;
  const seed = props.seed ?? 0;
  let variant;
  try {
    variant = polynomialDivisionVariant(seed);
  } catch {
    return null;
  }
  return <GuidedPolynomialDivision key={`polynomial-division-${seed}`} {...props} seed={seed} initialVariant={variant} />;
}

function GuidedPolynomialDivision({ seed = 0, initialVariant, onMathEvent }: InteractivePolynomialDivisionProps & {
  initialVariant: PolynomialDivisionVariant;
}) {
  const id = useId();
  const [variant, setVariant] = useState(initialVariant);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [processed, setProcessed] = useState<number[]>([]);
  const [prediction, setPrediction] = useState<"positive" | "negative" | null>(null);
  const [coefficientReason, setCoefficientReason] = useState<"DIVIDEND_BY_DIVISOR" | "DIVISOR_BY_DIVIDEND" | null>(null);
  const [exponentReason, setExponentReason] = useState<"SUBTRACT" | "ADD" | null>(null);
  const [restrictions, setRestrictions] = useState<Array<"x" | "y">>([]);
  const [reconstructionConfirmed, setReconstructionConfirmed] = useState(false);
  const [diagnosis, setDiagnosis] = useState<PolynomialDivisionMisconception | null>(null);
  const [freshRepair, setFreshRepair] = useState(false);
  const [supportStage, setSupportStage] = useState<"MODELED" | "COACHED" | "INDEPENDENT_READINESS">("MODELED");
  const [feedback, setFeedback] = useState("Select each grouped term and apply the shared divisor.");
  const [transferVerified, setTransferVerified] = useState(false);
  const quotients = quotientTerms(variant);
  const control = "rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 motion-reduce:transition-none disabled:opacity-50";

  function expectedSign(index: number) {
    return dividePolynomialTerm(variant.dividend[index], variant.divisor).coefficient.numerator < 0 ? "negative" : "positive";
  }

  function divideSelected() {
    const quotient = dividePolynomialTerm(variant.dividend[selectedIndex], variant.divisor);
    setProcessed(current => [...new Set([...current, selectedIndex])].sort((a, b) => a - b));
    setReconstructionConfirmed(false);
    setFeedback(`Term ${selectedIndex + 1} becomes ${formatPolynomialTerm(quotient)}. Keep the original divisor restrictions visible.`);
    onMathEvent?.({
      schema_version: 1,
      type: "POLYNOMIAL_TERM_DIVIDED",
      term_index: selectedIndex,
      dividend: variant.dividend[selectedIndex],
      divisor: variant.divisor,
      quotient,
    });
  }

  function toggleRestriction(symbol: "x" | "y") {
    setRestrictions(current => current.includes(symbol) ? current.filter(item => item !== symbol) : [...current, symbol].sort());
    setReconstructionConfirmed(false);
  }

  function verifyReconstruction() {
    const reconstructed = processed.length === variant.dividend.length &&
      reconstructsDividend(variant, quotients) && quotients.every((quotient, index) =>
        samePolynomialTerm(multiplyPolynomialTerms(quotient, variant.divisor), variant.dividend[index]));
    setReconstructionConfirmed(reconstructed);
    setTransferVerified(reconstructed);
    setFeedback(reconstructed
      ? "Every quotient term multiplied by the shared divisor reconstructs its original area term."
      : "Divide every grouped term before checking the reconstruction.");
  }

  function checkReasoning() {
    const result = diagnosePolynomialDivisionAttempt(variant, {
      processedTermIndexes: processed,
      coefficientReason,
      exponentReason,
      restrictions,
      reconstructionConfirmed,
    });
    if (result === null) {
      setDiagnosis(null);
      setSupportStage(freshRepair ? "INDEPENDENT_READINESS" : "COACHED");
      setFeedback(freshRepair
        ? "Fresh repair complete. Your factor rules and multiplication reconstruction are consistent."
        : "The termwise division, restrictions, and reconstruction are consistent. Try the transfer and fresh verification next.");
      return;
    }
    if (result === "UNCLASSIFIED_FOR_HUMAN_REVIEW") {
      setFeedback("Complete both rule choices and verify by multiplication before checking again.");
      return;
    }
    setDiagnosis(result);
    setSupportStage("MODELED");
    setFeedback(result === "POLY.DIV.ONE_TERM_ONLY"
      ? "The divisor applies to every term inside the grouping. Which term has not yet been processed?"
      : result === "POLY.DIV.COEFFICIENT_RECIPROCAL"
        ? "Which coefficient is the dividend, and what factor multiplied by the divisor would reconstruct it?"
        : result === "POLY.DIV.ADD_EXPONENTS"
          ? "Count the like-base factors that cancel. Which operation records how many remain?"
          : "Cancellation cannot restore a value that made the original divisor zero. Which restriction must travel with the result?");
    onMathEvent?.({ schema_version: 1, type: "POLYNOMIAL_DIVISION_DIAGNOSED", diagnosis: result, phase: "DIAGNOSE" });
  }

  function beginFreshRepair() {
    if (!diagnosis) return;
    const fresh = freshPolynomialDivisionVariant(seed, diagnosis);
    setVariant(fresh);
    setSelectedIndex(0);
    setProcessed([]);
    setPrediction(null);
    setCoefficientReason(null);
    setExponentReason(null);
    setRestrictions([]);
    setReconstructionConfirmed(false);
    setTransferVerified(false);
    setFreshRepair(true);
    setDiagnosis(null);
    setSupportStage("COACHED");
    setFeedback("Fresh related example loaded. Rebuild the evidence without using the previous quotient.");
  }

  const expression = `(${formatPolynomial(variant.dividend)}) ÷ ${formatPolynomialTerm(variant.divisor)}`;

  return <section aria-label="Guided grouped polynomial division exploration" data-mve-family="polynomial-division"
    data-reduced-motion="discrete-states" className="space-y-4 rounded-lg border p-4 motion-reduce:scroll-auto">
    <h3 className="font-semibold">Observe: one divisor applies to every grouped term</h3>
    <p>This guided exploration is separate from independent assessment and cannot award mastery.</p>
    <p className="text-lg font-medium" aria-label={`Expression ${expression}`}>{expression}</p>
    <p><strong>Support stage:</strong> {supportStage.replace("_", " ")}</p>

    <h3 className="font-semibold">Predict</h3>
    <p id={`${id}-prediction`}>Predict the sign of the selected term's quotient before revealing its exact form.</p>
    <div role="group" aria-describedby={`${id}-prediction`} className="flex gap-2">
      {(["positive", "negative"] as const).map(sign => <button key={sign} type="button" className={control}
        aria-pressed={prediction === sign} onClick={() => {
          setPrediction(sign);
          setFeedback(sign === expectedSign(selectedIndex)
            ? "That sign is consistent. Now apply the shared divisor."
            : "Recheck the dividend and divisor signs; the exact quotient remains hidden.");
        }}>{sign[0].toUpperCase() + sign.slice(1)}</button>)}
    </div>

    <h3 className="font-semibold">Manipulate grouped terms</h3>
    <p id={`${id}-term-help`}>Use Previous and Next to move through terms, then divide the selected term. Every action is keyboard-operable.</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={control} disabled={selectedIndex === 0}
        onClick={() => { setSelectedIndex(value => value - 1); setPrediction(null); }}>Previous term</button>
      <button type="button" className={control} disabled={selectedIndex === variant.dividend.length - 1}
        onClick={() => { setSelectedIndex(value => value + 1); setPrediction(null); }}>Next term</button>
      <button type="button" className={control} aria-describedby={`${id}-term-help`} onClick={divideSelected}>
        Divide selected term by shared divisor
      </button>
    </div>
    <table className="w-full border-collapse text-left">
      <caption className="sr-only">Grouped-term polynomial division state</caption>
      <thead><tr><th scope="col">Term</th><th scope="col">Dividend term</th><th scope="col">Shared divisor</th><th scope="col">Quotient state</th></tr></thead>
      <tbody>{variant.dividend.map((dividend, index) => <tr key={`${variant.id}-${index}`} aria-current={index === selectedIndex ? "true" : undefined}>
        <th scope="row">{index + 1}{index === selectedIndex ? " (selected)" : ""}</th>
        <td>{formatPolynomialTerm(dividend)}</td>
        <td>{formatPolynomialTerm(variant.divisor)}</td>
        <td>{processed.includes(index) ? formatPolynomialTerm(quotients[index]) : "Not divided yet"}</td>
      </tr>)}</tbody>
    </table>

    <h3 className="font-semibold">Explain the factor rules</h3>
    <fieldset className="space-y-2">
      <legend>How should the coefficients be divided?</legend>
      <label className="block"><input type="radio" name={`${id}-coefficient`} checked={coefficientReason === "DIVIDEND_BY_DIVISOR"}
        onChange={() => { setCoefficientReason("DIVIDEND_BY_DIVISOR"); setReconstructionConfirmed(false); }} /> Dividend coefficient ÷ divisor coefficient</label>
      <label className="block"><input type="radio" name={`${id}-coefficient`} checked={coefficientReason === "DIVISOR_BY_DIVIDEND"}
        onChange={() => { setCoefficientReason("DIVISOR_BY_DIVIDEND"); setReconstructionConfirmed(false); }} /> Divisor coefficient ÷ dividend coefficient</label>
    </fieldset>
    <fieldset className="space-y-2">
      <legend>For like bases, how do exponents change during division?</legend>
      <label className="block"><input type="radio" name={`${id}-exponent`} checked={exponentReason === "SUBTRACT"}
        onChange={() => { setExponentReason("SUBTRACT"); setReconstructionConfirmed(false); }} /> Subtract divisor exponent from dividend exponent</label>
      <label className="block"><input type="radio" name={`${id}-exponent`} checked={exponentReason === "ADD"}
        onChange={() => { setExponentReason("ADD"); setReconstructionConfirmed(false); }} /> Add the exponents</label>
    </fieldset>
    <fieldset className="space-y-2">
      <legend>Which variables must stay nonzero because of the original divisor?</legend>
      {(["x", "y"] as const).map(symbol => <label className="mr-4 inline-block" key={symbol}>
        <input type="checkbox" checked={restrictions.includes(symbol)} onChange={() => toggleRestriction(symbol)} /> {symbol} ≠ 0
      </label>)}
    </fieldset>

    <h3 className="font-semibold">Transfer and verify by multiplication</h3>
    <p>Interpret the shared divisor as a rectangle height and the grouped dividend terms as areas. Recover each width, then multiply each width by the height.</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={control} onClick={verifyReconstruction}>Verify reconstructed areas</button>
      <button type="button" className={control} onClick={checkReasoning}>Check my reasoning</button>
      {diagnosis && <button type="button" className={control} onClick={beginFreshRepair}>Try a fresh related example</button>}
    </div>
    <p><strong>Reconstruction state:</strong> {transferVerified ? "Every quotient term reconstructs its original dividend term." : "Not yet verified."}</p>
    <p id={`${id}-feedback`} role="status" aria-live="polite" aria-atomic="true">{feedback}</p>
  </section>;
}
