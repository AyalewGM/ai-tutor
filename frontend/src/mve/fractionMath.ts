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
