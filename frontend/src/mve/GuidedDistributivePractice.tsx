import { useEffect, useState } from "react";
import { buildDistributiveLesson, checkDistributiveCoefficients } from "./distributiveLesson";

/** Guided-only activity. Never mount while an independent assessment is active. */
export function GuidedDistributivePractice({ factor = 3, constant = 4, independentAssessment = false }: {
  factor?: number; constant?: number; independentAssessment?: boolean;
}) {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [coefficient, setCoefficient] = useState("");
  const [term, setTerm] = useState("");
  const [feedback, setFeedback] = useState("");
  if (independentAssessment) return null;
  const lesson = buildDistributiveLesson(factor, constant);
  const steps = lesson.animation.steps;
  const current = steps[step];
  useEffect(() => {
    if (!playing) return;
    if (step >= steps.length - 1) { setPlaying(false); return; }
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    const timeout = window.setTimeout(() => setStep(index => index + 1), reducedMotion ? 0 : current.duration_ms);
    return () => window.clearTimeout(timeout);
  }, [playing, step, steps.length, current.duration_ms]);
  const check = () => {
    if (!/^-?\d+$/.test(coefficient.trim()) || !/^-?\d+$/.test(term.trim())) {
      setFeedback("Enter whole-number coefficients in both fields.");
      return;
    }
    const result = checkDistributiveCoefficients(lesson, Number(coefficient), Number(term));
    setFeedback(result.correct ? "Correct: both terms were multiplied." :
      result.misconception === "MISSED_SECOND_TERM" ? "Check the constant term: distribute to both terms." :
      result.misconception === "COEFFICIENT_ERROR" ? "Check the coefficient of x against the outside factor." :
      "Recheck the constant product using the area model.");
  };
  return <section aria-label="Guided distributive property lesson" data-mve-family="distributive">
    <h3>Distribute across both terms</h3>
    <p>{lesson.original}</p>
    <p role="status" aria-live="polite">Step {step + 1} of {steps.length}: {current.description}</p>
    <div role="group" aria-label="Explanation controls">
      <button type="button" onClick={() => setPlaying(!playing)} aria-pressed={playing}>{playing ? "Pause" : "Play"}</button>
      <button type="button" onClick={() => { setPlaying(false); setStep(Math.max(0, step - 1)); }} disabled={step === 0}>Previous step</button>
      <button type="button" onClick={() => { setPlaying(false); setStep(Math.min(steps.length - 1, step + 1)); }} disabled={step === steps.length - 1}>Next step</button>
      <button type="button" onClick={() => { setPlaying(false); setStep(0); }}>Replay</button>
    </div>
    <p>Use the controls to read each explanation step. No motion is required.</p>
    <fieldset><legend>Try the expanded expression: coefficient of x and constant</legend>
      <label>Coefficient of x <input inputMode="numeric" value={coefficient} onChange={e => setCoefficient(e.target.value)} /></label>
      <label>Constant term <input inputMode="numeric" value={term} onChange={e => setTerm(e.target.value)} /></label>
      <button type="button" onClick={check}>Check my work</button>
    </fieldset>
    <p role="status" aria-live="polite">{feedback}</p>
  </section>;
}
