import { formatRational, rational, type Rational } from "./linearExplorer";

export interface PolynomialTerm {
  coefficient: Rational;
  xExponent: number;
  yExponent: number;
}

export interface PolynomialDivisionVariant {
  id: string;
  dividend: readonly PolynomialTerm[];
  divisor: PolynomialTerm;
  restrictions: readonly ("x" | "y")[];
}

export type PolynomialDivisionMisconception =
  | "POLY.DIV.COEFFICIENT_RECIPROCAL"
  | "POLY.DIV.ADD_EXPONENTS"
  | "POLY.DIV.ONE_TERM_ONLY"
  | "POLY.DIV.DOMAIN_OMITTED";

export interface PolynomialDivisionAttempt {
  processedTermIndexes: readonly number[];
  coefficientReason: "DIVIDEND_BY_DIVISOR" | "DIVISOR_BY_DIVIDEND" | null;
  exponentReason: "SUBTRACT" | "ADD" | null;
  restrictions: readonly ("x" | "y")[];
  reconstructionConfirmed: boolean;
}

const MAX_EXPONENT = 12;

function sameRational(left: Rational, right: Rational) {
  return left.numerator === right.numerator && left.denominator === right.denominator;
}

function isRational(value: unknown): value is Rational {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Rational;
  if (!Number.isSafeInteger(candidate.numerator) || !Number.isSafeInteger(candidate.denominator) ||
      candidate.denominator < 1 || candidate.denominator > 10000 || Math.abs(candidate.numerator) > 10000) return false;
  try {
    return sameRational(candidate, rational(candidate.numerator, candidate.denominator));
  } catch {
    return false;
  }
}

export function isPolynomialTerm(value: unknown): value is PolynomialTerm {
  if (!value || typeof value !== "object") return false;
  const term = value as PolynomialTerm;
  return isRational(term.coefficient) && term.coefficient.numerator !== 0 &&
    Number.isSafeInteger(term.xExponent) && Math.abs(term.xExponent) <= MAX_EXPONENT &&
    Number.isSafeInteger(term.yExponent) && Math.abs(term.yExponent) <= MAX_EXPONENT;
}

export function dividePolynomialTerm(dividend: PolynomialTerm, divisor: PolynomialTerm): PolynomialTerm {
  if (!isPolynomialTerm(dividend) || !isPolynomialTerm(divisor)) throw new RangeError("Unsupported polynomial term");
  const quotient = {
    coefficient: rational(
      dividend.coefficient.numerator * divisor.coefficient.denominator,
      dividend.coefficient.denominator * divisor.coefficient.numerator,
    ),
    xExponent: dividend.xExponent - divisor.xExponent,
    yExponent: dividend.yExponent - divisor.yExponent,
  };
  if (!isPolynomialTerm(quotient)) throw new RangeError("Quotient is outside the bounded MVE contract");
  return quotient;
}

export function multiplyPolynomialTerms(left: PolynomialTerm, right: PolynomialTerm): PolynomialTerm {
  if (!isPolynomialTerm(left) || !isPolynomialTerm(right)) throw new RangeError("Unsupported polynomial term");
  const product = {
    coefficient: rational(
      left.coefficient.numerator * right.coefficient.numerator,
      left.coefficient.denominator * right.coefficient.denominator,
    ),
    xExponent: left.xExponent + right.xExponent,
    yExponent: left.yExponent + right.yExponent,
  };
  if (!isPolynomialTerm(product)) throw new RangeError("Product is outside the bounded MVE contract");
  return product;
}

export function samePolynomialTerm(left: PolynomialTerm, right: PolynomialTerm) {
  return isPolynomialTerm(left) && isPolynomialTerm(right) &&
    sameRational(left.coefficient, right.coefficient) &&
    left.xExponent === right.xExponent && left.yExponent === right.yExponent;
}

function variableText(name: "x" | "y", exponent: number) {
  if (exponent === 0) return "";
  return exponent === 1 ? name : `${name}^${exponent}`;
}

export function formatPolynomialTerm(term: PolynomialTerm) {
  if (!isPolynomialTerm(term)) throw new RangeError("Unsupported polynomial term");
  const hasVariable = term.xExponent !== 0 || term.yExponent !== 0;
  const coefficient = formatRational(term.coefficient);
  const coefficientText = hasVariable && coefficient === "1" ? "" :
    hasVariable && coefficient === "-1" ? "−" : coefficient.replace("-", "−");
  return `${coefficientText}${variableText("x", term.xExponent)}${variableText("y", term.yExponent)}`;
}

export function formatPolynomial(terms: readonly PolynomialTerm[]) {
  if (!Array.isArray(terms) || terms.length < 1 || terms.length > 4 || !terms.every(isPolynomialTerm)) {
    throw new RangeError("Unsupported polynomial");
  }
  return terms.map((term, index) => {
    const text = formatPolynomialTerm(term);
    if (index === 0) return text;
    return text.startsWith("−") ? ` − ${text.slice(1)}` : ` + ${text}`;
  }).join("");
}

