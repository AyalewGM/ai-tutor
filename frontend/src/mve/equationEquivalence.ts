import { formatRational, rational, type Rational } from "./linearExplorer";

export interface AffineSide {
  x: Rational;
  constant: Rational;
}

export interface AffineEquation {
  left: AffineSide;
  right: AffineSide;
}

export type EquationOperation =
  | { kind: "add_constant"; amount: Rational }
  | { kind: "add_variable"; amount: Rational }
  | { kind: "scale"; amount: Rational };

export type EquationMisconception =
  | "EQ.OP.ONE_SIDE"
  | "EQ.DENOMINATOR_IGNORED"
  | "EQ.FALSE_EQUIVALENCE";

const ZERO = rational(0, 1);
const ONE = rational(1, 1);

function sameRational(left: Rational, right: Rational) {
  return left.numerator === right.numerator && left.denominator === right.denominator;
}

export function isBoundedRational(value: unknown): value is Rational {
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

export function isAffineEquation(value: unknown): value is AffineEquation {
  if (!value || typeof value !== "object") return false;
  const equation = value as AffineEquation;
  const validSide = (side: AffineSide | undefined) => !!side &&
    isBoundedRational(side.x) && isBoundedRational(side.constant);
  return validSide(equation.left) && validSide(equation.right) &&
    !sameRational(equation.left.x, equation.right.x);
}

function add(left: Rational, right: Rational) {
  return rational(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function multiply(left: Rational, right: Rational) {
  return rational(left.numerator * right.numerator, left.denominator * right.denominator);
}

function negate(value: Rational) {
  return rational(-value.numerator, value.denominator);
}

function reciprocal(value: Rational) {
  if (value.numerator === 0) throw new RangeError("Cannot divide by zero");
  return rational(value.denominator, value.numerator);
}

function transformSide(side: AffineSide, operation: EquationOperation): AffineSide {
  if (operation.kind === "add_constant") return { x: { ...side.x }, constant: add(side.constant, operation.amount) };
  if (operation.kind === "add_variable") return { x: add(side.x, operation.amount), constant: { ...side.constant } };
  return { x: multiply(side.x, operation.amount), constant: multiply(side.constant, operation.amount) };
}

function sameSide(left: AffineSide, right: AffineSide) {
  return sameRational(left.x, right.x) && sameRational(left.constant, right.constant);
}

/** Returns null for malformed, out-of-bounds, or equality-destroying operations. */
export function applyEquationOperation(equation: AffineEquation, operation: EquationOperation): AffineEquation | null {
  if (!isAffineEquation(equation) || !operation || !isBoundedRational(operation.amount) ||
      !["add_constant", "add_variable", "scale"].includes(operation.kind) ||
      (operation.kind === "scale" && operation.amount.numerator === 0)) return null;
  try {
    const next = { left: transformSide(equation.left, operation), right: transformSide(equation.right, operation) };
    return isAffineEquation(next) ? next : null;
  } catch {
    return null;
  }
}

/** Builds a visible counterexample for instruction; callers must never apply it as valid work. */
export function makeOneSidedCounterexample(
  equation: AffineEquation,
  operation: EquationOperation,
  side: "left" | "right" = "left",
): AffineEquation | null {
  if (!isAffineEquation(equation) || !operation || !isBoundedRational(operation.amount) ||
      !["add_constant", "add_variable", "scale"].includes(operation.kind) ||
      (operation.kind === "scale" && operation.amount.numerator === 0)) return null;
  try {
    const candidate = {
      left: side === "left" ? transformSide(equation.left, operation) : equation.left,
      right: side === "right" ? transformSide(equation.right, operation) : equation.right,
    };
    return isAffineEquation(candidate) &&
      !sameRational(equationSolution(equation), equationSolution(candidate)) ? candidate : null;
  } catch {
    return null;
  }
}

export function equationSolution(equation: AffineEquation): Rational {
  if (!isAffineEquation(equation)) throw new RangeError("Unsupported affine equation");
  return multiply(
    add(equation.right.constant, negate(equation.left.constant)),
    reciprocal(add(equation.left.x, negate(equation.right.x))),
  );
}

export function equationHolds(equation: AffineEquation, value: Rational) {
  if (!isAffineEquation(equation) || !isBoundedRational(value)) return false;
  try {
    const evaluate = (side: AffineSide) => add(multiply(side.x, value), side.constant);
    return sameRational(evaluate(equation.left), evaluate(equation.right));
  } catch {
    return false;
  }
}

/** Converts exact learner-step evidence into a bounded remediation route. */
export function diagnoseEquationAttempt(
  before: AffineEquation,
  candidate: AffineEquation,
  options: { denominatorIgnored?: boolean } = {},
): EquationMisconception | null {
  if (!isAffineEquation(before) || !isAffineEquation(candidate)) return "EQ.FALSE_EQUIVALENCE";
  const leftChanged = !sameSide(before.left, candidate.left);
  const rightChanged = !sameSide(before.right, candidate.right);
  if (leftChanged !== rightChanged) return "EQ.OP.ONE_SIDE";
  if (options.denominatorIgnored === true) return "EQ.DENOMINATOR_IGNORED";
  try {
    return sameRational(equationSolution(before), equationSolution(candidate)) ? null : "EQ.FALSE_EQUIVALENCE";
  } catch {
    return "EQ.FALSE_EQUIVALENCE";
  }
}

export function isEquationIsolated(equation: AffineEquation) {
  return isAffineEquation(equation) && sameRational(equation.left.x, ONE) &&
    sameRational(equation.left.constant, ZERO) && sameRational(equation.right.x, ZERO);
}

/** A deterministic solve path. Each move preserves the complete solution set. */
export function nextEquationMoves(equation: AffineEquation): readonly EquationOperation[] {
  if (!isAffineEquation(equation) || isEquationIsolated(equation)) return [];
  if (equation.right.x.numerator !== 0) return [{ kind: "add_variable", amount: negate(equation.right.x) }];
  if (equation.left.constant.numerator !== 0) return [{ kind: "add_constant", amount: negate(equation.left.constant) }];
  if (!sameRational(equation.left.x, ONE)) return [{ kind: "scale", amount: reciprocal(equation.left.x) }];
  return [];
}

function formatTerm(value: Rational, variable: boolean, first: boolean) {
  if (value.numerator === 0) return "";
  const negative = value.numerator < 0;
  const magnitude = rational(Math.abs(value.numerator), value.denominator);
  const coefficient = variable && sameRational(magnitude, ONE) ? "" : formatRational(magnitude);
  const body = `${coefficient}${variable ? "x" : ""}`;
  if (first) return negative ? `−${body}` : body;
  return `${negative ? " − " : " + "}${body}`;
}

export function formatAffineSide(side: AffineSide) {
  if (!side || !isBoundedRational(side.x) || !isBoundedRational(side.constant)) throw new RangeError("Unsupported affine side");
  const variable = formatTerm(side.x, true, true);
  const constant = formatTerm(side.constant, false, !variable);
  return `${variable}${constant}` || "0";
}

export function formatAffineEquation(equation: AffineEquation) {
  if (!isAffineEquation(equation)) throw new RangeError("Unsupported affine equation");
  return `${formatAffineSide(equation.left)} = ${formatAffineSide(equation.right)}`;
}

export function formatEquationOperation(operation: EquationOperation) {
  if (!operation || !isBoundedRational(operation.amount)) throw new RangeError("Unsupported equation operation");
  if (operation.kind === "scale") return `Multiply both sides by ${formatRational(operation.amount)}`;
  const magnitude = formatRational(rational(Math.abs(operation.amount.numerator), operation.amount.denominator));
  const term = operation.kind === "add_variable" ? `${magnitude === "1" ? "" : magnitude}x` : magnitude;
  return `${operation.amount.numerator < 0 ? "Subtract" : "Add"} ${term} ${operation.amount.numerator < 0 ? "from" : "to"} both sides`;
}

export function areScaleEquivalent(original: AffineEquation, candidate: AffineEquation) {
  if (!isAffineEquation(original) || !isAffineEquation(candidate)) return false;
  const originalTerms = [original.left.x, original.left.constant, original.right.x, original.right.constant];
  const candidateTerms = [candidate.left.x, candidate.left.constant, candidate.right.x, candidate.right.constant];
  const pivot = originalTerms.findIndex(term => term.numerator !== 0);
  if (pivot < 0) return false;
  try {
    const scale = multiply(candidateTerms[pivot], reciprocal(originalTerms[pivot]));
    if (scale.numerator === 0) return false;
    return originalTerms.every((term, index) => sameRational(multiply(term, scale), candidateTerms[index]));
  } catch {
    return false;
  }
}

export const EQUATION_EQUIVALENCE_EXAMPLES: readonly AffineEquation[] = [
  { left: { x: rational(-2, 1), constant: rational(-3, 1) }, right: { x: ZERO, constant: rational(14, 1) } },
  { left: { x: rational(1, 5), constant: rational(8, 1) }, right: { x: ZERO, constant: rational(7, 1) } },
  { left: { x: rational(-7, 1), constant: rational(2, 1) }, right: { x: rational(-1, 1), constant: rational(20, 1) } },
];

/** Fresh structurally related check; its exact solution is intentionally not exposed by the component. */
export const EQUATION_EQUIVALENCE_EXIT: AffineEquation = {
  left: { x: rational(2, 3), constant: ZERO },
  right: { x: ZERO, constant: rational(-4, 1) },
};
