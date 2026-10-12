import { rational, type Rational } from "./linearExplorer";

export function isExplorerDataset(value: unknown): value is number[] {
  return Array.isArray(value) && value.length >= 1 && value.length <= 6 &&
    Array.from(value).every(point => Number.isSafeInteger(point) && point >= 0 && point <= 12);
}
export function datasetModel(values: readonly number[]) {
  if (!isExplorerDataset(values)) throw new RangeError("Expected 1–6 whole-number observations from 0 to 12");
  const sorted = [...values].sort((a, b) => a - b);
  const count = values.length;
  const sum = values.reduce((total, value) => total + value, 0);
  const middle = Math.floor(count / 2);
  const median = count % 2 ? rational(sorted[middle], 1) : rational(sorted[middle - 1] + sorted[middle], 2);
  return { sorted, count, sum, mean: rational(sum, count), median,
    range: sorted[count - 1] - sorted[0],
    frequencies: Array.from({ length: 13 }, (_, value) => ({ value, count: values.filter(point => point === value).length })),
  };
}
export function replaceObservation(values: readonly number[], index: number, value: number): number[] {
  datasetModel(values);
  if (!Number.isInteger(index) || index < 0 || index >= values.length || !Number.isSafeInteger(value) || value < 0 || value > 12) throw new RangeError("Unsupported observation change");
  return values.map((point, i) => i === index ? value : point);
}
export type DatasetMeasure = "mean" | "median" | "range";
export const DOT_PRACTICE: readonly { values: readonly number[]; measure: DatasetMeasure }[] = [
  { values: [1, 2, 6], measure: "mean" },
  { values: [9, 2, 4, 3], measure: "median" },
  { values: [1, 1, 1, 9], measure: "mean" },
  { values: [0, 0, 0], measure: "range" },
];
export function checkDatasetAnswer(index: number, answer: string) {
  if (!Number.isInteger(index) || index < 0 || index >= DOT_PRACTICE.length) throw new RangeError("Unknown practice item");
  const match = /^(\d{1,3})(?:\s*\/\s*(\d{1,3}))?$/.exec(answer.trim());
  if (!match || Number(match[2] ?? 1) === 0) return { correct: false, feedback: "Enter an integer or fraction with a nonzero denominator." };
  const actual = rational(Number(match[1]), Number(match[2] ?? 1));
  const item = DOT_PRACTICE[index];
  const model = datasetModel(item.values);
  const expected: Rational = item.measure === "range" ? rational(model.range, 1) : model[item.measure];
  const correct = actual.numerator === expected.numerator && actual.denominator === expected.denominator;
  const hint = item.measure === "mean" ? "Add every observation and divide by the number of observations, including repeated values." :
    item.measure === "median" ? "Sort first. For an even count, average the two middle observations." : "Subtract the smallest observation from the largest.";
  return { correct, feedback: correct ? "Correct. " + hint : "Try again. " + hint };
}
export function showDotPlotExploration(state: string, name: string) {
  return ["GUIDED_PRACTICE", "REMEDIATION"].includes(state) &&
    ["Center and Spread", "Center", "Find the mean", "Find the median"].includes(name);
}
