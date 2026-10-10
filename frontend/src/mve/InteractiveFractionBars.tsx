import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import type { MathInteractionEvent } from "./interactions";
import { normalizeFractionParts, changeShadedParts, describeFraction, compareFractions, describeFractionComparison, isValidFractionParts, type FractionParts } from "./fractionMath";

/** Guided exploration only; never mount in independent assessment. */
export interface InteractiveFractionBarsProps {
  independentAssessment: boolean;
  denominator?: number;
  initialNumerator?: number;
  /** Optional guided comparison target. Invalid targets are not rendered. */
  compareWith?: FractionParts;
  onFractionChange?: (value: { numerator: number; denominator: number }) => void;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function InteractiveFractionBars(props: InteractiveFractionBarsProps) {
  if (props.independentAssessment) return null;
  return <GuidedFractionBars {...props} />;
}

function GuidedFractionBars({
  denominator = 4, initialNumerator = 1, compareWith, onFractionChange, onMathEvent,
}: InteractiveFractionBarsProps) {
  const statusId = useId();
  const comparisonStatusId = useId();
  const initial = normalizeFractionParts(initialNumerator, denominator);
  const [numerator, setNumerator] = useState(initial.numerator);
  const [previousDenominator, setPreviousDenominator] = useState(initial.denominator);
  const d = initial.denominator;
  const target = isValidFractionParts(compareWith) ? compareWith : null;
  const [showComparison, setShowComparison] = useState(false);
  const [lastTargetKey, setLastTargetKey] = useState<string | null>(null);
  const targetKey = target ? `${target.numerator}/${target.denominator}` : null;
  if (lastTargetKey !== targetKey) {
    setLastTargetKey(targetKey);
    setShowComparison(false);
  }
  // Reset local exploration when the example's denominator changes.
  if (previousDenominator !== d) {
    setPreviousDenominator(d);
    setNumerator(initial.numerator);
    setShowComparison(false);
  }
  const current = previousDenominator === d ? numerator : initial.numerator;
  const update = (next: number) => {
    const value = normalizeFractionParts(next, d);
    if (value.numerator === current) return;
    setNumerator(value.numerator);
    setShowComparison(false);
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
      <p id={statusId} role="status" aria-live="polite" aria-atomic="true">{describeFraction({ numerator: current, denominator: d })}</p>
      <div role="group" className="flex flex-wrap gap-2" aria-label="Fraction exploration controls">
        <button type="button" onClick={() => update(changeShadedParts({ numerator: current, denominator: d }, -1).numerator)} disabled={current === 0} aria-describedby={statusId}
          className="rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2">Shade one fewer part</button>
        <button type="button" onClick={() => update(changeShadedParts({ numerator: current, denominator: d }, 1).numerator)} disabled={current === d} aria-describedby={statusId}
          className="rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2">Shade one more part</button>
        <button type="button" onClick={() => update(0)} disabled={current === 0} aria-describedby={statusId}
          className="rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2">Clear shading</button>
      </div>
      {target && (
        <div className="space-y-2" aria-label="Guided fraction comparison">
          <p className="text-sm">Compare your shaded fraction with {target.numerator}/{target.denominator}.</p>
          <ProblemVisual spec={{
            type: "fraction_bar", numerator: target.numerator, denominator: target.denominator,
            aria_label: `${target.numerator} of ${target.denominator} equal parts shaded in comparison bar`,
          }} />
          <button type="button" aria-describedby={comparisonStatusId}
            className="rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
            onClick={() => {
              const left = { numerator: current, denominator: d };
              const relation = compareFractions(left, target);
              if (relation === null) return;
              setShowComparison(true);
              onMathEvent?.({ schema_version: 1, type: "FRACTION_COMPARED", left, right: target, relation });
            }}>Explain comparison</button>
          {showComparison && (
            <p id={comparisonStatusId} role="status" aria-live="polite" aria-atomic="true">
              {describeFractionComparison({ numerator: current, denominator: d }, target)}
            </p>
          )}
        </div>
      )}
      <p className="text-sm">Each part is one-{d === 2 ? "half" : d === 3 ? "third" : d === 4 ? "fourth" : `${d}th`} of the whole.</p>
    </section>
  );
}
