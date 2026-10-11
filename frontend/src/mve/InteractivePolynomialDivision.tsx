import { useId, useMemo, useState } from "react";
import type { MathInteractionEvent } from "./interactions";
import {
  CORRECT_COEFFICIENT_REASON,
  CORRECT_EXPONENT_REASON,
  diagnosePolynomialDivision,
  formatPolynomial,
  formatTerm,
  POLYNOMIAL_DIVISION_EXAMPLE,
  POLYNOMIAL_DIVISION_FRESH_EXIT,
  polynomialPracticeFeedback,
  quotientFor,
  reconstructionFor,
  type PolynomialDivisionReason,
  type PolynomialExponentReason,
} from "./polynomialDivision";

export interface InteractivePolynomialDivisionProps {
  independentAssessment: boolean;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

const CONTROL = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50";
const WRONG_COEFFICIENT_REASON: PolynomialDivisionReason = "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT";
const WRONG_EXPONENT_REASON: PolynomialExponentReason = "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT";

export function InteractivePolynomialDivision(props: InteractivePolynomialDivisionProps) {
  if (props.independentAssessment !== false) return null;
  return <GuidedPolynomialDivision {...props} />;
}

function GuidedPolynomialDivision({ onMathEvent }: InteractivePolynomialDivisionProps) {
  const id = useId();
  const [divided, setDivided] = useState<number[]>([]);
  const [coefficientReason, setCoefficientReason] = useState<PolynomialDivisionReason>(WRONG_COEFFICIENT_REASON);
  const [exponentReason, setExponentReason] = useState<PolynomialExponentReason>(WRONG_EXPONENT_REASON);
  const [domain, setDomain] = useState<("x" | "y")[]>([]);
  const [feedback, setFeedback] = useState("");
  const quotient = useMemo(() => quotientFor(POLYNOMIAL_DIVISION_EXAMPLE), []);
  const reconstruction = useMemo(() => reconstructionFor(POLYNOMIAL_DIVISION_EXAMPLE), []);
  const response = {
    divided_term_indexes: divided,
    coefficient_reason: coefficientReason,
    exponent_reason: exponentReason,
    domain_restrictions: domain,
  };
  const diagnosis = diagnosePolynomialDivision(response);

  function emit(nextDivided = divided, nextCoefficient = coefficientReason, nextExponent = exponentReason, nextDomain = domain) {
    onMathEvent?.({
      schema_version: 1,
      type: "POLYNOMIAL_DIVISION_MANIPULATED",
      divided_terms: nextDivided.length,
      coefficient_reason: nextCoefficient,
      exponent_reason: nextExponent,
      domain_x: nextDomain.includes("x"),
      domain_y: nextDomain.includes("y"),
    });
  }

  function toggleTerm(index: number) {
    const next = divided.includes(index) ? divided.filter((value) => value !== index) : [...divided, index].sort();
    setDivided(next);
    setFeedback("");
    emit(next);
  }

  function setReason(reason: PolynomialDivisionReason) {
    setCoefficientReason(reason);
    setFeedback("");
    emit(divided, reason);
  }

  function setExponent(reason: PolynomialExponentReason) {
    setExponentReason(reason);
    setFeedback("");
    emit(divided, coefficientReason, reason);
  }

  function toggleDomain(symbol: "x" | "y") {
    const next = domain.includes(symbol) ? domain.filter((value) => value !== symbol) : [...domain, symbol].sort() as ("x" | "y")[];
    setDomain(next);
    setFeedback("");
    emit(divided, coefficientReason, exponentReason, next);
  }

  function check() {
    setFeedback(polynomialPracticeFeedback(response).feedback);
  }

  return <section aria-label="Guided polynomial division exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: divide every grouped term by the same nonzero monomial</h3>
    <p>This review-only guided model does not count toward mastery. It uses the accepted draft evidence contract for term records, reasons, domain restrictions, and multiplication reconstruction.</p>
    <div className="rounded border p-3" role="img" aria-label={`Polynomial division model: ${formatPolynomial(POLYNOMIAL_DIVISION_EXAMPLE.dividend)} divided by ${formatTerm(POLYNOMIAL_DIVISION_EXAMPLE.divisor)}.`}>
      <p className="font-semibold">({formatPolynomial(POLYNOMIAL_DIVISION_EXAMPLE.dividend)}) / {formatTerm(POLYNOMIAL_DIVISION_EXAMPLE.divisor)}</p>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {POLYNOMIAL_DIVISION_EXAMPLE.dividend.map((term, index) => (
          <button key={index} type="button" className={`${CONTROL} text-left ${divided.includes(index) ? "bg-blue-50" : ""}`}
            aria-pressed={divided.includes(index)} onClick={() => toggleTerm(index)}>
            Term {index + 1}: {formatTerm(term)} / {formatTerm(POLYNOMIAL_DIVISION_EXAMPLE.divisor)}
            <span className="block text-sm">Quotient card: {divided.includes(index) ? formatTerm(quotient[index]) : "not divided yet"}</span>
          </button>
        ))}
      </div>
    </div>
    <h3 className="font-semibold">Manipulate</h3>
    <fieldset className="space-y-2">
      <legend className="font-medium">Coefficient reason</legend>
      <label className="block"><input type="radio" name={`${id}-coeff`} checked={coefficientReason === CORRECT_COEFFICIENT_REASON} onChange={() => setReason(CORRECT_COEFFICIENT_REASON)} /> Dividend coefficient divided by divisor coefficient</label>
      <label className="block"><input type="radio" name={`${id}-coeff`} checked={coefficientReason === WRONG_COEFFICIENT_REASON} onChange={() => setReason(WRONG_COEFFICIENT_REASON)} /> Divisor coefficient divided by dividend coefficient</label>
    </fieldset>
    <fieldset className="space-y-2">
      <legend className="font-medium">Exponent reason</legend>
      <label className="block"><input type="radio" name={`${id}-exp`} checked={exponentReason === CORRECT_EXPONENT_REASON} onChange={() => setExponent(CORRECT_EXPONENT_REASON)} /> Dividend exponent minus divisor exponent</label>
      <label className="block"><input type="radio" name={`${id}-exp`} checked={exponentReason === WRONG_EXPONENT_REASON} onChange={() => setExponent(WRONG_EXPONENT_REASON)} /> Dividend exponent plus divisor exponent</label>
    </fieldset>
    <fieldset className="space-y-2">
      <legend className="font-medium">Original divisor restrictions</legend>
      <label className="mr-4"><input type="checkbox" checked={domain.includes("x")} onChange={() => toggleDomain("x")} /> x not equal to 0</label>
      <label><input type="checkbox" checked={domain.includes("y")} onChange={() => toggleDomain("y")} /> y not equal to 0</label>
    </fieldset>
    <h3 className="font-semibold">Explain</h3>
    <p role="status" aria-live="polite" aria-atomic="true">Current diagnosis: {diagnosis.replaceAll("_", " ")}.</p>
    <ol className="list-decimal pl-6" aria-label="Multiplication reconstruction">
      {reconstruction.map((record, index) => (
        <li key={index}>{formatTerm(record.quotient_term)} times {formatTerm(record.divisor_term)} reconstructs {formatTerm(record.product_term)}</li>
      ))}
    </ol>
    <h3 className="font-semibold">Practice</h3>
    <p>Check when every term card is divided, the correct reasons are selected, and the original nonzero restrictions are preserved.</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={CONTROL} onClick={check}>Check polynomial division</button>
      <button type="button" className={CONTROL} onClick={() => { setDivided([]); setCoefficientReason(WRONG_COEFFICIENT_REASON); setExponentReason(WRONG_EXPONENT_REASON); setDomain([]); setFeedback(""); }}>Reset guided attempt</button>
    </div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
    <h3 className="font-semibold">Transfer</h3>
    <p>Fresh exit preview: ({formatPolynomial(POLYNOMIAL_DIVISION_FRESH_EXIT.dividend)}) / {formatTerm(POLYNOMIAL_DIVISION_FRESH_EXIT.divisor)} produces negative exponents, so students must still subtract exponent counts rather than add them.</p>
  </section>;
}
