import type { LearnContent } from "./types";

export const INTEGER_ADDITION_INTERACTION = "MATH.INT.ADD" as const;

export const MTH1W_EQUATION_CURRICULUM = {
  name: "Grade 9 Mathematics (MTH1W)",
  jurisdiction: "Ontario, Canada",
} as const;

export const MTH1W_EQUATION_SKILLS = [
  "Two-Step and Multi-Step Equations",
  "Multi-Step Equations with Variables on Both Sides",
] as const;

export interface EquationLearningIdentity {
  curriculumName: string;
  jurisdiction: string | null;
  skillName: string;
}

/**
 * Integration-owned route for the reviewed addition-only guided slice.
 * Display names are deliberately ignored; absent or unknown metadata fails closed.
 */
export function integerAdditionEligible(
  state: string,
  learn: Pick<LearnContent, "guided_interactions"> | null | undefined,
): boolean {
  const guidedState = state === "GUIDED_PRACTICE" || state === "REMEDIATION";
  const interactions = learn?.guided_interactions;
  return guidedState &&
    Array.isArray(interactions) &&
    interactions.every((identity) => typeof identity === "string") &&
    interactions.includes(INTEGER_ADDITION_INTERACTION);
}

/**
 * Draft-only route for the reviewed MTH1W equation-equivalence slice.
 *
 * The workspace API does not currently expose curriculum-local skill codes.
 * Until that owner-controlled contract changes, all three stable fields already
 * present in the response must match exactly. The caller must also opt in via
 * the default-off runtime gate. Missing or display-similar metadata fails closed.
 */
export function equationEquivalenceEligible(
  state: string,
  identity: EquationLearningIdentity | null | undefined,
  draftRuntimeEnabled = false,
): boolean {
  if (draftRuntimeEnabled !== true || !identity) return false;
  if (state !== "GUIDED_PRACTICE" && state !== "REMEDIATION") return false;
  return identity.curriculumName === MTH1W_EQUATION_CURRICULUM.name &&
    identity.jurisdiction === MTH1W_EQUATION_CURRICULUM.jurisdiction &&
    MTH1W_EQUATION_SKILLS.some((skillName) => skillName === identity.skillName);
}

/** Selects a reproducible reviewed example without exposing any answer. */
export function equationEquivalenceExampleIndex(seed: string, skillName: string): number {
  if (skillName === "Multi-Step Equations with Variables on Both Sides") return 2;
  let hash = 2166136261;
  for (const character of seed) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) % 2;
}
