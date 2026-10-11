export interface ExactRational {
  numerator: number;
  denominator: number;
}

export interface AlgebraTerm {
  coefficient: ExactRational;
  x_exponent: number;
  y_exponent: number;
}

export interface DivisionExample {
  dividend: readonly AlgebraTerm[];
  divisor: AlgebraTerm;
  quotient: readonly AlgebraTerm[];
  domain_restrictions: readonly ("x" | "y")[];
}

export type PolynomialDivisionReason =
  | "DIVIDEND_COEFFICIENT_DIVIDED_BY_DIVISOR_COEFFICIENT"
  | "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT";

export type PolynomialExponentReason =
  | "DIVIDEND_EXPONENT_MINUS_DIVISOR_EXPONENT"
  | "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT";

export type PredictionCoefficientEvidence =
  | "PREDICT_DIVIDE_EACH_DIVIDEND_COEFFICIENT"
  | "PREDICT_USE_DIVISOR_AS_NUMERATOR"
  | "";

export type PredictionExponentEvidence =
  | "PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS"
  | "PREDICT_ADD_LIKE_BASE_EXPONENTS"
  | "";

export type PredictionDomainEvidence =
  | "PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO"
  | "PREDICT_CANCELLED_VARIABLES_CAN_BE_ZERO"
  | "";

export type ExplanationReconstructionEvidence =
  | "EXPLAIN_QUOTIENT_TIMES_DIVISOR_REBUILDS_DIVIDEND"
  | "EXPLAIN_QUOTIENT_PLUS_DIVISOR_REBUILDS_DIVIDEND"
  | "";

export type RepairEvidenceChoice =
  | "REPAIR_PREDICT_ALL_THREE_FEATURES"
  | "REPAIR_PREDICT_ONLY_COEFFICIENTS"
  | "REPAIR_DIVIDEND_THEN_DIVISOR"
  | "REPAIR_DIVISOR_THEN_DIVIDEND"
  | "REPAIR_CANCEL_THEN_SUBTRACT"
  | "REPAIR_MULTIPLY_THEN_ADD"
  | "REPAIR_EVERY_TERM"
  | "REPAIR_FIRST_TERM_ONLY"
  | "REPAIR_KEEP_ORIGINAL_NONZERO"
  | "REPAIR_RESTRICTIONS_CANCEL_AWAY"
  | "REPAIR_COMPUTE_TERM_AND_VERIFY"
  | "REPAIR_ESTIMATE_TERM"
  | "REPAIR_PRODUCT_MATCHES_DIVIDEND"
  | "REPAIR_PRODUCT_MATCHES_DIVISOR"
  | "REPAIR_RECONSTRUCT_SUBTRACT_RESTRICT"
  | "REPAIR_RESTATE_RULE_WORDS"
  | "REPAIR_NEGATIVE_FROM_SUBTRACTION"
  | "REPAIR_NEGATIVE_MEANS_ERROR"
  | "";

export type PolynomialDivisionMisconception =
  | "NO_REMEDIATION"
  | "POLY.DIV.COEFFICIENT_RECIPROCAL"
  | "POLY.DIV.ADD_EXPONENTS"
  | "POLY.DIV.ONE_TERM_ONLY"
  | "POLY.DIV.DOMAIN_OMITTED";

export interface ReconstructionRecord {
  quotient_term: AlgebraTerm;
  divisor_term: AlgebraTerm;
  product_term: AlgebraTerm;
}

export interface StructuredPolynomialResponse {
  divided_term_indexes: readonly number[];
  coefficient_reason: PolynomialDivisionReason;
  exponent_reason: PolynomialExponentReason;
  domain_restrictions: readonly ("x" | "y")[];
}

export interface LearnerTermRecord {
  coefficient: string;
  x_exponent: string;
  y_exponent: string;
}

export interface LearnerReconstructionRecord {
  product_coefficient: string;
  product_x_exponent: string;
  product_y_exponent: string;
}

