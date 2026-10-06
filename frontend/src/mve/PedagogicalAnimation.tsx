import { useEffect, useMemo, useState } from "react";
import type { MathAnimationSpec } from "./animation";

export interface PedagogicalAnimationProps { spec: MathAnimationSpec; }

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduced;
}

export function PedagogicalAnimation({ spec }: PedagogicalAnimationProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [stepIndex, setStepIndex] = useState(0);
  const lastIndex = Math.max(0, spec.steps.length - 1);
  const effectiveIndex = useMemo(
    () => prefersReducedMotion && spec.reduced_motion === "show_final_state"
      ? lastIndex : Math.min(stepIndex, lastIndex),
    [lastIndex, prefersReducedMotion, spec.reduced_motion, stepIndex],
  );
  const step = spec.steps[effectiveIndex];

  useEffect(() => {
    if (prefersReducedMotion || spec.steps.length < 2) return;
    const current = spec.steps[stepIndex];
    if (!current || stepIndex >= lastIndex) return;
    const timer = window.setTimeout(
      () => setStepIndex((index) => Math.min(index + 1, lastIndex)),
      Math.max(0, current.duration_ms),
    );
    return () => window.clearTimeout(timer);
  }, [lastIndex, prefersReducedMotion, spec.steps, stepIndex]);

  if (!step) return <div role="status">No animation steps are available.</div>;

  return (
    <section aria-label={spec.purpose}>
      <p>{spec.purpose}</p>
      <div aria-live="polite" aria-atomic="true">
        <strong>Step {effectiveIndex + 1} of {spec.steps.length}:</strong>{" "}
        {step.description}
      </div>
      {prefersReducedMotion && spec.reduced_motion === "step_without_motion" && (
        <div>
          <button type="button" onClick={() => setStepIndex((i) => Math.max(0, i - 1))} disabled={effectiveIndex === 0}>
            Previous step
          </button>
          <button type="button" onClick={() => setStepIndex((i) => Math.min(lastIndex, i + 1))} disabled={effectiveIndex === lastIndex}>
            Next step
          </button>
        </div>
      )}
    </section>
  );
}
