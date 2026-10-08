import { useEffect, useState } from "react";
import type { AnimationStep, MathAnimationSpec } from "./animation";

export interface PedagogicalAnimationProps {
  spec: MathAnimationSpec;
  autoPlay?: boolean;
  onStepChange?: (step: AnimationStep, index: number) => void;
}

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

/** Playback controls work with any existing MathAnimationSpec renderer. */
export function PedagogicalAnimation({
  spec,
  autoPlay = true,
  onStepChange,
}: PedagogicalAnimationProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [stepIndex, setStepIndex] = useState(0);
  const [playing, setPlaying] = useState(autoPlay);
  const lastIndex = Math.max(0, spec.steps.length - 1);
  const index = Math.min(stepIndex, lastIndex);
  const effectiveIndex =
    prefersReducedMotion && spec.reduced_motion === "show_final_state"
      ? lastIndex
      : index;
  const step = spec.steps[effectiveIndex];

  useEffect(() => {
    setStepIndex(0);
    setPlaying(autoPlay);
  }, [spec, autoPlay]);

  useEffect(() => {
    if (prefersReducedMotion) setPlaying(false);
  }, [prefersReducedMotion]);

  useEffect(() => {
    if (!step) return;
    onStepChange?.(step, effectiveIndex);
  }, [step, effectiveIndex, onStepChange]);

  useEffect(() => {
    if (!playing || prefersReducedMotion || index >= lastIndex) return;
    const current = spec.steps[index];
    if (!current) return;
    const timer = window.setTimeout(() => {
      setStepIndex((value) => Math.min(value + 1, lastIndex));
      if (index + 1 >= lastIndex) setPlaying(false);
    }, Math.max(0, current.duration_ms));
    return () => window.clearTimeout(timer);
  }, [index, lastIndex, playing, prefersReducedMotion, spec.steps]);

  if (!step) return <div role="status">No animation steps are available.</div>;

  return (
    <section aria-label={spec.purpose} className="space-y-2">
      <p>{spec.purpose}</p>
      <p role="status" aria-live="polite" aria-atomic="true">
        <strong>Step {effectiveIndex + 1} of {spec.steps.length}:</strong>{" "}
        {step.description}
      </p>
      <div role="group" aria-label="Animation playback controls" className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => {
            if (playing) setPlaying(false);
            else if (!prefersReducedMotion) {
              if (index === lastIndex) setStepIndex(0);
              setPlaying(true);
            }
          }}
          disabled={prefersReducedMotion || lastIndex === 0}
          aria-label={playing ? "Pause animation" : "Play animation"}
        >
          {playing ? "Pause" : "Play"}
        </button>
        <button
          type="button"
          onClick={() => { setPlaying(false); setStepIndex((i) => Math.max(0, i - 1)); }}
          disabled={effectiveIndex === 0 || spec.reduced_motion === "show_final_state" && prefersReducedMotion}
        >
          Previous step
        </button>
        <button
          type="button"
          onClick={() => { setPlaying(false); setStepIndex((i) => Math.min(lastIndex, i + 1)); }}
          disabled={effectiveIndex === lastIndex}
        >
          Next step
        </button>
        <button
          type="button"
          onClick={() => { setStepIndex(0); setPlaying(!prefersReducedMotion && lastIndex > 0); }}
          disabled={lastIndex === 0 || prefersReducedMotion && spec.reduced_motion === "show_final_state"}
        >
          Replay
        </button>
      </div>
      {prefersReducedMotion && (
        <p className="text-sm text-muted-foreground">
          Reduced motion is on. Use Previous step and Next step to explore without animation.
        </p>
      )}
    </section>
  );
}