export interface PredictionEvidenceRecord {
  coefficient: PredictionCoefficientEvidence;
  exponent: PredictionExponentEvidence;
  domain: PredictionDomainEvidence;
}

export interface ExplanationEvidenceRecord {
  reconstruction: ExplanationReconstructionEvidence;
  exponent: PredictionExponentEvidence;
  domain: PredictionDomainEvidence;
}

export interface LearnerPolynomialAttempt extends StructuredPolynomialResponse {
  prediction: string;
  prediction_evidence: PredictionEvidenceRecord;
  explanation: string;
  explanation_evidence: ExplanationEvidenceRecord;
  quotient_terms: readonly LearnerTermRecord[];
  reconstruction: readonly LearnerReconstructionRecord[];
  transfer_terms: readonly LearnerTermRecord[];
}

export interface SocraticRepairPrompt {
  diagnosis: string;
  question: string;
  choices: readonly { value: RepairEvidenceChoice; label: string }[];
  correct_choice: RepairEvidenceChoice;
  scaffold: "RESTORE" | "FADE";
}

export const CORRECT_COEFFICIENT_REASON: PolynomialDivisionReason =
  "DIVIDEND_COEFFICIENT_DIVIDED_BY_DIVISOR_COEFFICIENT";
export const CORRECT_EXPONENT_REASON: PolynomialExponentReason =
  "DIVIDEND_EXPONENT_MINUS_DIVISOR_EXPONENT";

export const POLYNOMIAL_DIVISION_EXAMPLE: DivisionExample = {
  dividend: [
    { coefficient: rational(6), x_exponent: 3, y_exponent: 2 },
    { coefficient: rational(-4), x_exponent: 2, y_exponent: 1 },
  ],
  divisor: { coefficient: rational(2), x_exponent: 1, y_exponent: 1 },
  quotient: [
    { coefficient: rational(3), x_exponent: 2, y_exponent: 1 },
    { coefficient: rational(-2), x_exponent: 1, y_exponent: 0 },
  ],
  domain_restrictions: ["x", "y"],
};

export const POLYNOMIAL_DIVISION_FRESH_EXIT: DivisionExample = {
  dividend: [
    { coefficient: rational(6), x_exponent: 1, y_exponent: 1 },
    { coefficient: rational(10), x_exponent: 0, y_exponent: 2 },
  ],
  divisor: { coefficient: rational(2), x_exponent: 2, y_exponent: 1 },
  quotient: [
    { coefficient: rational(3), x_exponent: -1, y_exponent: 0 },
    { coefficient: rational(5), x_exponent: -2, y_exponent: 1 },
  ],
  domain_restrictions: ["x", "y"],
};

export const POLYNOMIAL_DIVISION_REPAIR_EXIT: DivisionExample = {
  dividend: [
    { coefficient: rational(-9), x_exponent: 4, y_exponent: 1 },
    { coefficient: rational(15), x_exponent: 2, y_exponent: 3 },
  ],
  divisor: { coefficient: rational(3), x_exponent: 2, y_exponent: 1 },
  quotient: [
    { coefficient: rational(-3), x_exponent: 2, y_exponent: 0 },
    { coefficient: rational(5), x_exponent: 0, y_exponent: 2 },
  ],
  domain_restrictions: ["x", "y"],
};

export function rational(numerator: number, denominator = 1): ExactRational {
  if (!Number.isSafeInteger(numerator) || !Number.isSafeInteger(denominator) || denominator === 0) {
    throw new RangeError("Expected safe integer rational values with nonzero denominator");
  }
  const sign = denominator < 0 ? -1 : 1;
  const gcd = greatestCommonDivisor(Math.abs(numerator), Math.abs(denominator));
  return { numerator: sign * numerator / gcd, denominator: Math.abs(denominator) / gcd };
}

