import { useId, useState } from "react";
import type { MathInteractionEvent } from "./interactions";
import {
  CORRECT_COEFFICIENT_REASON,
  CORRECT_EXPONENT_REASON,
  evaluateSocraticRepair,
  evaluateLearnerPolynomialAttempt,
  formatPolynomial,
  formatTerm,
  POLYNOMIAL_DIVISION_EXAMPLE,
  POLYNOMIAL_DIVISION_FRESH_EXIT,
  POLYNOMIAL_DIVISION_REPAIR_EXIT,
  socraticRepairFor,
  type LearnerReconstructionRecord,
  type LearnerTermRecord,
  type PolynomialDivisionReason,
  type PolynomialExponentReason,
} from "./polynomialDivision";

export interface InteractivePolynomialDivisionProps {
  independentAssessment: boolean;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

const CONTROL = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50";
const INPUT = "w-20 rounded border p-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600";
const WRONG_COEFFICIENT_REASON: PolynomialDivisionReason = "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT";
const WRONG_EXPONENT_REASON: PolynomialExponentReason = "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT";
const BLANK_TERM: LearnerTermRecord = { coefficient: "", x_exponent: "", y_exponent: "" };
const BLANK_RECONSTRUCTION: LearnerReconstructionRecord = { product_coefficient: "", product_x_exponent: "", product_y_exponent: "" };

export function InteractivePolynomialDivision(props: InteractivePolynomialDivisionProps) {
  if (props.independentAssessment !== false) return null;
  return <GuidedPolynomialDivision {...props} />;
}

function GuidedPolynomialDivision({ onMathEvent }: InteractivePolynomialDivisionProps) {
  const id = useId();
  const [divided, setDivided] = useState<number[]>([]);
  const [prediction, setPrediction] = useState("");
  const [quotientTerms, setQuotientTerms] = useState<LearnerTermRecord[]>(() =>
    POLYNOMIAL_DIVISION_EXAMPLE.dividend.map(() => ({ ...BLANK_TERM })),
  );
  const [coefficientReason, setCoefficientReason] = useState<PolynomialDivisionReason>(WRONG_COEFFICIENT_REASON);
  const [exponentReason, setExponentReason] = useState<PolynomialExponentReason>(WRONG_EXPONENT_REASON);
  const [domain, setDomain] = useState<("x" | "y")[]>([]);
  const [reconstruction, setReconstruction] = useState<LearnerReconstructionRecord[]>(() =>
    POLYNOMIAL_DIVISION_EXAMPLE.dividend.map(() => ({ ...BLANK_RECONSTRUCTION })),
  );
  const [explanation, setExplanation] = useState("");
  const [transferTerms, setTransferTerms] = useState<LearnerTermRecord[]>(() =>
    POLYNOMIAL_DIVISION_FRESH_EXIT.dividend.map(() => ({ ...BLANK_TERM })),
  );
  const [repairResponse, setRepairResponse] = useState("");
  const [repairTerms, setRepairTerms] = useState<LearnerTermRecord[]>(() =>
    POLYNOMIAL_DIVISION_REPAIR_EXIT.dividend.map(() => ({ ...BLANK_TERM })),
  );
  const [activeDiagnosis, setActiveDiagnosis] = useState("");
  const [scaffold, setScaffold] = useState<"MODEL" | "RESTORE" | "FADE">("MODEL");
  const [feedback, setFeedback] = useState("Enter a prediction, then produce the quotient and reconstruction before checking.");
  const attempt = {
    divided_term_indexes: divided,
    prediction,
    quotient_terms: quotientTerms,
    coefficient_reason: coefficientReason,
    exponent_reason: exponentReason,
    domain_restrictions: domain,
    reconstruction,
    explanation,
    transfer_terms: transferTerms,
  };
  const diagnosis = evaluateLearnerPolynomialAttempt(attempt).diagnosis;

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
    setFeedback("Term selection changed. Now write the quotient record instead of revealing an answer card.");
    emit(next);
  }

  function updateTerm(index: number, field: keyof LearnerTermRecord, value: string, target: "quotient" | "transfer" | "repair") {
    const setter = target === "quotient" ? setQuotientTerms : target === "transfer" ? setTransferTerms : setRepairTerms;
    setter((records) => records.map((record, cursor) => cursor === index ? { ...record, [field]: value } : record));
    setFeedback("");
  }

