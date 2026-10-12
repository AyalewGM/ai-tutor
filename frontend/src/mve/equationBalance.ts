import { rational, type Rational } from "./linearExplorer";

export interface BalancePan { x_count: number; units: number }
export interface BalanceEquation { left: BalancePan; right: BalancePan }
export type BalanceOperation = "add_unit" | "remove_unit" | "remove_x" | "divide_two" | "divide_three";
export const BALANCE_OPERATIONS: readonly BalanceOperation[] = ["add_unit", "remove_unit", "remove_x", "divide_two", "divide_three"];
export const BALANCE_LABELS: Record<BalanceOperation, string> = {
  add_unit: "Add 1 to both sides", remove_unit: "Subtract 1 from both sides",
  remove_x: "Subtract x from both sides", divide_two: "Divide both sides by 2", divide_three: "Divide both sides by 3",
};
export const BALANCE_EXAMPLES: readonly BalanceEquation[] = [
  { left: { x_count: 2, units: 4 }, right: { x_count: 0, units: 10 } },
  { left: { x_count: 3, units: 2 }, right: { x_count: 1, units: 8 } },
  { left: { x_count: 3, units: 3 }, right: { x_count: 0, units: 12 } },
];
export function isBalanceEquation(value: unknown): value is BalanceEquation {
  if (!value || typeof value !== "object") return false;
  const equation = value as BalanceEquation;
  return [equation.left, equation.right].every(pan => pan &&
    Number.isSafeInteger(pan.x_count) && pan.x_count >= 0 && pan.x_count <= 3 &&
    Number.isSafeInteger(pan.units) && pan.units >= 0 && pan.units <= 12) &&
    equation.left.x_count > equation.right.x_count && equation.right.units >= equation.left.units;
}
export function balanceSolution(equation: BalanceEquation): Rational {
  if (!isBalanceEquation(equation)) throw new RangeError("Unsupported balance equation");
  return rational(equation.right.units - equation.left.units, equation.left.x_count - equation.right.x_count);
}
export function balanceExpression(equation: BalanceEquation) {
  if (!isBalanceEquation(equation)) throw new RangeError("Unsupported balance equation");
  const side = (pan: BalancePan) => [pan.x_count ? `${pan.x_count === 1 ? "" : pan.x_count}x` : "", pan.units ? String(pan.units) : ""].filter(Boolean).join(" + ") || "0";
  return `${side(equation.left)} = ${side(equation.right)}`;
}
/** Null means the concrete whole-tile model cannot perform this operation. */
export function applyBalanceOperation(equation: BalanceEquation, operation: BalanceOperation): BalanceEquation | null {
  if (!isBalanceEquation(equation) || !BALANCE_OPERATIONS.includes(operation)) return null;
  const transform = (pan: BalancePan): BalancePan => {
    if (operation === "add_unit") return { ...pan, units: pan.units + 1 };
    if (operation === "remove_unit") return { ...pan, units: pan.units - 1 };
    if (operation === "remove_x") return { ...pan, x_count: pan.x_count - 1 };
    const divisor = operation === "divide_two" ? 2 : 3;
    return { x_count: pan.x_count / divisor, units: pan.units / divisor };
  };
  const next = { left: transform(equation.left), right: transform(equation.right) };
  return isBalanceEquation(next) ? next : null;
}
export function isIsolated(equation: BalanceEquation) {
  return isBalanceEquation(equation) && equation.left.x_count === 1 && equation.left.units === 0 && equation.right.x_count === 0;
}
export const BALANCE_PRACTICE: readonly BalanceEquation[] = [
  { left: { x_count: 2, units: 2 }, right: { x_count: 0, units: 10 } },
  { left: { x_count: 3, units: 1 }, right: { x_count: 1, units: 5 } },
  { left: { x_count: 2, units: 1 }, right: { x_count: 0, units: 6 } },
];
export function checkBalanceAnswer(index: number, answer: string) {
  if (!Number.isInteger(index) || index < 0 || index >= BALANCE_PRACTICE.length) throw new RangeError("Unknown practice item");
  const match = /^(\d{1,3})(?:\s*\/\s*(\d{1,3}))?$/.exec(answer.trim());
  if (!match || Number(match[2] ?? 1) === 0) return { correct: false, feedback: "Enter a nonnegative integer or fraction with a nonzero denominator." };
  const value = rational(Number(match[1]), Number(match[2] ?? 1));
  const expected = balanceSolution(BALANCE_PRACTICE[index]);
  const correct = value.numerator === expected.numerator && value.denominator === expected.denominator;
  return { correct, feedback: correct ? "Correct. Substitution makes the two sides equal." : "Try again. Remove equal terms from both sides, then divide both sides by the remaining coefficient of x." };
}
export function showBalanceExploration(state: string, name: string) {
  return ["GUIDED_PRACTICE", "REMEDIATION"].includes(state) &&
    ["One-Step Equations", "Two-Step and Multi-Step Equations", "Multi-Step Equations with Variables on Both Sides"].includes(name);
}