export function divideTerm(dividend: AlgebraTerm, divisor: AlgebraTerm): AlgebraTerm {
  assertTerm(dividend);
  assertTerm(divisor);
  if (divisor.coefficient.numerator === 0) throw new RangeError("Cannot divide by a zero coefficient");
  return {
    coefficient: rational(
      dividend.coefficient.numerator * divisor.coefficient.denominator,
      dividend.coefficient.denominator * divisor.coefficient.numerator,
    ),
    x_exponent: dividend.x_exponent - divisor.x_exponent,
    y_exponent: dividend.y_exponent - divisor.y_exponent,
  };
}

export function multiplyTerms(left: AlgebraTerm, right: AlgebraTerm): AlgebraTerm {
  assertTerm(left);
  assertTerm(right);
  return {
    coefficient: rational(
      left.coefficient.numerator * right.coefficient.numerator,
      left.coefficient.denominator * right.coefficient.denominator,
    ),
    x_exponent: left.x_exponent + right.x_exponent,
    y_exponent: left.y_exponent + right.y_exponent,
  };
}

export function quotientFor(example: DivisionExample): readonly AlgebraTerm[] {
  assertExample(example);
  return example.dividend.map((term) => divideTerm(term, example.divisor));
}

export function reconstructionFor(example: DivisionExample): readonly ReconstructionRecord[] {
  return quotientFor(example).map((term) => ({
    quotient_term: term,
    divisor_term: example.divisor,
    product_term: multiplyTerms(term, example.divisor),
  }));
}

export function diagnosePolynomialDivision(
  response: StructuredPolynomialResponse,
  example: DivisionExample = POLYNOMIAL_DIVISION_EXAMPLE,
): PolynomialDivisionMisconception {
  assertExample(example);
  if (response.coefficient_reason !== CORRECT_COEFFICIENT_REASON) return "POLY.DIV.COEFFICIENT_RECIPROCAL";
  if (response.exponent_reason !== CORRECT_EXPONENT_REASON) return "POLY.DIV.ADD_EXPONENTS";
  if (!hasExactTermIndexSet(response.divided_term_indexes, example.dividend.length)) return "POLY.DIV.ONE_TERM_ONLY";
  if (!sameUniqueStrings(response.domain_restrictions, example.domain_restrictions)) return "POLY.DIV.DOMAIN_OMITTED";
  return "NO_REMEDIATION";
}

export function polynomialPracticeFeedback(response: StructuredPolynomialResponse) {
  const diagnosis = diagnosePolynomialDivision(response);
  const feedback: Record<PolynomialDivisionMisconception, string> = {
    "NO_REMEDIATION": "Correct. Every grouped term was divided, exponents were subtracted, and original nonzero restrictions were preserved.",
    "POLY.DIV.COEFFICIENT_RECIPROCAL": "Check coefficient direction: divide each dividend coefficient by the divisor coefficient.",
    "POLY.DIV.ADD_EXPONENTS": "Check exponent reasoning: dividing like bases subtracts divisor exponents from dividend exponents.",
    "POLY.DIV.ONE_TERM_ONLY": "The divisor applies to every term in the grouped polynomial, not only one term.",
    "POLY.DIV.DOMAIN_OMITTED": "Keep the original divisor restrictions: variables in the divisor cannot be zero.",
  };
  return { diagnosis, feedback: feedback[diagnosis], correct: diagnosis === "NO_REMEDIATION" };
}

