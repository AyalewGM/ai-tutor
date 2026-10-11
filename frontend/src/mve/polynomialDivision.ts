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

export interface LearnerPolynomialAttempt extends StructuredPolynomialResponse {
  prediction: string;
  explanation: string;
  quotient_terms: readonly LearnerTermRecord[];
  reconstruction: readonly LearnerReconstructionRecord[];
  transfer_terms: readonly LearnerTermRecord[];
}

export interface SocraticRepairPrompt {
  diagnosis: string;
  question: string;
  expected_evidence: readonly string[];
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
  if (uniqueSorted(response.divided_term_indexes).length !== example.dividend.length) return "POLY.DIV.ONE_TERM_ONLY";
  if (!sameStrings(response.domain_restrictions, example.domain_restrictions)) return "POLY.DIV.DOMAIN_OMITTED";
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
  if (!hasPredictionEvidence(attempt.prediction)) {
    return {
      correct: false,
      diagnosis: "POLY.DIV.PREDICTION_REASONING",
      feedback: "Predict with math evidence: coefficients divide, like-base exponents subtract, and original divisor variables stay nonzero.",
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
  if (!hasExplanationEvidence(attempt.explanation)) {
    return {
      correct: false,
      diagnosis: "POLY.DIV.EXPLANATION_REASONING",
      feedback: "Explain with math evidence: name quotient times divisor reconstruction, exponent subtraction, and original nonzero restrictions.",
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
      expected_evidence: ["coefficient division", "exponent subtraction", "nonzero restriction"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.COEFFICIENT_RECIPROCAL": {
      diagnosis,
      question: "For one term, which coefficient is the dividend and which is the divisor? Write the division in that order.",
      expected_evidence: ["dividend coefficient first", "divisor coefficient second"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.ADD_EXPONENTS": {
      diagnosis,
      question: "When factors cancel in division, why do we subtract the divisor exponent instead of adding it?",
      expected_evidence: ["cancel matching factors", "subtract divisor exponent"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.ONE_TERM_ONLY": {
      diagnosis,
      question: "The divisor sits outside the grouped polynomial. Which terms must it divide, and why?",
      expected_evidence: ["every term", "same divisor"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.DOMAIN_OMITTED": {
      diagnosis,
      question: "Which original divisor variables would make division by zero, and why do those restrictions remain?",
      expected_evidence: ["x nonzero", "y nonzero", "original divisor"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.QUOTIENT_RECORD": {
      diagnosis,
      question: "Choose one incorrect quotient term. What coefficient and exponent changes produce the exact quotient?",
      expected_evidence: ["divide coefficient", "subtract exponents"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.RECONSTRUCTION_RECORD": {
      diagnosis,
      question: "Multiply your quotient by the divisor. Which product must match the original dividend term?",
      expected_evidence: ["quotient times divisor", "original dividend"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.EXPLANATION_REASONING": {
      diagnosis,
      question: "Explain how your quotient reconstructs the dividend and why restrictions are preserved.",
      expected_evidence: ["reconstruction", "exponent subtraction", "nonzero restriction"],
      scaffold: "RESTORE",
    },
    "POLY.DIV.FRESH_EXIT_UNVERIFIED": {
      diagnosis,
      question: "In the fresh problem, where does a negative exponent come from, and how can multiplication verify it?",
      expected_evidence: ["negative exponent", "multiply to verify"],
      scaffold: "RESTORE",
    },
  };
  return prompts[diagnosis] ?? {
    diagnosis,
    question: "What exact step connects the divisor, quotient, and original dividend?",
    expected_evidence: ["quotient", "divisor", "dividend"],
    scaffold: "RESTORE",
  };
}

export function evaluateSocraticRepair(diagnosis: string, response: string, repairTerms: readonly LearnerTermRecord[]) {
  const repair = socraticRepairFor(diagnosis);
  const textOk = repair.expected_evidence.every((evidence) => phraseMatches(response, evidence));
  const exitOk = sameTermLists(repairTerms, quotientFor(POLYNOMIAL_DIVISION_REPAIR_EXIT));
  return {
    correct: textOk && exitOk,
    feedback: textOk && exitOk
      ? "Repair complete. Your scaffold can fade: you explained the misconception and solved a different repair exit."
      : `Repair needs more evidence: answer the question using ${repair.expected_evidence.join(", ")} and complete the different repair exit.`,
    scaffold: textOk && exitOk ? "FADE" : repair.scaffold,
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

export function showPolynomialDivisionExploration(state: string, skillName: string): boolean {
  return ["GUIDED_PRACTICE", "REMEDIATION"].includes(state) &&
    /polynomial.*monomial|monomial.*polynomial|polynomial division|divide.*polynomial/i.test(skillName);
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

function uniqueSorted(values: readonly number[]) {
  return [...new Set(values)].sort((a, b) => a - b);
}

function sameStrings(left: readonly string[], right: readonly string[]) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function hasPredictionEvidence(value: string) {
  return phraseMatches(value, "coefficient division") &&
    phraseMatches(value, "exponent subtraction") &&
    phraseMatches(value, "nonzero restriction");
}

function hasExplanationEvidence(value: string) {
  return phraseMatches(value, "reconstruction") &&
    phraseMatches(value, "exponent subtraction") &&
    phraseMatches(value, "nonzero restriction");
}

function phraseMatches(value: string, evidence: string) {
  const text = value.toLowerCase();
  switch (evidence) {
    case "coefficient division":
      return includesAll(text, ["coefficient"]) && includesAny(text, ["divide", "divides", "division"]);
    case "exponent subtraction":
      return includesAll(text, ["exponent"]) && includesAny(text, ["subtract", "subtracts", "subtraction"]);
    case "nonzero restriction":
      return includesAny(text, ["nonzero", "not zero", "cannot be zero", "restriction"]);
    case "dividend coefficient first":
      return includesAll(text, ["dividend", "coefficient", "first"]);
    case "divisor coefficient second":
      return includesAll(text, ["divisor", "coefficient", "second"]);
    case "cancel matching factors":
      return includesAll(text, ["cancel", "factor"]);
    case "subtract divisor exponent":
      return includesAll(text, ["subtract", "divisor", "exponent"]);
    case "every term":
      return includesAll(text, ["every", "term"]);
    case "same divisor":
      return includesAll(text, ["same", "divisor"]);
    case "x nonzero":
      return text.includes("x") && includesAny(text, ["nonzero", "not zero", "cannot be zero"]);
    case "y nonzero":
      return text.includes("y") && includesAny(text, ["nonzero", "not zero", "cannot be zero"]);
    case "original divisor":
      return includesAll(text, ["original", "divisor"]);
    case "divide coefficient":
      return includesAll(text, ["coefficient"]) && includesAny(text, ["divide", "divides", "division"]);
    case "subtract exponents":
      return includesAll(text, ["exponent"]) && includesAny(text, ["subtract", "subtracts", "subtraction"]);
    case "quotient times divisor":
      return includesAll(text, ["quotient", "divisor"]);
    case "original dividend":
      return includesAll(text, ["original", "dividend"]);
    case "reconstruction":
      return includesAny(text, ["reconstruct", "multiply", "product"]);
    case "negative exponent":
      return includesAll(text, ["negative", "exponent"]);
    case "multiply to verify":
      return includesAll(text, ["multiply", "verify"]);
    default:
      return text.includes(evidence);
  }
}

function includesAll(text: string, words: readonly string[]) {
  return words.every((word) => text.includes(word));
}

function includesAny(text: string, words: readonly string[]) {
  return words.some((word) => text.includes(word));
}

function sameTermLists(observed: readonly LearnerTermRecord[], expected: readonly AlgebraTerm[]) {
  return observed.length === expected.length &&
    observed.every((term, index) => termMatches(term, expected[index]));
}

function sameReconstruction(observed: readonly LearnerReconstructionRecord[], expected: readonly ReconstructionRecord[]) {
  return observed.length === expected.length &&
    observed.every((record, index) => termMatches({
      coefficient: record.product_coefficient,
      x_exponent: record.product_x_exponent,
      y_exponent: record.product_y_exponent,
    }, expected[index].product_term));
}

function termMatches(observed: LearnerTermRecord, expected: AlgebraTerm) {
  try {
    return sameRational(parseRational(observed.coefficient), expected.coefficient) &&
      parseInteger(observed.x_exponent) === expected.x_exponent &&
      parseInteger(observed.y_exponent) === expected.y_exponent;
  } catch {
    return false;
  }
}

function parseInteger(value: string) {
  const trimmed = value.trim();
  if (!/^-?(0|[1-9]\d*)$/.test(trimmed)) throw new RangeError("Expected an integer string");
  return Number(trimmed);
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
