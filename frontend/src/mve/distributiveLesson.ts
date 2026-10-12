import type { MathAnimationSpec } from "./animation";

/**
 * Canonical distributive-property explanation data.
 *
 * The MVE renderer owns presentation. These semantic steps never grade learner
 * work and must not be exposed as answer hints in independent assessments.
 */
export interface DistributiveLesson {
  factor: number;
  variable: string;
  constant: number;
  original: string;
  expanded: string;
  simplified: string;
  animation: MathAnimationSpec;
  areaModel: {
    type: "area_model";
    a: number;
    b: number;
    aria_label: string;
  };
  algebraTiles: {
    type: "algebra_tiles";
    aria_label: string;
    groups: Array<{
      key: string;
      terms: Array<{
        coefficient: number;
        variable?: string | null;
        degree: number;
        label: string;
      }>;
    }>;
  };
}

export type DistributiveMisconception =
  | "MISSED_SECOND_TERM"
  | "DROPPED_NEGATIVE"
  | "COEFFICIENT_ERROR"
  | "CONSTANT_ERROR";

function signedSum(value: number): string {
  return `${value < 0 ? "−" : "+"} ${Math.abs(value)}`;
}

function variableTerm(coefficient: number, variable: string): string {
  if (coefficient === 1) return variable;
  if (coefficient === -1) return `−${variable}`;
  return `${coefficient}${variable}`;
}

export function buildDistributiveLesson(
  factor: number,
  constant: number,
  variable = "x",
): DistributiveLesson {
  if (!Number.isSafeInteger(factor) || factor === 0 || Math.abs(factor) > 12) {
    throw new RangeError("The outside factor must be a nonzero integer from -12 to 12");
  }
  if (!Number.isSafeInteger(constant) || Math.abs(constant) > 12) {
    throw new RangeError("The constant must be an integer from -12 to 12");
  }
  if (!/^[a-z]$/i.test(variable)) {
    throw new RangeError("Variable must be a single letter");
  }

  const product = factor * constant;
  const original = `${factor}(${variable} ${signedSum(constant)})`;
  const expanded = `${factor} × ${variable} + ${factor} × (${constant})`;
  const simplified = `${variableTerm(factor, variable)} ${signedSum(product)}`;
  return {
    factor,
    constant,
    variable,
    original,
    expanded,
    simplified,
    areaModel: {
      type: "area_model",
      a: factor,
      b: constant,
      aria_label: `Area model: ${factor} rows of one ${variable} unit and ${constant} unit squares, total ${simplified}`,
    },
    algebraTiles: {
      type: "algebra_tiles",
      aria_label: `Signed algebra tiles after distribution: ${variableTerm(factor, variable)} and ${product} give ${simplified}`,
      groups: [
        {
          key: `${variable} terms`,
          terms: [{ coefficient: factor, variable, degree: 1, label: variableTerm(factor, variable) }],
        },
        {
          key: "constant terms",
          terms: [{ coefficient: product, degree: 0, label: String(product) }],
        },
      ],
    },
    animation: {
      schema_version: 1,
      purpose: "Show that multiplication distributes to every term in a sum",
      objects: [],
      steps: [
        {
          id: "identify",
          duration_ms: 800,
          description: `Identify ${factor}, including its sign, as the factor outside the parentheses in ${original}.`,
        },
        {
          id: "distribute_variable",
          duration_ms: 800,
          description: `Multiply ${factor} by ${variable}; the variable term becomes ${variableTerm(factor, variable)}.`,
        },
        {
          id: "distribute_constant",
          duration_ms: 800,
          description: `Also multiply ${factor} by ${constant}; use the sign rules and do not skip the second term.`,
        },
        {
          id: "simplify",
          duration_ms: 800,
          description: `Simplify to ${simplified}.`,
        },
      ],
      easing: "ease_in_out",
      reduced_motion: "step_without_motion",
    },
  };
}

/** Deterministic, misconception-aware semantic validation. */
export function checkDistributiveCoefficients(
  lesson: DistributiveLesson,
  variableCoefficient: number,
  constantTerm: number,
): { correct: boolean; misconception: DistributiveMisconception | null } {
  const expectedConstant = lesson.factor * lesson.constant;
  if (variableCoefficient === lesson.factor && constantTerm === expectedConstant) {
    return { correct: true, misconception: null };
  }
  if (lesson.factor < 0 &&
      variableCoefficient === Math.abs(lesson.factor) &&
      constantTerm === Math.abs(lesson.factor) * lesson.constant) {
    return { correct: false, misconception: "DROPPED_NEGATIVE" };
  }
  if (variableCoefficient === lesson.factor && constantTerm === lesson.constant) {
    return { correct: false, misconception: "MISSED_SECOND_TERM" };
  }
  if (variableCoefficient !== lesson.factor) {
    return { correct: false, misconception: "COEFFICIENT_ERROR" };
  }
  if (constantTerm !== expectedConstant) {
    return { correct: false, misconception: "CONSTANT_ERROR" };
  }
  return { correct: false, misconception: "CONSTANT_ERROR" };
}