export function evaluateLearnerPolynomialAttempt(
  attempt: LearnerPolynomialAttempt,
  example: DivisionExample = POLYNOMIAL_DIVISION_EXAMPLE,
  transferExample: DivisionExample = POLYNOMIAL_DIVISION_FRESH_EXIT,
) {
  const diagnosis = diagnosePolynomialDivision(attempt, example);
  if (!hasPredictionEvidence(attempt.prediction_evidence)) {
    return {
      correct: false,
      diagnosis: "POLY.DIV.PREDICTION_REASONING",
      feedback: "Predict with mathematical structure before calculating: choose what happens to coefficients, exponents, and divisor restrictions.",
    };
  }
  if (diagnosis !== "NO_REMEDIATION") return polynomialPracticeFeedback(attempt);
  if (!sameTermLists(attempt.quotient_terms, quotientFor(example))) {
    return {
      correct: false,
      diagnosis: "POLY.DIV.QUOTIENT_RECORD",
      feedback: "One quotient term is not independently produced yet. Divide each coefficient and subtract each matching exponent.",
    };
  }
  if (!sameReconstruction(attempt.reconstruction, reconstructionFor(example))) {
    return {
      correct: false,
      diagnosis: "POLY.DIV.RECONSTRUCTION_RECORD",
      feedback: "Use your quotient term times the original divisor to reconstruct each original dividend term.",
    };
  }
  if (!hasExplanationEvidence(attempt.explanation_evidence)) {
    return {
      correct: false,
      diagnosis: "POLY.DIV.EXPLANATION_REASONING",
      feedback: "Complete the explanation evidence: connect quotient times divisor to the dividend, exponent subtraction, and original nonzero restrictions.",
    };
  }
  if (!sameTermLists(attempt.transfer_terms, quotientFor(transferExample))) {
    return {
      correct: false,
      diagnosis: "POLY.DIV.FRESH_EXIT_UNVERIFIED",
      feedback: "Try the fresh exit without answer cards: at least one exponent becomes negative, so subtract divisor exponents carefully.",
    };
  }
  return {
    correct: true,
    diagnosis: "NO_REMEDIATION",
    feedback: "Correct. You predicted, produced quotient terms, reconstructed the dividend, explained the rule, and solved a fresh transfer case.",
  };
}

