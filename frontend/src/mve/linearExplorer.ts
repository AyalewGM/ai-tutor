/** Exact bounded rational models; SVG coordinates alone may use floating point. */
export interface Rational { numerator: number; denominator: number }
export function rational(numerator: number, denominator: number): Rational {
  if (![numerator, denominator].every(Number.isSafeInteger) || denominator === 0 ||
      Math.abs(numerator) > 10000 || Math.abs(denominator) > 10000) throw new RangeError("Invalid bounded rational");
  let a = Math.abs(numerator), b = Math.abs(denominator);
  while (b) { const remainder = a % b; a = b; b = remainder; }
  const sign = denominator < 0 ? -1 : 1;
  return { numerator: numerator === 0 ? 0 : sign * numerator / a, denominator: Math.abs(denominator) / a };
}
export function formatRational(value: Rational): string {
  return value.denominator === 1 ? String(value.numerator) : `${value.numerator}/${value.denominator}`;
}
export function linearModel(rise: number, run: number, intercept: number) {
  if (!Number.isSafeInteger(rise) || Math.abs(rise) > 6 ||
      !Number.isSafeInteger(run) || run < 1 || run > 6 ||
      !Number.isSafeInteger(intercept) || Math.abs(intercept) > 4) throw new RangeError("Unsupported linear model");
  const slope = rational(rise, run);
  const equation = `y = (${formatRational(slope)})x ${intercept < 0 ? "−" : "+"} ${Math.abs(intercept)}`;
  const rows = [-2, -1, 0, 1, 2].map(x => ({ x, y: rational(rise * x + intercept * run, run) }));
  return { rise, run, intercept, slope, equation, rows,
    explanation: `Move ${run} units right and ${Math.abs(rise)} units ${rise < 0 ? "down" : "up"}. Slope is ${formatRational(slope)}. The line crosses the y-axis at (0, ${intercept}).${rise === 0 ? " Zero rise gives a horizontal line." : ""}` };
}
export const LINEAR_PRACTICE = [
  { rise: 2, run: 4, intercept: 3 },
  { rise: -3, run: 2, intercept: 1 },
  { rise: 0, run: 3, intercept: -2 },
  { rise: 6, run: 3, intercept: 0 },
] as const;
export function checkSlope(index: number, answer: string) {
  if (!Number.isInteger(index) || index < 0 || index >= LINEAR_PRACTICE.length) throw new RangeError("Unknown practice item");
  const match = /^(-?\d{1,3})(?:\s*\/\s*(-?\d{1,3}))?$/.exec(answer.trim());
  if (!match || Number(match[2] ?? 1) === 0) return { correct: false, feedback: "Enter an integer or fraction with a nonzero denominator, such as -3/2." };
  const value = rational(Number(match[1]), Number(match[2] ?? 1));
  const item = LINEAR_PRACTICE[index];
  const expected = rational(item.rise, item.run);
  const correct = value.numerator === expected.numerator && value.denominator === expected.denominator;
  return { correct, feedback: correct ? "Correct: slope is change in y divided by change in x." :
    "Try again: use rise divided by run, keeping the sign. The y-intercept is a starting value, not the slope." };
}
export function showLinearExploration(state: string, name: string) {
  return ["GUIDED_PRACTICE", "REMEDIATION"].includes(state) &&
    /^(slope[- ]intercept(?: form)?|determine slope from a table|evaluate a linear function)$/i.test(name);
}
