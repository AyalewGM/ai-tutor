import type { MathObject, MathTransformation } from "./contracts";

export type AnimationEasing = "linear" | "ease_in_out";

export interface AnimationStep {
  id: string;
  duration_ms: number;
  description: string;
  transformation?: MathTransformation;
  reveal_object_ids?: readonly string[];
}

export interface MathAnimationSpec {
  schema_version: 1;
  purpose: string;
  objects: readonly MathObject[];
  steps: readonly AnimationStep[];
  easing?: AnimationEasing;
  reduced_motion: "show_final_state" | "step_without_motion";
}

export function isMathAnimationSpec(value: unknown): value is MathAnimationSpec {
  if (!value || typeof value !== "object") return false;
  const spec = value as Partial<MathAnimationSpec>;
  return (
    spec.schema_version === 1 &&
    typeof spec.purpose === "string" &&
    Array.isArray(spec.objects) &&
    Array.isArray(spec.steps) &&
    (spec.reduced_motion === "show_final_state" ||
      spec.reduced_motion === "step_without_motion")
  );
}