export function socraticRepairFor(diagnosis: string): SocraticRepairPrompt {
  const prompts: Record<string, SocraticRepairPrompt> = {
    "POLY.DIV.PREDICTION_REASONING": {
      diagnosis,
      question: "Before calculating, what should happen to coefficients, like-base exponents, and original divisor restrictions?",
      choices: [
        { value: "REPAIR_PREDICT_ALL_THREE_FEATURES", label: "Decide coefficient division, exponent subtraction, and original nonzero restrictions before computing." },
        { value: "REPAIR_PREDICT_ONLY_COEFFICIENTS", label: "Predict only the coefficient changes first, then decide the other parts after seeing the quotient." },
      ],
      correct_choice: "REPAIR_PREDICT_ALL_THREE_FEATURES",
      scaffold: "RESTORE",
    },
    "POLY.DIV.COEFFICIENT_RECIPROCAL": {
      diagnosis,
      question: "For one term, which coefficient is the dividend and which is the divisor? Write the division in that order.",
      choices: [
        { value: "REPAIR_DIVIDEND_THEN_DIVISOR", label: "Use the dividend coefficient first, then divide by the divisor coefficient." },
        { value: "REPAIR_DIVISOR_THEN_DIVIDEND", label: "Use the divisor coefficient first, then divide by the dividend coefficient." },
      ],
      correct_choice: "REPAIR_DIVIDEND_THEN_DIVISOR",
      scaffold: "RESTORE",
    },
    "POLY.DIV.ADD_EXPONENTS": {
      diagnosis,
      question: "When factors cancel in division, why do we subtract the divisor exponent instead of adding it?",
      choices: [
        { value: "REPAIR_CANCEL_THEN_SUBTRACT", label: "Cancel matching factors from numerator and denominator; the remaining count is a subtraction." },
        { value: "REPAIR_MULTIPLY_THEN_ADD", label: "Treat division like multiplication and add all matching exponents." },
      ],
      correct_choice: "REPAIR_CANCEL_THEN_SUBTRACT",
      scaffold: "RESTORE",
    },
    "POLY.DIV.ONE_TERM_ONLY": {
      diagnosis,
      question: "The divisor sits outside the grouped polynomial. Which terms must it divide, and why?",
      choices: [
        { value: "REPAIR_EVERY_TERM", label: "Divide every term in the grouped dividend by the same outside divisor." },
        { value: "REPAIR_FIRST_TERM_ONLY", label: "Divide only the first term because the divisor is written once." },
      ],
      correct_choice: "REPAIR_EVERY_TERM",
      scaffold: "RESTORE",
    },
    "POLY.DIV.DOMAIN_OMITTED": {
      diagnosis,
      question: "Which original divisor variables would make division by zero, and why do those restrictions remain?",
      choices: [
        { value: "REPAIR_KEEP_ORIGINAL_NONZERO", label: "Keep restrictions from the original divisor because those input values would make division undefined." },
        { value: "REPAIR_RESTRICTIONS_CANCEL_AWAY", label: "Remove restrictions whenever variables no longer appear in the simplified quotient." },
      ],
      correct_choice: "REPAIR_KEEP_ORIGINAL_NONZERO",
      scaffold: "RESTORE",
    },
    "POLY.DIV.QUOTIENT_RECORD": {
      diagnosis,
      question: "Choose one incorrect quotient term. What coefficient and exponent changes produce the exact quotient?",
      choices: [
        { value: "REPAIR_COMPUTE_TERM_AND_VERIFY", label: "Compute the coefficient division and exponent differences, then verify the term by multiplying back." },
        { value: "REPAIR_ESTIMATE_TERM", label: "Estimate the term from the visible sizes and signs, then move on." },
      ],
      correct_choice: "REPAIR_COMPUTE_TERM_AND_VERIFY",
      scaffold: "RESTORE",
    },
    "POLY.DIV.RECONSTRUCTION_RECORD": {
      diagnosis,
      question: "Multiply your quotient by the divisor. Which product must match the original dividend term?",
      choices: [
        { value: "REPAIR_PRODUCT_MATCHES_DIVIDEND", label: "The product of quotient and divisor must match the corresponding original dividend term." },
        { value: "REPAIR_PRODUCT_MATCHES_DIVISOR", label: "The product of quotient and divisor must match the divisor term." },
      ],
      correct_choice: "REPAIR_PRODUCT_MATCHES_DIVIDEND",
      scaffold: "RESTORE",
    },
    "POLY.DIV.EXPLANATION_REASONING": {
      diagnosis,
      question: "Explain how your quotient reconstructs the dividend and why restrictions are preserved.",
      choices: [
        { value: "REPAIR_RECONSTRUCT_SUBTRACT_RESTRICT", label: "Show that quotient times divisor returns the dividend, exponents came from subtraction, and original divisor zero values stay excluded." },
        { value: "REPAIR_RESTATE_RULE_WORDS", label: "Restate the rule words without connecting them to this dividend, divisor, and domain." },
      ],
      correct_choice: "REPAIR_RECONSTRUCT_SUBTRACT_RESTRICT",
      scaffold: "RESTORE",
    },
    "POLY.DIV.FRESH_EXIT_UNVERIFIED": {
      diagnosis,
      question: "In the fresh problem, where does a negative exponent come from, and how can multiplication verify it?",
      choices: [
        { value: "REPAIR_NEGATIVE_FROM_SUBTRACTION", label: "A negative exponent appears when the divisor exponent is larger; multiplying by the divisor verifies the original term." },
        { value: "REPAIR_NEGATIVE_MEANS_ERROR", label: "A negative exponent means the quotient cannot be checked by multiplication." },
      ],
      correct_choice: "REPAIR_NEGATIVE_FROM_SUBTRACTION",
      scaffold: "RESTORE",
    },
  };
  return prompts[diagnosis] ?? {
    diagnosis,
    question: "What exact step connects the divisor, quotient, and original dividend?",
    choices: [
      { value: "REPAIR_PRODUCT_MATCHES_DIVIDEND", label: "Quotient times divisor must reconstruct the original dividend." },
      { value: "REPAIR_PRODUCT_MATCHES_DIVISOR", label: "Quotient times divisor must reconstruct the divisor." },
    ],
    correct_choice: "REPAIR_PRODUCT_MATCHES_DIVIDEND",
    scaffold: "RESTORE",
  };
}

