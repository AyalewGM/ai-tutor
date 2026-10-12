import { useCallback, useId, useState, type FormEvent } from "react";
import ProblemVisual from "../components/ProblemVisual";
import { PedagogicalAnimation } from "./PedagogicalAnimation";
import { buildDistributiveLesson, checkDistributiveCoefficients } from "./distributiveLesson";
import type { AnimationStep } from "./animation";
import type { MathInteractionEvent } from "./interactions";

interface GuidedDistributivePracticeProps {
  factor?: number;
  constant?: number;
  /** Fail closed: only an explicit guided-mode false may mount a worked explanation. */
  independentAssessment?: boolean;
  /** Optional normalized mathematical events, never raw keystrokes or child data. */
  onMathEvent?: (event: MathInteractionEvent) => void;
}

export function GuidedDistributivePractice(props: GuidedDistributivePracticeProps) {
  if (props.independentAssessment !== false) return null;
  let lesson;
  try {
    lesson = buildDistributiveLesson(props.factor ?? -2, props.constant ?? -4);
  } catch {
    return null;
  }
  return <GuidedDistributiveActivity
    key={`${lesson.factor}|${lesson.constant}|${lesson.variable}`}
    lesson={lesson}
    onMathEvent={props.onMathEvent}
  />;
}

function GuidedDistributiveActivity({
  lesson, onMathEvent,
}: {
  lesson: ReturnType<typeof buildDistributiveLesson>;
  onMathEvent?: (event: MathInteractionEvent) => void;
}) {
  const id = useId();
  const [stepId, setStepId] = useState("identify");
  const [prediction, setPrediction] = useState<"positive" | "negative" | "zero" | "">("");
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
  const constantProduct = lesson.factor * lesson.constant;
  const constantProductSign = constantProduct === 0 ? "zero" : constantProduct < 0 ? "negative" : "positive";

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
      result.misconception === "MISSED_SECOND_TERM" ? "The outside factor must multiply the constant term too." :
      result.misconception === "DROPPED_NEGATIVE" ? "Keep the outside negative attached while multiplying each term." :
      result.misconception === "COEFFICIENT_ERROR" ? "Recheck the signed factor applied to the variable term." :
      "Recheck both the sign rule and magnitude of the constant product.");
  };

  return (
    <section aria-label="Guided distributive property lesson" data-mve-family="distributive"
      className="space-y-3 rounded-lg border p-4">
      <h3 className="font-semibold">Explore the distributive property</h3>
      <p className="text-sm">Worked example, separate from your current question.</p>
      <h4 className="font-medium">Observe and predict</h4>
      <p id={`${id}-prediction-prompt`}>
        Before distributing, predict the sign of the constant product in {lesson.original}.
      </p>
      <div role="group" aria-labelledby={`${id}-prediction-prompt`} className="flex flex-wrap gap-2">
        {(["positive", "negative", "zero"] as const).map((sign) => (
          <button key={sign} type="button"
            className="rounded border px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
            aria-pressed={prediction === sign}
            onClick={() => setPrediction(sign)}>{sign[0].toUpperCase() + sign.slice(1)}</button>
        ))}
      </div>
      <p role="status" aria-live="polite" aria-atomic="true">
        {prediction ? prediction === constantProductSign
          ? "Your sign prediction is consistent with the multiplication sign rules."
          : "Recheck the signs and whether either factor is zero."
          : "Choose a sign prediction before stepping through the model."}
      </p>
      <p aria-label="Current mathematical expression" className="text-lg font-medium">{expression}</p>
      <PedagogicalAnimation spec={lesson.animation} autoPlay={false} onStepChange={onStepChange} />
      {stepIndex >= 1 && <ProblemVisual spec={lesson.factor > 0 && lesson.constant >= 0
        ? lesson.areaModel : lesson.algebraTiles} />}
      <form onSubmit={check} className="space-y-2">
        <fieldset className="space-y-2">
          <legend className="font-medium">Try the expanded expression</legend>
          <label className="block" htmlFor={`${id}-coefficient`}>Coefficient of {lesson.variable}</label>
          <input id={`${id}-coefficient`}
            className="rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
            inputMode="numeric" type="text" aria-describedby={`${id}-feedback`}
            value={coefficient} onChange={(event) => { setCoefficient(event.target.value); setFeedback(""); }} />
          <label className="block" htmlFor={`${id}-constant`}>Constant term</label>
          <input id={`${id}-constant`}
            className="rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
            inputMode="numeric" type="text" aria-describedby={`${id}-feedback`}
            value={term} onChange={(event) => { setTerm(event.target.value); setFeedback(""); }} />
        </fieldset>
        <button type="submit"
          className="rounded bg-primary px-3 py-2 text-primary-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2">
          Check my work
        </button>
      </form>
      <p id={`${id}-feedback`} role="status" aria-live="polite" aria-atomic="true">{feedback}</p>
    </section>
  );
}