const term = (coefficient: number, xExponent: number, yExponent: number): PolynomialTerm => ({
  coefficient: rational(coefficient, 1), xExponent, yExponent,
});

export const POLYNOMIAL_DIVISION_VARIANTS: readonly PolynomialDivisionVariant[] = [
  {
    id: "poly-div-0",
    dividend: [term(6, 3, 1), term(-10, 2, 0)],
    divisor: term(2, 1, 0),
    restrictions: ["x"],
  },
  {
    id: "poly-div-1",
    dividend: [term(12, 3, 1), term(-6, 1, 4)],
    divisor: term(-3, 1, 2),
    restrictions: ["x", "y"],
  },
  {
    id: "poly-div-2",
    dividend: [term(-8, 4, 2), term(20, 2, 1)],
    divisor: term(4, 2, 0),
    restrictions: ["x"],
  },
  {
    id: "poly-div-3",
    dividend: [term(10, 1, 3), term(-4, 4, 0)],
    divisor: term(2, 2, 1),
    restrictions: ["x", "y"],
  },
] as const;

export function polynomialDivisionVariant(seed: number) {
  if (!Number.isSafeInteger(seed) || seed < 0 || seed > 1_000_000) throw new RangeError("Invalid polynomial-division seed");
  return POLYNOMIAL_DIVISION_VARIANTS[seed % POLYNOMIAL_DIVISION_VARIANTS.length];
}

export function quotientTerms(variant: PolynomialDivisionVariant) {
  if (!variant || !Array.isArray(variant.dividend) || variant.dividend.length < 1 || variant.dividend.length > 4 ||
      !variant.dividend.every(isPolynomialTerm) || !isPolynomialTerm(variant.divisor)) {
    throw new RangeError("Unsupported polynomial-division variant");
  }
  return variant.dividend.map(value => dividePolynomialTerm(value, variant.divisor));
}

export function reconstructsDividend(variant: PolynomialDivisionVariant, quotient: readonly PolynomialTerm[]) {
  if (!Array.isArray(quotient) || quotient.length !== variant.dividend.length || !quotient.every(isPolynomialTerm)) return false;
  return quotient.every((value, index) =>
    samePolynomialTerm(multiplyPolynomialTerms(value, variant.divisor), variant.dividend[index]));
}

function sortedUniqueIndexes(values: readonly number[], length: number) {
  if (!Array.isArray(values) || values.some(value => !Number.isSafeInteger(value) || value < 0 || value >= length)) return null;
  return [...new Set(values)].sort((a, b) => a - b);
}

export function diagnosePolynomialDivisionAttempt(
  variant: PolynomialDivisionVariant,
  attempt: PolynomialDivisionAttempt,
): PolynomialDivisionMisconception | "UNCLASSIFIED_FOR_HUMAN_REVIEW" | null {
  const indexes = sortedUniqueIndexes(attempt?.processedTermIndexes ?? [], variant.dividend.length);
  if (!indexes || indexes.length !== variant.dividend.length) return "POLY.DIV.ONE_TERM_ONLY";
  if (attempt.coefficientReason === "DIVISOR_BY_DIVIDEND") return "POLY.DIV.COEFFICIENT_RECIPROCAL";
  if (attempt.exponentReason === "ADD") return "POLY.DIV.ADD_EXPONENTS";
  const restrictions = [...new Set(attempt.restrictions ?? [])].sort();
  if (restrictions.join("|") !== [...variant.restrictions].sort().join("|")) return "POLY.DIV.DOMAIN_OMITTED";
  if (attempt.coefficientReason !== "DIVIDEND_BY_DIVISOR" || attempt.exponentReason !== "SUBTRACT" ||
      attempt.reconstructionConfirmed !== true) return "UNCLASSIFIED_FOR_HUMAN_REVIEW";
  return null;
}

export function freshPolynomialDivisionVariant(seed: number, misconception: PolynomialDivisionMisconception) {
  if (!Number.isSafeInteger(seed) || seed < 0 || seed > 1_000_000) throw new RangeError("Invalid polynomial-division seed");
  if (misconception === "POLY.DIV.ADD_EXPONENTS") {
    return POLYNOMIAL_DIVISION_VARIANTS[seed % POLYNOMIAL_DIVISION_VARIANTS.length === 1 ? 3 : 1];
  }
  const offset = misconception === "POLY.DIV.COEFFICIENT_RECIPROCAL" ? 1 :
    misconception === "POLY.DIV.ONE_TERM_ONLY" ? 2 : misconception === "POLY.DIV.DOMAIN_OMITTED" ? 4 : 0;
  const current = seed % POLYNOMIAL_DIVISION_VARIANTS.length;
  let next = (seed + offset) % POLYNOMIAL_DIVISION_VARIANTS.length;
  if (next === current) next = (next + 1) % POLYNOMIAL_DIVISION_VARIANTS.length;
  return POLYNOMIAL_DIVISION_VARIANTS[next];
}