  function updateReconstruction(index: number, field: keyof LearnerReconstructionRecord, value: string) {
    setReconstruction((records) => records.map((record, cursor) => cursor === index ? { ...record, [field]: value } : record));
    setFeedback("");
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
    const result = evaluateLearnerPolynomialAttempt(attempt);
    setActiveDiagnosis(result.correct ? "" : String(result.diagnosis));
    setScaffold(result.correct ? "FADE" : "RESTORE");
    setFeedback(result.feedback);
  }

  function checkRepair() {
    const result = evaluateSocraticRepair(activeDiagnosis || String(diagnosis), repairResponse, repairTerms);
    setScaffold(result.scaffold);
    setFeedback(result.feedback);
  }

  function reset() {
    setDivided([]);
    setPrediction("");
    setQuotientTerms(POLYNOMIAL_DIVISION_EXAMPLE.dividend.map(() => ({ ...BLANK_TERM })));
    setCoefficientReason(WRONG_COEFFICIENT_REASON);
    setExponentReason(WRONG_EXPONENT_REASON);
    setDomain([]);
    setReconstruction(POLYNOMIAL_DIVISION_EXAMPLE.dividend.map(() => ({ ...BLANK_RECONSTRUCTION })));
    setExplanation("");
    setTransferTerms(POLYNOMIAL_DIVISION_FRESH_EXIT.dividend.map(() => ({ ...BLANK_TERM })));
    setRepairResponse("");
    setRepairTerms(POLYNOMIAL_DIVISION_REPAIR_EXIT.dividend.map(() => ({ ...BLANK_TERM })));
    setActiveDiagnosis("");
    setScaffold("MODEL");
    setFeedback("Enter a prediction, then produce the quotient and reconstruction before checking.");
  }

  const repair = activeDiagnosis ? socraticRepairFor(activeDiagnosis) : null;

  return <section aria-label="Guided polynomial division exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: divide every grouped term by the same nonzero monomial</h3>
    <p>This review-only guided model does not count toward mastery. It requires learner-entered quotient, reconstruction, explanation, and fresh transfer evidence before any correctness feedback.</p>
    <div className="rounded border p-3" role="img" aria-label={`Polynomial division model: ${formatPolynomial(POLYNOMIAL_DIVISION_EXAMPLE.dividend)} divided by ${formatTerm(POLYNOMIAL_DIVISION_EXAMPLE.divisor)}.`}>
      <p className="font-semibold">({formatPolynomial(POLYNOMIAL_DIVISION_EXAMPLE.dividend)}) / {formatTerm(POLYNOMIAL_DIVISION_EXAMPLE.divisor)}</p>
      <label className="mt-3 block">
        Predict before manipulating
        <textarea className="mt-1 block w-full rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          value={prediction} onChange={(event) => setPrediction(event.target.value)}
          aria-label="Prediction before quotient reveal" rows={2} />
      </label>
    </div>

    <h3 className="font-semibold">Manipulate: choose each term and write its quotient</h3>
    <div className="grid gap-3 md:grid-cols-2">
      {POLYNOMIAL_DIVISION_EXAMPLE.dividend.map((term, index) => (
        <div key={index} className="rounded border p-3">
          <button type="button" className={`${CONTROL} w-full text-left ${divided.includes(index) ? "bg-blue-50" : ""}`}
            aria-pressed={divided.includes(index)} onClick={() => toggleTerm(index)}>
            Term {index + 1}: {formatTerm(term)} / {formatTerm(POLYNOMIAL_DIVISION_EXAMPLE.divisor)}
          </button>
          <TermInputs id={`${id}-q-${index}`} label={`Quotient term ${index + 1}`} value={quotientTerms[index]}
            onChange={(field, value) => updateTerm(index, field, value, "quotient")} />
        </div>
      ))}
    </div>

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

