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
  type PredictionCoefficientEvidence,
  type PredictionDomainEvidence,
  type PredictionExponentEvidence,
  type ExplanationReconstructionEvidence,
  type RepairEvidenceChoice,
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
  const [predictionCoefficient, setPredictionCoefficient] = useState<PredictionCoefficientEvidence>("");
  const [predictionExponent, setPredictionExponent] = useState<PredictionExponentEvidence>("");
  const [predictionDomain, setPredictionDomain] = useState<PredictionDomainEvidence>("");
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
  const [explanationReconstruction, setExplanationReconstruction] = useState<ExplanationReconstructionEvidence>("");
  const [explanationExponent, setExplanationExponent] = useState<PredictionExponentEvidence>("");
  const [explanationDomain, setExplanationDomain] = useState<PredictionDomainEvidence>("");
  const [transferTerms, setTransferTerms] = useState<LearnerTermRecord[]>(() =>
    POLYNOMIAL_DIVISION_FRESH_EXIT.dividend.map(() => ({ ...BLANK_TERM })),
  );
  const [repairChoice, setRepairChoice] = useState<RepairEvidenceChoice>("");
  const [repairTerms, setRepairTerms] = useState<LearnerTermRecord[]>(() =>
    POLYNOMIAL_DIVISION_REPAIR_EXIT.dividend.map(() => ({ ...BLANK_TERM })),
  );
  const [activeDiagnosis, setActiveDiagnosis] = useState("");
  const [scaffold, setScaffold] = useState<"MODEL" | "RESTORE" | "FADE">("MODEL");
  const [feedback, setFeedback] = useState("Enter a prediction, then produce the quotient and reconstruction before checking.");
  const attempt = {
    divided_term_indexes: divided,
    prediction,
    prediction_evidence: {
      coefficient: predictionCoefficient,
      exponent: predictionExponent,
      domain: predictionDomain,
    },
    quotient_terms: quotientTerms,
    coefficient_reason: coefficientReason,
    exponent_reason: exponentReason,
    domain_restrictions: domain,
    reconstruction,
    explanation,
    explanation_evidence: {
      reconstruction: explanationReconstruction,
      exponent: explanationExponent,
      domain: explanationDomain,
    },
    transfer_terms: transferTerms,
  };
  const diagnosis = evaluateLearnerPolynomialAttempt(attempt).diagnosis;
  const supportVisible = scaffold !== "FADE";

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
    const result = evaluateSocraticRepair(activeDiagnosis || String(diagnosis), repairChoice, repairTerms);
    setScaffold(result.scaffold);
    if (result.correct) setActiveDiagnosis("");
    setFeedback(result.feedback);
  }

  function reset() {
    setDivided([]);
    setPrediction("");
    setPredictionCoefficient("");
    setPredictionExponent("");
    setPredictionDomain("");
    setQuotientTerms(POLYNOMIAL_DIVISION_EXAMPLE.dividend.map(() => ({ ...BLANK_TERM })));
    setCoefficientReason(WRONG_COEFFICIENT_REASON);
    setExponentReason(WRONG_EXPONENT_REASON);
    setDomain([]);
    setReconstruction(POLYNOMIAL_DIVISION_EXAMPLE.dividend.map(() => ({ ...BLANK_RECONSTRUCTION })));
    setExplanation("");
    setExplanationReconstruction("");
    setExplanationExponent("");
    setExplanationDomain("");
    setTransferTerms(POLYNOMIAL_DIVISION_FRESH_EXIT.dividend.map(() => ({ ...BLANK_TERM })));
    setRepairChoice("");
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
        Predict before manipulating (reflection)
        <textarea className="mt-1 block w-full rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          value={prediction} onChange={(event) => setPrediction(event.target.value)}
          aria-label="Prediction before quotient reveal" rows={2} />
      </label>
      <fieldset className="mt-3 grid gap-2 md:grid-cols-3">
        <legend className="font-medium">Prediction evidence</legend>
        <label className="block">Coefficient
          <select className={`${CONTROL} mt-1 block w-full`} aria-label="Prediction coefficient evidence" value={predictionCoefficient}
            onChange={(event) => setPredictionCoefficient(event.target.value as PredictionCoefficientEvidence)}>
            <option value="">Choose</option>
            <option value="PREDICT_DIVIDE_EACH_DIVIDEND_COEFFICIENT">Each dividend coefficient is divided by the divisor coefficient</option>
            <option value="PREDICT_USE_DIVISOR_AS_NUMERATOR">The divisor coefficient becomes the numerator</option>
          </select>
        </label>
        <label className="block">Exponent
          <select className={`${CONTROL} mt-1 block w-full`} aria-label="Prediction exponent evidence" value={predictionExponent}
            onChange={(event) => setPredictionExponent(event.target.value as PredictionExponentEvidence)}>
            <option value="">Choose</option>
            <option value="PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS">Like-base exponents subtract</option>
            <option value="PREDICT_ADD_LIKE_BASE_EXPONENTS">Like-base exponents add</option>
          </select>
        </label>
        <label className="block">Domain
          <select className={`${CONTROL} mt-1 block w-full`} aria-label="Prediction domain evidence" value={predictionDomain}
            onChange={(event) => setPredictionDomain(event.target.value as PredictionDomainEvidence)}>
            <option value="">Choose</option>
            <option value="PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO">Original divisor variables stay nonzero</option>
            <option value="PREDICT_CANCELLED_VARIABLES_CAN_BE_ZERO">Cancelled variables may be zero</option>
          </select>
        </label>
      </fieldset>
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
            showHint={supportVisible} onChange={(field, value) => updateTerm(index, field, value, "quotient")} />
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
    {supportVisible ? <p role="status" aria-live="polite" aria-atomic="true">Current diagnosis: {String(diagnosis).replaceAll("_", " ")}.</p> : null}
    <p aria-live="polite">Scaffold state: {scaffold === "FADE" ? "faded after verified repair" : scaffold === "RESTORE" ? "restored for targeted repair" : "modeled guidance"}.</p>
    {scaffold === "FADE" ? <p className="text-sm" aria-live="polite">Support faded: solve new terms without hint text or repair prompts.</p> : null}
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
    <fieldset className="grid gap-2 md:grid-cols-3">
      <legend className="font-medium">Explanation evidence</legend>
      <label className="block">Reconstruction
        <select className={`${CONTROL} mt-1 block w-full`} aria-label="Explanation reconstruction evidence" value={explanationReconstruction}
          onChange={(event) => setExplanationReconstruction(event.target.value as ExplanationReconstructionEvidence)}>
          <option value="">Choose</option>
          <option value="EXPLAIN_QUOTIENT_TIMES_DIVISOR_REBUILDS_DIVIDEND">Quotient times divisor rebuilds each dividend term</option>
          <option value="EXPLAIN_QUOTIENT_PLUS_DIVISOR_REBUILDS_DIVIDEND">Quotient plus divisor rebuilds each dividend term</option>
        </select>
      </label>
      <label className="block">Exponent
        <select className={`${CONTROL} mt-1 block w-full`} aria-label="Explanation exponent evidence" value={explanationExponent}
          onChange={(event) => setExplanationExponent(event.target.value as PredictionExponentEvidence)}>
          <option value="">Choose</option>
          <option value="PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS">Like-base exponents subtract</option>
          <option value="PREDICT_ADD_LIKE_BASE_EXPONENTS">Like-base exponents add</option>
        </select>
      </label>
      <label className="block">Domain
        <select className={`${CONTROL} mt-1 block w-full`} aria-label="Explanation domain evidence" value={explanationDomain}
          onChange={(event) => setExplanationDomain(event.target.value as PredictionDomainEvidence)}>
          <option value="">Choose</option>
          <option value="PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO">Restrictions come from original divisor values</option>
          <option value="PREDICT_CANCELLED_VARIABLES_CAN_BE_ZERO">Restrictions disappear after simplification</option>
        </select>
      </label>
    </fieldset>

    <h3 className="font-semibold">Transfer: solve a fresh exit without answer cards</h3>
    <p>({formatPolynomial(POLYNOMIAL_DIVISION_FRESH_EXIT.dividend)}) / {formatTerm(POLYNOMIAL_DIVISION_FRESH_EXIT.divisor)}</p>
    <div className="grid gap-3 md:grid-cols-2">
      {POLYNOMIAL_DIVISION_FRESH_EXIT.dividend.map((_term, index) => (
        <TermInputs key={index} id={`${id}-t-${index}`} label={`Fresh quotient term ${index + 1}`} value={transferTerms[index]}
          showHint={supportVisible} onChange={(field, value) => updateTerm(index, field, value, "transfer")} />
      ))}
    </div>

    {repair && supportVisible ? <section aria-label="Socratic polynomial division repair" className="space-y-3 rounded border p-3">
      <h3 className="font-semibold">Diagnose and Repair</h3>
      <p>{repair.question}</p>
      <fieldset className="space-y-2">
        <legend className="font-medium">Repair reasoning</legend>
        {repair.choices.map((choice) => (
          <label key={choice.value} className="block">
            <input type="radio" name={`${id}-repair`} checked={repairChoice === choice.value}
              onChange={() => setRepairChoice(choice.value)} /> {choice.label}
          </label>
        ))}
      </fieldset>
      <p>Different repair exit: ({formatPolynomial(POLYNOMIAL_DIVISION_REPAIR_EXIT.dividend)}) / {formatTerm(POLYNOMIAL_DIVISION_REPAIR_EXIT.divisor)}</p>
      <div className="grid gap-3 md:grid-cols-2">
        {POLYNOMIAL_DIVISION_REPAIR_EXIT.dividend.map((_term, index) => (
          <TermInputs key={index} id={`${id}-r-${index}`} label={`Repair quotient term ${index + 1}`} value={repairTerms[index]}
            showHint={true} onChange={(field, value) => updateTerm(index, field, value, "repair")} />
        ))}
      </div>
      <button type="button" className={CONTROL} onClick={checkRepair}>Check repair exit</button>
    </section> : null}

    <h3 className="font-semibold">Practice</h3>
    <div className="flex flex-wrap gap-2">
      <button type="button" className={CONTROL} onClick={check}>Check polynomial division</button>
      <button type="button" className={CONTROL} onClick={reset}>Reset guided attempt</button>
    </div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>
  </section>;
}

function TermInputs({ id, label, value, showHint, onChange }: {
  id: string;
  label: string;
  value: LearnerTermRecord;
  showHint: boolean;
  onChange: (field: keyof LearnerTermRecord, value: string) => void;
}) {
  return <fieldset className="mt-3 space-y-2 rounded border p-3">
    <legend className="font-medium">{label}</legend>
    <label className="mr-2">coefficient <input className={INPUT} aria-label={`${label} coefficient`} value={value.coefficient} onChange={(event) => onChange("coefficient", event.target.value)} /></label>
    <label className="mr-2">x exponent <input className={INPUT} aria-label={`${label} x exponent`} value={value.x_exponent} onChange={(event) => onChange("x_exponent", event.target.value)} /></label>
    <label>y exponent <input className={INPUT} aria-label={`${label} y exponent`} value={value.y_exponent} onChange={(event) => onChange("y_exponent", event.target.value)} /></label>
    {showHint ? <span id={`${id}-hint`} className="block text-sm">Use exact integers or reduced rational coefficients.</span> : null}
  </fieldset>;
}
