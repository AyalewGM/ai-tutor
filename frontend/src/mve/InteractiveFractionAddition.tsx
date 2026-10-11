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
  independentAssessment?: boolean;
  first?: FractionParts;
  second?: FractionParts;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function InteractiveFractionAddition(props: InteractiveFractionAdditionProps) {
  // Fail closed for absent or malformed runtime assessment state.
  if (props.independentAssessment !== false) return null;
  const first = props.first ?? { numerator: 1, denominator: 4 };
  const second = props.second ?? { numerator: 1, denominator: 2 };
  const plan = planFractionAddition(first, second);
  const lifecycleKey = plan
    ? `${first.numerator}/${first.denominator}+${second.numerator}/${second.denominator}`
    : "invalid";
  return <GuidedFractionAddition key={lifecycleKey} {...props} first={first} second={second} />;
}

type Stage = "native" | "common" | "combined";
type GuidedFractionAdditionProps = InteractiveFractionAdditionProps & {
  first: FractionParts;
  second: FractionParts;
};

function GuidedFractionAddition({
  first,
  second,
  onMathEvent,
}: GuidedFractionAdditionProps) {
  const statusId = useId();
  const plan =
    isValidFractionParts(first) && isValidFractionParts(second)
      ? planFractionAddition(first, second)
      : null;
  const [stage, setStage] = useState<Stage>("native");
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
  const showCommon = stage !== "native";
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
        <button type="button" disabled={stage !== "common"} aria-describedby={statusId}
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
      {stage === "combined" && plan.sum_numerator <= plan.sum_denominator && (
        <ProblemVisual spec={{
          type: "fraction_bar", numerator: plan.sum_numerator, denominator: plan.sum_denominator,
          aria_label: `Sum: ${plan.sum_numerator} of ${plan.sum_denominator} equal parts shaded`,
        }} />
      )}
      <p id={statusId} role="status" aria-live="polite" aria-atomic="true">
        {stage === "combined"
          ? describeFractionAddition(plan)
          : stage === "common"
            ? `Both bars now show ${plan.common_denominator} equal parts. Combine them to see the sum.`
            : "Make equal parts first, then combine the shaded parts to see the sum."}
      </p>
    </section>
  );
}
