import type { MathAnimationSpec } from "./animation";
import { isMathAnimationSpec } from "./animation";
import type { MathInteractionEvent } from "./interactions";

export interface PersistedMathWorkV1 {
  schema_version: 1;
  session_id: string;
  interaction_events: readonly MathInteractionEvent[];
  animation?: MathAnimationSpec;
  animation_step_index?: number;
}

/**
 * Minimal versioned envelope for replayable learner math work.
 *
 * This stores semantic mathematical evidence only. Raw pointer coordinates,
 * rendered pixels, screenshots, and inferred visual state do not belong here.
 */
export function isPersistedMathWorkV1(
  value: unknown,
): value is PersistedMathWorkV1 {
  if (!value || typeof value !== "object") return false;
  const work = value as Partial<PersistedMathWorkV1>;

  if (
    work.schema_version !== 1 ||
    typeof work.session_id !== "string" ||
    !Array.isArray(work.interaction_events)
  ) {
    return false;
  }

  if (work.animation !== undefined && !isMathAnimationSpec(work.animation)) {
    return false;
  }

  return (
    work.animation_step_index === undefined ||
    (Number.isInteger(work.animation_step_index) &&
      (work.animation_step_index as number) >= 0)
  );
}

export function serializeMathWork(work: PersistedMathWorkV1): string {
  return JSON.stringify(work);
}

export function parseMathWork(serialized: string): PersistedMathWorkV1 | null {
  try {
    const value: unknown = JSON.parse(serialized);
    return isPersistedMathWorkV1(value) ? value : null;
  } catch {
    return null;
  }
}
