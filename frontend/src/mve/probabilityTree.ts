import { rational, type Rational } from "./linearExplorer";

export interface ProbabilityStage {
  label: string;
  favorable: number;
  total: number;
}

export interface ProbabilityTreeState {
  first: ProbabilityStage;
  second: ProbabilityStage;
}

export interface ProbabilityBranch {
  label: string;
  probability: Rational;
  favorable: boolean;
}

export interface ProbabilityOutcome {
  label: string;
  probability: Rational;
  favorable: boolean;
}

export interface ProbabilityTreeModel {
  firstBranches: readonly ProbabilityBranch[];
  secondBranches: readonly ProbabilityBranch[];
  outcomes: readonly ProbabilityOutcome[];
  bothProbability: Rational;
  atLeastOneProbability: Rational;
  neitherProbability: Rational;
  sampleSpaceSize: number;
}

export type ProbabilityMeasure = "both" | "at_least_one" | "neither";

export const MIN_PROBABILITY_TOTAL = 2;
export const MAX_PROBABILITY_TOTAL = 12;

export function isProbabilityStage(value: unknown): value is ProbabilityStage {
  if (!value || typeof value !== "object") return false;
  const stage = value as Record<string, unknown>;
  const favorable = stage.favorable;
  const total = stage.total;
  return typeof stage.label === "string" && stage.label.length >= 1 && stage.label.length <= 24 &&
    typeof favorable === "number" && Number.isSafeInteger(favorable) &&
    typeof total === "number" && Number.isSafeInteger(total) &&
    total >= MIN_PROBABILITY_TOTAL && total <= MAX_PROBABILITY_TOTAL &&
    favorable >= 1 && favorable < total;
}

export function isProbabilityTreeState(value: unknown): value is ProbabilityTreeState {
  if (!value || typeof value !== "object") return false;
  const tree = value as Record<string, unknown>;
  return isProbabilityStage(tree.first) && isProbabilityStage(tree.second);
}

export function probabilityTreeModel(state: ProbabilityTreeState): ProbabilityTreeModel {
  if (!isProbabilityTreeState(state)) {
    throw new RangeError("Expected two bounded probability stages with at least one favorable and one non-favorable outcome");
  }
  const firstMiss = state.first.total - state.first.favorable;
  const secondMiss = state.second.total - state.second.favorable;
  const denominator = state.first.total * state.second.total;
  const both = state.first.favorable * state.second.favorable;
  const firstOnly = state.first.favorable * secondMiss;
  const secondOnly = firstMiss * state.second.favorable;
  const neither = firstMiss * secondMiss;
  return {
    firstBranches: [
      { label: state.first.label, probability: rational(state.first.favorable, state.first.total), favorable: true },
      { label: `not ${state.first.label}`, probability: rational(firstMiss, state.first.total), favorable: false },
    ],
    secondBranches: [
      { label: state.second.label, probability: rational(state.second.favorable, state.second.total), favorable: true },
      { label: `not ${state.second.label}`, probability: rational(secondMiss, state.second.total), favorable: false },
    ],
    outcomes: [
      { label: `${state.first.label} and ${state.second.label}`, probability: rational(both, denominator), favorable: true },
      { label: `${state.first.label} and not ${state.second.label}`, probability: rational(firstOnly, denominator), favorable: false },
      { label: `not ${state.first.label} and ${state.second.label}`, probability: rational(secondOnly, denominator), favorable: false },
      { label: `not ${state.first.label} and not ${state.second.label}`, probability: rational(neither, denominator), favorable: false },
    ],
    bothProbability: rational(both, denominator),
    atLeastOneProbability: rational(both + firstOnly + secondOnly, denominator),
    neitherProbability: rational(neither, denominator),
    sampleSpaceSize: denominator,
  };
}

export function updateProbabilityStage(
  state: ProbabilityTreeState,
  stage: "first" | "second",
  field: "favorable" | "total",
  value: number,
): ProbabilityTreeState {
  probabilityTreeModel(state);
  if (!Number.isSafeInteger(value)) throw new RangeError("Probability values must be whole numbers");
  const nextStage = { ...state[stage], [field]: value };
  if (nextStage.favorable >= nextStage.total) nextStage.favorable = nextStage.total - 1;
  if (nextStage.favorable < 1) nextStage.favorable = 1;
  const next = { ...state, [stage]: nextStage };
  probabilityTreeModel(next);
  return next;
}

