import type { MathAnimationSpec } from "./animation";
import { isMathAnimationSpec } from "./animation";
import type { MathInteractionEvent } from "./interactions";
import { isMathInteractionEvent } from "./interactions";

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
    !Array.isArray(work.interaction_events) ||
    !work.interaction_events.every(isMathInteractionEvent)
  ) {
    return false;
  }

  if (work.animation !== undefined && !isMathAnimationSpec(work.animation)) {
    return false;
  }

  if (work.animation_step_index !== undefined) {
    if (
      !Number.isInteger(work.animation_step_index) ||
      work.animation_step_index < 0 ||
      work.animation === undefined ||
      work.animation_step_index >= work.animation.steps.length
    ) {
      return false;
    }
  }

  return true;
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
