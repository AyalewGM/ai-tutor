/** Pure, deterministic fraction-bar arithmetic. No scoring or learner identifiers. */
export interface FractionParts { numerator: number; denominator: number }

/** Invalid denominators default to fourths; valid values are bounded to 1..12. */
export function normalizeFractionParts(numerator: number, denominator: number): FractionParts {
  const d = Number.isSafeInteger(denominator) ? Math.min(12, Math.max(1, denominator)) : 4;
  const n = Number.isSafeInteger(numerator) ? Math.min(d, Math.max(0, numerator)) : 0;
  return { numerator: n, denominator: d };
}

/** One native-button step, saturating at zero and the denominator. */
export function changeShadedParts(current: FractionParts, delta: -1 | 1): FractionParts {
  const safe = normalizeFractionParts(current.numerator, current.denominator);
  return normalizeFractionParts(safe.numerator + delta, safe.denominator);
}

/** Greatest common divisor, used only for explanatory equivalence. */
function gcd(a: number, b: number): number {
  while (b !== 0) {
    const remainder = a % b;
    a = b;
    b = remainder;
  }
  return a;
}

/** Reduce a displayed fraction without changing its shaded-parts representation. */
export function simplifyFraction(parts: FractionParts): FractionParts {
  const safe = normalizeFractionParts(parts.numerator, parts.denominator);
  const factor = gcd(safe.numerator, safe.denominator);
  return { numerator: safe.numerator / factor, denominator: safe.denominator / factor };
}

/** Produce a deterministic, non-assessment explanation of the shaded fraction. */
export function describeFraction(parts: FractionParts): string {
  const safe = normalizeFractionParts(parts.numerator, parts.denominator);
  const reduced = simplifyFraction(safe);
  const equivalent = reduced.numerator !== safe.numerator || reduced.denominator !== safe.denominator;
  const detail = equivalent ? ` This is equivalent to ${reduced.numerator}/${reduced.denominator}.` : "";
  return `${safe.numerator} out of ${safe.denominator} equal parts are shaded.${detail}`;
}

/** Fraction comparison never uses floating-point division or learner evidence. */
export type FractionRelation = "LESS_THAN" | "EQUAL_TO" | "GREATER_THAN";

/** Invalid reference fractions must not be silently replaced by defaults. */
export function isValidFractionParts(value: unknown): value is FractionParts {
  if (!value || typeof value !== "object") return false;
  const parts = value as Partial<FractionParts>;
  return Number.isSafeInteger(parts.denominator) &&
    (parts.denominator as number) >= 1 && (parts.denominator as number) <= 12 &&
    Number.isSafeInteger(parts.numerator) &&
    (parts.numerator as number) >= 0 &&
    (parts.numerator as number) <= (parts.denominator as number);
}

/** Null means invalid input; callers must fail closed rather than invent a comparison. */
export function compareFractions(left: unknown, right: unknown): FractionRelation | null {
  if (!isValidFractionParts(left) || !isValidFractionParts(right)) return null;
  const crossLeft = left.numerator * right.denominator;
  const crossRight = right.numerator * left.denominator;
  if (crossLeft < crossRight) return "LESS_THAN";
  if (crossLeft > crossRight) return "GREATER_THAN";
  return "EQUAL_TO";
}

/** Scale a fraction by a whole-number factor; null keeps callers fail-closed. */
export function scaleFraction(parts: FractionParts, factor: unknown): FractionParts | null {
  if (!isValidFractionParts(parts)) return null;
  if (!Number.isSafeInteger(factor) || (factor as number) < 2) return null;
  const numerator = parts.numerator * (factor as number);
  const denominator = parts.denominator * (factor as number);
  if (denominator > 12) return null;
  return { numerator, denominator };
}

/** Multipliers that keep the scaled denominator inside the bounded range. */
export function validScaleFactors(parts: FractionParts, factors: readonly number[] = [2, 3, 4]): number[] {
  return factors.filter((factor) => scaleFraction(parts, factor) !== null);
}

/** Deterministic equivalence explanation for guided exploration. */
export function describeEquivalence(parts: FractionParts, factor: number): string | null {
  const scaled = scaleFraction(parts, factor);
  if (scaled === null) return null;
  return (
    `Multiplying numerator and denominator by ${factor} keeps the same amount shaded: ` +
    `${parts.numerator}/${parts.denominator} = ${scaled.numerator}/${scaled.denominator}.`
  );
}

/** Deterministic simplification explanation; null when already lowest terms. */
export function describeSimplification(parts: FractionParts): string | null {
  const safe = normalizeFractionParts(parts.numerator, parts.denominator);
  const reduced = simplifyFraction(safe);
  if (reduced.numerator === safe.numerator && reduced.denominator === safe.denominator) return null;
  const divisor = safe.denominator / reduced.denominator;
  return (
    `Dividing numerator and denominator by ${divisor} keeps the same amount shaded: ` +
    `${safe.numerator}/${safe.denominator} = ${reduced.numerator}/${reduced.denominator}.`
  );
}

/** Exact common-denominator addition plan; null keeps callers fail-closed. */
export interface FractionAddition {
  common_denominator: number;
  first_scaled: FractionParts;
  second_scaled: FractionParts;
  sum_numerator: number;
  sum_denominator: number;
}

export function planFractionAddition(first: unknown, second: unknown, limit = 24): FractionAddition | null {
  if (!isValidFractionParts(first) || !isValidFractionParts(second)) return null;
  const lcd = (first.denominator / gcd(first.denominator, second.denominator)) * second.denominator;
  if (lcd > limit) return null;
  const sum = first.numerator * (lcd / first.denominator) + second.numerator * (lcd / second.denominator);
  if (sum > 2 * lcd) return null;
  return {
    common_denominator: lcd,
    first_scaled: { numerator: first.numerator * (lcd / first.denominator), denominator: lcd },
    second_scaled: { numerator: second.numerator * (lcd / second.denominator), denominator: lcd },
    sum_numerator: sum,
    sum_denominator: lcd,
  };
}

/** Deterministic addition explanation, including honest >1 sums. */
export function describeFractionAddition(plan: FractionAddition): string {
  const { first_scaled, second_scaled, sum_numerator: s, sum_denominator: d } = plan;
  const whole = Math.floor(s / d);
  const rest = s % d;
  const tail =
    s === 0 ? "" :
    whole === 0 ? ` ${s}/${d}.` :
    rest === 0 ? ` ${s}/${d}, which is ${whole} whole${whole === 1 ? "" : "s"}.` :
    ` ${s}/${d}, which is more than one whole: ${whole} and ${rest}/${d}.`;
  return `With equal parts, ${first_scaled.numerator}/${d} + ${second_scaled.numerator}/${d} =${tail}`;
}

/** Explanatory feedback only; this does not score answers or mastery. */
export function describeFractionComparison(left: FractionParts, right: FractionParts): string | null {
  const relation = compareFractions(left, right);
  if (relation === null) return null;
  const phrase = relation === "LESS_THAN" ? "less than" :
    relation === "GREATER_THAN" ? "greater than" : "equal to";
  return `${left.numerator}/${left.denominator} is ${phrase} ${right.numerator}/${right.denominator}.`;
}
