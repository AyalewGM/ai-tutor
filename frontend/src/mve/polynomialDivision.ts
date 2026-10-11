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