export function evaluateSocraticRepair(diagnosis: string, choice: RepairEvidenceChoice, repairTerms: readonly LearnerTermRecord[]) {
  const repair = socraticRepairFor(diagnosis);
  const reasoningOk = choice === repair.correct_choice;
  const exitOk = sameTermLists(repairTerms, quotientFor(POLYNOMIAL_DIVISION_REPAIR_EXIT));
  return {
    correct: reasoningOk && exitOk,
    feedback: reasoningOk && exitOk
      ? "Repair complete. Your scaffold can fade: you selected reasoning tied to the misconception and solved a different repair exit."
      : "Repair needs stronger evidence: choose the reasoning that fixes this misconception and complete the different repair exit.",
    scaffold: reasoningOk && exitOk ? "FADE" : repair.scaffold,
  };
}

export function formatRational(value: ExactRational): string {
  return value.denominator === 1 ? `${value.numerator}` : `${value.numerator}/${value.denominator}`;
}

export function formatTerm(term: AlgebraTerm): string {
  assertTerm(term);
  const coeff = formatRational(term.coefficient);
  const variable = [
    formatPower("x", term.x_exponent),
    formatPower("y", term.y_exponent),
  ].filter(Boolean).join("");
  if (!variable) return coeff;
  if (coeff === "1") return variable;
  if (coeff === "-1") return `-${variable}`;
  return `${coeff}${variable}`;
}

export function formatPolynomial(terms: readonly AlgebraTerm[]): string {
  return terms.map((term, index) => {
    const text = formatTerm(term);
    if (index === 0 || text.startsWith("-")) return text;
    return `+ ${text}`;
  }).join(" ");
}

export const POLYNOMIAL_DIVISION_ROUTE_STATUS =
  "DEFAULT_OFF_PENDING_APPROVED_SERVER_CAPABILITY" as const;

/**
 * Route the guided polynomial-by-monomial MVE only from a future approved,
 * server-owned capability. No such capability exists in LearnerWorkspace yet,
 * so every value fails closed. Mutable display names and provisional taxonomy
 * codes must never authorize this interaction.
 */
export function showPolynomialDivisionExploration(
  state: string,
  serverOwnedCapability: unknown,
): boolean {
  if (!["GUIDED_PRACTICE", "REMEDIATION"].includes(state)) return false;
  if (typeof serverOwnedCapability !== "string" || serverOwnedCapability.length === 0) return false;
  return false;
}

function assertExample(example: DivisionExample) {
  if (!example || example.dividend.length < 1 || example.dividend.length > 4) {
    throw new RangeError("Expected one to four dividend terms");
  }
  example.dividend.forEach(assertTerm);
  assertTerm(example.divisor);
  example.domain_restrictions.forEach((value) => {
    if (value !== "x" && value !== "y") throw new RangeError("Unsupported domain restriction");
  });
}

function assertTerm(term: AlgebraTerm) {
  if (!term || !Number.isSafeInteger(term.x_exponent) || !Number.isSafeInteger(term.y_exponent)) {
    throw new RangeError("Expected integer exponents");
  }
  rational(term.coefficient.numerator, term.coefficient.denominator);
}

function formatPower(symbol: "x" | "y", exponent: number): string {
  if (exponent === 0) return "";
  if (exponent === 1) return symbol;
  return `${symbol}^${exponent}`;
}

function greatestCommonDivisor(a: number, b: number): number {
  while (b) [a, b] = [b, a % b];
  return a || 1;
}

function hasExactTermIndexSet(values: readonly number[], termCount: number) {
  if (values.length !== termCount || new Set(values).size !== termCount) return false;
  return values.every((value) => Number.isSafeInteger(value) && value >= 0 && value < termCount);
}

