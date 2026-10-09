import { useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import type { MathInteractionEvent } from "./interactions";

/** Guided exploration only; never mount in independent assessment. */
export interface InteractiveFractionBarsProps {
  independentAssessment: boolean;
  denominator?: number;
  initialNumerator?: number;
  onFractionChange?: (value: { numerator: number; denominator: number }) => void;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function normalizeFractionParts(numerator: number, denominator: number) {
  const d = Number.isSafeInteger(denominator) ? Math.min(12, Math.max(1, denominator)) : 4;
  const n = Number.isSafeInteger(numerator) ? Math.min(d, Math.max(0, numerator)) : 0;
  return { numerator: n, denominator: d };
}

export function InteractiveFractionBars(props: InteractiveFractionBarsProps) {
  if (props.independentAssessment) return null;
  return <GuidedFractionBars {...props} />;
}

function GuidedFractionBars({
  denominator = 4, initialNumerator = 1, onFractionChange, onMathEvent,
}: InteractiveFractionBarsProps) {
  const initial = normalizeFractionParts(initialNumerator, denominator);
  const [numerator, setNumerator] = useState(initial.numerator);
  const [previousDenominator, setPreviousDenominator] = useState(initial.denominator);
  const d = initial.denominator;
  // Reset local exploration when the example's denominator changes.
  if (previousDenominator !== d) {
    setPreviousDenominator(d);
    setNumerator(initial.numerator);
  }
  const current = previousDenominator === d ? numerator : initial.numerator;
  const update = (next: number) => {
    const value = normalizeFractionParts(next, d);
    setNumerator(value.numerator);
    onFractionChange?.(value);
    onMathEvent?.({ schema_version: 1, type: "FRACTION_SHADING_CHANGED", ...value });
  };
  return (
    <section aria-label="Guided fraction bar exploration" data-mve-family="fractions"
      className="space-y-3 rounded-lg border p-4">
      <h3 className="font-semibold">Explore equal parts</h3>
      <p className="text-sm">A guided example, not an independent assessment question.</p>
      <ProblemVisual spec={{
        type: "fraction_bar",
        numerator: current,
        denominator: d,
        aria_label: `${current} of ${d} equal parts shaded`,
      }} />
      <p role="status" aria-live="polite">{current} of {d} equal parts shaded</p>
      <div className="flex flex-wrap gap-2" aria-label="Fraction exploration controls">
        <button type="button" onClick={() => update(current - 1)} disabled={current === 0}
          className="rounded border px-3 py-2">Shade one fewer part</button>
        <button type="button" onClick={() => update(current + 1)} disabled={current === d}
          className="rounded border px-3 py-2">Shade one more part</button>
        <button type="button" onClick={() => update(0)} disabled={current === 0}
          className="rounded border px-3 py-2">Clear shading</button>
      </div>
      <p className="text-sm">Each part is one-{d === 2 ? "half" : d === 3 ? "third" : d === 4 ? "fourth" : `${d}th`} of the whole.</p>
    </section>
  );
}
