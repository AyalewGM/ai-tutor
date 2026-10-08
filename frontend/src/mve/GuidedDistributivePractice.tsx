import { useCallback, useMemo, useState, type FormEvent } from "react";
import ProblemVisual from "../components/ProblemVisual";
import { PedagogicalAnimation } from "./PedagogicalAnimation";
import { buildDistributiveLesson, checkDistributiveCoefficients } from "./distributiveLesson";
import type { AnimationStep } from "./animation";
import type { MathInteractionEvent } from "./interactions";

interface GuidedDistributivePracticeProps {
  factor?: number;
  constant?: number;
  /** Fail closed: independent assessment must never mount the worked explanation. */
  independentAssessment: boolean;
  /** Optional normalized mathematical events, never raw keystrokes or child data. */
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function GuidedDistributivePractice(props: GuidedDistributivePracticeProps) {
  if (props.independentAssessment) return null;
  return <GuidedDistributiveActivity
    factor={props.factor ?? 3}
    constant={props.constant ?? 4}
    onMathEvent={props.onMathEvent}
  />;
}

function GuidedDistributiveActivity({
  factor, constant, onMathEvent,
}: {
  factor: number;
  constant: number;
  onMathEvent?: (event: MathInteractionEvent) => void;
}) {
  const lesson = useMemo(() => buildDistributiveLesson(factor, constant), [factor, constant]);
  const [stepId, setStepId] = useState("identify");
  const [coefficient, setCoefficient] = useState("");
  const [term, setTerm] = useState("");
  const [feedback, setFeedback] = useState("");

  const onStepChange = useCallback((step: AnimationStep) => {
    setStepId(step.id);
    onMathEvent?.({ schema_version: 1, type: "DISTRIBUTIVE_STEP_VIEWED", step_id: step.id });
  }, [onMathEvent]);

  const stepIndex = lesson.animation.steps.findIndex((step) => step.id === stepId);
  const expression = stepIndex < 1 ? lesson.original
    : stepIndex === 1 ? `${lesson.factor} × ${lesson.variable} + ${lesson.factor} × (${lesson.constant})`
    : stepIndex === 2 ? lesson.expanded : lesson.simplified;

  const check = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validInteger = (text: string) => /^-?\d+$/.test(text.trim()) &&
      Number.isSafeInteger(Number(text.trim())) && Math.abs(Number(text.trim())) <= 10000;
    if (!validInteger(coefficient) || !validInteger(term)) {
      setFeedback("Enter whole numbers in both fields.");
      return;
    }
    const variableCoefficient = Number(coefficient.trim());
    const constantTerm = Number(term.trim());
    const result = checkDistributiveCoefficients(lesson, variableCoefficient, constantTerm);
    onMathEvent?.({
      schema_version: 1,
      type: "DISTRIBUTIVE_COEFFICIENTS_CHECKED",
      variable_coefficient: variableCoefficient,
      constant_term: constantTerm,
      correct: result.correct,
      misconception: result.misconception,
    });
    setFeedback(result.correct ? "Correct: you multiplied both terms." :
      result.misconception === "MISSED_SECOND_TERM" ? "Multiply the outside factor by the constant too." :
      result.misconception === "COEFFICIENT_ERROR" ? "Check the coefficient of the variable against the outside factor." :
      "Check the constant product using the area model.");
  };

  return (
    <section aria-label="Guided distributive property lesson" data-mve-family="distributive"
      className="space-y-3 rounded-lg border p-4">
      <h3 className="font-semibold">Explore the distributive property</h3>
      <p className="text-sm">Worked example, separate from your current question.</p>
      <p aria-label="Current mathematical expression" className="text-lg font-medium">{expression}</p>
      <PedagogicalAnimation spec={lesson.animation} autoPlay={false} onStepChange={onStepChange} />
      {stepIndex >= 1 && <ProblemVisual spec={lesson.areaModel} />}
      <form onSubmit={check} className="space-y-2">
        <fieldset className="space-y-2">
          <legend className="font-medium">Try the expanded expression</legend>
          <label className="block">Coefficient of {lesson.variable}
            <input className="ml-2 rounded border p-2" inputMode="numeric" type="text"
              value={coefficient} onChange={(event) => setCoefficient(event.target.value)} />
          </label>
          <label className="block">Constant term
            <input className="ml-2 rounded border p-2" inputMode="numeric" type="text"
              value={term} onChange={(event) => setTerm(event.target.value)} />
          </label>
        </fieldset>
        <button type="submit" className="rounded bg-primary px-3 py-2 text-primary-foreground">
          Check my work
        </button>
      </form>
      <p role="status" aria-live="polite" aria-atomic="true">{feedback}</p>
    </section>
  );
}