export const PROBABILITY_TREE_PRACTICE: readonly {
  state: ProbabilityTreeState;
  measure: ProbabilityMeasure;
}[] = [
  { state: { first: { label: "red", favorable: 2, total: 5 }, second: { label: "heads", favorable: 1, total: 2 } }, measure: "both" },
  { state: { first: { label: "blue", favorable: 3, total: 8 }, second: { label: "six", favorable: 1, total: 6 } }, measure: "at_least_one" },
  { state: { first: { label: "green", favorable: 4, total: 7 }, second: { label: "even", favorable: 3, total: 6 } }, measure: "neither" },
  { state: { first: { label: "win", favorable: 5, total: 12 }, second: { label: "bonus", favorable: 3, total: 10 } }, measure: "both" },
];

function parseFraction(answer: string): Rational | null {
  const match = /^(\d{1,4})(?:\s*\/\s*(\d{1,4}))?$/.exec(answer.trim());
  if (!match) return null;
  const denominator = Number(match[2] ?? 1);
  if (denominator === 0) return null;
  return rational(Number(match[1]), denominator);
}

export type ProbabilityMisconception =
  | "INVALID_INPUT"
  | "ADD_BRANCH_PROBABILITIES"
  | "BRANCH_COMPLEMENT_CONFUSION"
  | "AT_LEAST_ONE_AS_BOTH"
  | "RECOMPUTE_PATHS"
  | null;

function sameRational(a: Rational, b: Rational): boolean {
  return a.numerator === b.numerator && a.denominator === b.denominator;
}

export function isEquivalentProbabilityAnswer(
  answer: string,
  expectedNumerator: number,
  expectedDenominator: number,
): boolean {
  const actual = parseFraction(answer);
  if (!actual) return false;
  return sameRational(actual, rational(expectedNumerator, expectedDenominator));
}

export function classifyProbabilityTreeAnswer(index: number, answer: string): {
  correct: boolean;
  misconception: ProbabilityMisconception;
  feedback: string;
} {

  if (!Number.isInteger(index) || index < 0 || index >= PROBABILITY_TREE_PRACTICE.length) {
    throw new RangeError("Unknown probability-tree practice item");
  }
  const actual = parseFraction(answer);
  if (!actual) return { correct: false, misconception: "INVALID_INPUT", feedback: "Enter an integer or fraction with a nonzero denominator." };
  const item = PROBABILITY_TREE_PRACTICE[index];
  const model = probabilityTreeModel(item.state);
  const expected = item.measure === "both" ? model.bothProbability :
    item.measure === "at_least_one" ? model.atLeastOneProbability : model.neitherProbability;
  if (sameRational(actual, expected)) {
    return { correct: true, misconception: null, feedback: "Correct. Explain which paths you combined and why." };
  }
  const first = rational(item.state.first.favorable, item.state.first.total);
  const second = rational(item.state.second.favorable, item.state.second.total);
  const addedNumerator = first.numerator * second.denominator + second.numerator * first.denominator;
  const addedDenominator = first.denominator * second.denominator;
  const added = rational(addedNumerator, addedDenominator);
  if (item.measure === "both" && sameRational(actual, added)) {
    return { correct: false, misconception: "ADD_BRANCH_PROBABILITIES",
      feedback: "Try again. A single independent path combines stage probabilities multiplicatively, not by adding the two stage probabilities." };
  }
  if (item.measure === "at_least_one" && sameRational(actual, model.bothProbability)) {
    return { correct: false, misconception: "AT_LEAST_ONE_AS_BOTH",
      feedback: "Try again. 'At least one' includes three outcome paths, not only the both-favorable path." };
  }
  if (item.measure === "neither" && sameRational(actual, model.bothProbability)) {
    return { correct: false, misconception: "BRANCH_COMPLEMENT_CONFUSION",
      feedback: "Try again. 'Neither' follows both complement branches; use the non-favorable branch at each stage." };
  }
  return { correct: false, misconception: "RECOMPUTE_PATHS",
    feedback: "Try again. Rebuild the requested event from the visible outcome paths before calculating." };
}

export function checkProbabilityTreeAnswer(index: number, answer: string) {
  return classifyProbabilityTreeAnswer(index, answer);
}

export function showProbabilityTreeExploration(state: string, name: string) {
  return ["GUIDED_PRACTICE", "REMEDIATION"].includes(state) &&
    ["Compound Probability", "Probability", "Sample Space", "Probability Trees"].includes(name);
}