    <h3 className="font-semibold">Explain: reconstruct without an answer list</h3>
    <p role="status" aria-live="polite" aria-atomic="true">Current diagnosis: {String(diagnosis).replaceAll("_", " ")}.</p>
    <p aria-live="polite">Scaffold state: {scaffold === "FADE" ? "faded after verified repair" : scaffold === "RESTORE" ? "restored for targeted repair" : "modeled guidance"}.</p>
    <div className="grid gap-3 md:grid-cols-2" aria-label="Multiplication reconstruction">
      {POLYNOMIAL_DIVISION_EXAMPLE.dividend.map((_term, index) => (
        <fieldset key={index} className="rounded border p-3">
          <legend className="font-medium">Reconstruction product {index + 1}</legend>
          <label className="mr-2">coefficient <input className={INPUT} aria-label={`Reconstruction product ${index + 1} coefficient`} value={reconstruction[index].product_coefficient} onChange={(event) => updateReconstruction(index, "product_coefficient", event.target.value)} /></label>
          <label className="mr-2">x exponent <input className={INPUT} aria-label={`Reconstruction product ${index + 1} x exponent`} value={reconstruction[index].product_x_exponent} onChange={(event) => updateReconstruction(index, "product_x_exponent", event.target.value)} /></label>
          <label>y exponent <input className={INPUT} aria-label={`Reconstruction product ${index + 1} y exponent`} value={reconstruction[index].product_y_exponent} onChange={(event) => updateReconstruction(index, "product_y_exponent", event.target.value)} /></label>
        </fieldset>
      ))}
    </div>
    <label className="block">
      Explanation
      <textarea className="mt-1 block w-full rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        value={explanation} onChange={(event) => setExplanation(event.target.value)}
        aria-label="Explanation of polynomial division reasoning" rows={2} />
    </label>

    <h3 className="font-semibold">Transfer: solve a fresh exit without answer cards</h3>
    <p>({formatPolynomial(POLYNOMIAL_DIVISION_FRESH_EXIT.dividend)}) / {formatTerm(POLYNOMIAL_DIVISION_FRESH_EXIT.divisor)}</p>
    <div className="grid gap-3 md:grid-cols-2">
      {POLYNOMIAL_DIVISION_FRESH_EXIT.dividend.map((_term, index) => (
        <TermInputs key={index} id={`${id}-t-${index}`} label={`Fresh quotient term ${index + 1}`} value={transferTerms[index]}
          onChange={(field, value) => updateTerm(index, field, value, "transfer")} />
      ))}
    </div>

    {repair && <section aria-label="Socratic polynomial division repair" className="space-y-3 rounded border p-3">
      <h3 className="font-semibold">Diagnose and Repair</h3>
      <p>{repair.question}</p>
      <p className="text-sm">Your repair answer must include: {repair.expected_evidence.join(", ")}.</p>
      <label className="block">
        Repair response
        <textarea className="mt-1 block w-full rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          value={repairResponse} onChange={(event) => setRepairResponse(event.target.value)}
          aria-label="Socratic repair response" rows={2} />
      </label>
      <p>Different repair exit: ({formatPolynomial(POLYNOMIAL_DIVISION_REPAIR_EXIT.dividend)}) / {formatTerm(POLYNOMIAL_DIVISION_REPAIR_EXIT.divisor)}</p>
      <div className="grid gap-3 md:grid-cols-2">
        {POLYNOMIAL_DIVISION_REPAIR_EXIT.dividend.map((_term, index) => (
          <TermInputs key={index} id={`${id}-r-${index}`} label={`Repair quotient term ${index + 1}`} value={repairTerms[index]}
            onChange={(field, value) => updateTerm(index, field, value, "repair")} />
        ))}
      </div>
      <button type="button" className={CONTROL} onClick={checkRepair}>Check repair exit</button>
    </section>}

    <h3 className="font-semibold">Practice</h3>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={CONTROL} onClick={check}>Check polynomial division</button>
      <button type="button" className={CONTROL} onClick={reset}>Reset guided attempt</button>
    </div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
  </section>;
}

function TermInputs({ id, label, value, onChange }: {
  id: string;
  label: string;
  value: LearnerTermRecord;
  onChange: (field: keyof LearnerTermRecord, value: string) => void;
}) {
  return <fieldset className="mt-3 space-y-2 rounded border p-3">
    <legend className="font-medium">{label}</legend>
    <label className="mr-2">coefficient <input className={INPUT} aria-label={`${label} coefficient`} value={value.coefficient} onChange={(event) => onChange("coefficient", event.target.value)} /></label>
    <label className="mr-2">x exponent <input className={INPUT} aria-label={`${label} x exponent`} value={value.x_exponent} onChange={(event) => onChange("x_exponent", event.target.value)} /></label>
    <label>y exponent <input className={INPUT} aria-label={`${label} y exponent`} value={value.y_exponent} onChange={(event) => onChange("y_exponent", event.target.value)} /></label>
    <span id={`${id}-hint`} className="block text-sm">Use exact integers or reduced rational coefficients.</span>
  </fieldset>;
}
