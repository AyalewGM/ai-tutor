import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import type { MathInteractionEvent } from "./interactions";
import {
  isValidFractionParts,
  planFractionAddition,
  describeFractionAddition,
  type FractionParts,
} from "./fractionMath";

/** Guided exploration only; never mount in independent assessment. */
export interface InteractiveFractionAdditionProps {
  independentAssessment: boolean;
  first?: FractionParts;
  second?: FractionParts;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function InteractiveFractionAddition(props: InteractiveFractionAdditionProps) {
  if (props.independentAssessment) return null;
  return <GuidedFractionAddition {...props} />;
}

type Stage = "native" | "common" | "combined";

function GuidedFractionAddition({
  first = { numerator: 1, denominator: 4 },
  second = { numerator: 1, denominator: 2 },
  onMathEvent,
}: InteractiveFractionAdditionProps) {
  const statusId = useId();
  const plan =
    isValidFractionParts(first) && isValidFractionParts(second)
      ? planFractionAddition(first, second)
      : null;
  const planKey = plan
    ? `${first.numerator}/${first.denominator}+${second.numerator}/${second.denominator}`
    : "invalid";
  const [stage, setStage] = useState<Stage>("native");
  const [previousKey, setPreviousKey] = useState(planKey);
  if (previousKey !== planKey) {
    setPreviousKey(planKey);
    setStage("native");
  }
  const current = previousKey === planKey ? stage : "native";
  if (plan === null) {
    return (
      <section aria-label="Guided fraction addition" data-mve-family="fractions"
        className="space-y-3 rounded-lg border p-4">
        <h3 className="font-semibold">Add fractions with equal parts</h3>
        <p className="text-sm">A guided example, not an independent assessment question.</p>
        <p className="text-sm" role="status">
          These fractions cannot be shown with the bounded bar model.
        </p>
      </section>
    );
  }
  const showCommon = current !== "native";
  const left = showCommon ? plan.first_scaled : first;
  const right = showCommon ? plan.second_scaled : second;
  return (
    <section aria-label="Guided fraction addition" data-mve-family="fractions"
      className="space-y-3 rounded-lg border p-4">
      <h3 className="font-semibold">Add fractions with equal parts</h3>
      <p className="text-sm">A guided example, not an independent assessment question.</p>
      <p className="text-sm">
        {first.numerator}/{first.denominator} + {second.numerator}/{second.denominator}
      </p>
      <ProblemVisual spec={{
        type: "fraction_bar", numerator: left.numerator, denominator: left.denominator,
        aria_label: `First addend: ${left.numerator} of ${left.denominator} equal parts shaded`,
      }} />
      <ProblemVisual spec={{
        type: "fraction_bar", numerator: right.numerator, denominator: right.denominator,
        aria_label: `Second addend: ${right.numerator} of ${right.denominator} equal parts shaded`,
      }} />
      <div role="group" className="flex flex-wrap gap-2" aria-label="Fraction addition controls">
        <button type="button" disabled={showCommon} aria-describedby={statusId}
          className="rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
          onClick={() => setStage("common")}>Make equal parts</button>
        <button type="button" disabled={current !== "common"} aria-describedby={statusId}
          className="rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
          onClick={() => {
            setStage("combined");
            onMathEvent?.({
              schema_version: 1, type: "FRACTION_ADDITION_EXPLORED",
              first, second,
              common_denominator: plan.common_denominator,
              sum_numerator: plan.sum_numerator,
              sum_denominator: plan.sum_denominator,
            });
          }}>Combine the parts</button>
      </div>
      {current === "combined" && plan.sum_numerator <= plan.sum_denominator && (
        <ProblemVisual spec={{
          type: "fraction_bar", numerator: plan.sum_numerator, denominator: plan.sum_denominator,
          aria_label: `Sum: ${plan.sum_numerator} of ${plan.sum_denominator} equal parts shaded`,
        }} />
      )}
      <p id={statusId} role="status" aria-live="polite" aria-atomic="true">
        {current === "combined"
          ? describeFractionAddition(plan)
          : current === "common"
            ? `Both bars now show ${plan.common_denominator} equal parts. Combine them to see the sum.`
            : "Make equal parts first, then combine the shaded parts to see the sum."}
      </p>
    </section>
  );
}
