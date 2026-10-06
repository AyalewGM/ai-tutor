import type { MathAnimationSpec } from "./animation";
import { applyMathTransformation } from "./applyTransformation";
import type { MathObject } from "./contracts";

export interface AnimationFrame {
  step_id: string;
  description: string;
  objects: readonly MathObject[];
}

function replaceObject(
  objects: readonly MathObject[],
  source: MathObject,
  transformed: MathObject,
): readonly MathObject[] {
  if (source.id) {
    return objects.map((object) =>
      object.id === source.id ? transformed : object,
    );
  }
  return objects.map((object) => (object === source ? transformed : object));
}

/**
 * Materializes the mathematical state for every animation step.
 *
 * Frames are deterministic and renderer-independent, so replay, tests and
 * accessibility descriptions observe the same mathematical state as visuals.
 */
export function buildAnimationFrames(
  spec: MathAnimationSpec,
): readonly AnimationFrame[] {
  let objects: readonly MathObject[] = [...spec.objects];

  return spec.steps.map((step) => {
    if (step.transformation) {
      const transformed = applyMathTransformation(step.transformation);
      objects = replaceObject(
        objects,
        step.transformation.source,
        transformed,
      );
    }

    return {
      step_id: step.id,
      description: step.description,
      objects: [...objects],
    };
  });
}

export function replayAnimationFrame(
  spec: MathAnimationSpec,
  stepIndex: number,
): AnimationFrame | null {
  const frames = buildAnimationFrames(spec);
  if (frames.length === 0) return null;
  const index = Math.max(0, Math.min(stepIndex, frames.length - 1));
  return frames[index];
}
