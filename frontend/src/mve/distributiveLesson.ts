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
}

export function buildDistributiveLesson(
  factor: number,
  constant: number,
  variable = "x",
): DistributiveLesson {
  if (!Number.isSafeInteger(factor) || factor <= 0 || factor > 20) {
    throw new RangeError("The outside factor must be an integer from 1 to 20");
  }
  if (!Number.isSafeInteger(constant) || constant < 0 || constant > 20) {
    throw new RangeError("The constant must be an integer from 0 to 20");
  }
  if (!/^[a-z]$/i.test(variable)) {
    throw new RangeError("Variable must be a single letter");
  }

  const original = `${factor}(${variable} + ${constant})`;
  const expanded = `${factor} × ${variable} + ${factor} × ${constant}`;
  const simplified = `${factor}${variable} + ${factor * constant}`;
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
    animation: {
      schema_version: 1,
      purpose: "Show that multiplication distributes to every term in a sum",
      objects: [],
      steps: [
        {
          id: "identify",
          duration_ms: 800,
          description: `Identify ${factor} as the factor outside the parentheses in ${original}.`,
        },
        {
          id: "distribute_variable",
          duration_ms: 800,
          description: `Multiply ${factor} by ${variable}.`,
        },
        {
          id: "distribute_constant",
          duration_ms: 800,
          description: `Also multiply ${factor} by ${constant}; do not skip the second term.`,
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
): { correct: boolean; misconception: "MISSED_SECOND_TERM" | "COEFFICIENT_ERROR" | "CONSTANT_ERROR" | null } {
  if (variableCoefficient === lesson.factor && constantTerm === lesson.constant) {
    return { correct: false, misconception: "MISSED_SECOND_TERM" };
  }
  if (variableCoefficient !== lesson.factor) {
    return { correct: false, misconception: "COEFFICIENT_ERROR" };
  }
  if (constantTerm !== lesson.factor * lesson.constant) {
    return { correct: false, misconception: "CONSTANT_ERROR" };
  }
  return { correct: true, misconception: null };
}