function sameUniqueStrings(left: readonly string[], right: readonly string[]) {
  if (left.length !== right.length) return false;
  const leftSet = new Set(left);
  const rightSet = new Set(right);
  return leftSet.size === left.length && rightSet.size === right.length &&
    [...leftSet].every((value) => rightSet.has(value));
}

function hasPredictionEvidence(value: PredictionEvidenceRecord) {
  return value.coefficient === "PREDICT_DIVIDE_EACH_DIVIDEND_COEFFICIENT" &&
    value.exponent === "PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS" &&
    value.domain === "PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO";
}

function hasExplanationEvidence(value: ExplanationEvidenceRecord) {
  return value.reconstruction === "EXPLAIN_QUOTIENT_TIMES_DIVISOR_REBUILDS_DIVIDEND" &&
    value.exponent === "PREDICT_SUBTRACT_LIKE_BASE_EXPONENTS" &&
    value.domain === "PREDICT_KEEP_ORIGINAL_DIVISOR_NONZERO";
}

function sameTermLists(observed: readonly LearnerTermRecord[], expected: readonly AlgebraTerm[]) {
  if (observed.length !== expected.length) return false;
  try {
    return sameCanonicalTerms(observed.map(parseLearnerTerm), expected);
  } catch {
    return false;
  }
}

function sameReconstruction(observed: readonly LearnerReconstructionRecord[], expected: readonly ReconstructionRecord[]) {
  if (observed.length !== expected.length) return false;
  try {
    return sameCanonicalTerms(observed.map((record) => parseLearnerTerm({
      coefficient: record.product_coefficient,
      x_exponent: record.product_x_exponent,
      y_exponent: record.product_y_exponent,
    })), expected.map((record) => record.product_term));
  } catch {
    return false;
  }
}

function parseLearnerTerm(observed: LearnerTermRecord): AlgebraTerm {
  return {
    coefficient: parseRational(observed.coefficient),
    x_exponent: parseInteger(observed.x_exponent),
    y_exponent: parseInteger(observed.y_exponent),
  };
}

function sameCanonicalTerms(observed: readonly AlgebraTerm[], expected: readonly AlgebraTerm[]) {
  const observedByPowers = termsByPowers(observed);
  const expectedByPowers = termsByPowers(expected);
  if (!observedByPowers || !expectedByPowers || observedByPowers.size !== expectedByPowers.size) return false;
  return [...observedByPowers].every(([powers, coefficient]) => {
    const expectedCoefficient = expectedByPowers.get(powers);
    return expectedCoefficient !== undefined && sameRational(coefficient, expectedCoefficient);
  });
}

function termsByPowers(terms: readonly AlgebraTerm[]) {
  const byPowers = new Map<string, ExactRational>();
  for (const term of terms) {
    assertTerm(term);
    const powers = `${term.x_exponent},${term.y_exponent}`;
    if (byPowers.has(powers)) return null;
    byPowers.set(powers, term.coefficient);
  }
  return byPowers;
}

function parseInteger(value: string) {
  const trimmed = value.trim();
  if (!/^-?(0|[1-9]\d*)$/.test(trimmed)) throw new RangeError("Expected an integer string");
  const parsed = Number(trimmed);
  if (!Number.isSafeInteger(parsed)) throw new RangeError("Expected a safe integer string");
  return parsed;
}

function parseRational(value: string) {
  const trimmed = value.trim();
  if (!/^-?(0|[1-9]\d*)(\/[1-9]\d*)?$/.test(trimmed)) throw new RangeError("Expected a rational string");
  const [numerator, denominator = "1"] = trimmed.split("/");
  return rational(Number(numerator), Number(denominator));
}

function sameRational(left: ExactRational, right: ExactRational) {
  return left.numerator === right.numerator && left.denominator === right.denominator;
}
