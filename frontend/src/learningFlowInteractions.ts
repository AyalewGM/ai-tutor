import type { LearnContent } from "./types";

export const INTEGER_ADDITION_INTERACTION = "MATH.INT.ADD" as const;

/**
 * Integration-owned route for the reviewed addition-only guided slice.
 * Display names are deliberately ignored; absent or unknown metadata fails closed.
 */
export function integerAdditionEligible(
  state: string,
  learn: Pick<LearnContent, "guided_interactions"> | null | undefined,
): boolean {
  const guidedState = state === "GUIDED_PRACTICE" || state === "REMEDIATION";
  return guidedState &&
    learn?.guided_interactions?.includes(INTEGER_ADDITION_INTERACTION) === true;
}
