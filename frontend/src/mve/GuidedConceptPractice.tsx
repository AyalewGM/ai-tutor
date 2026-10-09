import { useState, type FormEvent } from "react";
import ProblemVisual from "../components/ProblemVisual";
import {
  classifyEquivalentAnswer,
  classifyRatioAnswer,
  equivalenceModel,
  ratioPartitionModel,
} from "./guidedConceptMath.mjs";

export interface GuidedConceptPracticeProps {
  /** Never expose guided answers or remediation inside an independent assessment. */
  independentAssessment: boolean;
  concept: "fraction-equivalence" | "ratio-partition";
}

const equivalent = equivalenceModel(2, 3, 3);
const ratio = ratioPartitionModel(2, 3, 4);

function FractionLesson() {
  const [stage, setStage] = useState(0);
  const [answer, setAnswer] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [solved, setSolved] = useState(false);
  const check = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = classifyEquivalentAnswer(equivalent, answer);
    if (result.correct) {
      setSolved(true);
      setFeedback("Yes. Each third was split into three smaller parts, so two thirds becomes six ninths.");
      return;
    }
    const next = attempts + 1;
    setAttempts(next);
    setStage(Math.max(stage, Math.min(next, 2)));
    setFeedback(result.misconception === "INVALID_INPUT" ? "Enter a whole-number numerator." :
      result.misconception === "NUMERATOR_NOT_SCALED" ?
        "The parts became smaller. How many new parts cover the same shaded length?" :
      result.misconception === "ADDITIVE_SCALING" ?
        "Equivalent fractions use multiplication, not adding the scale factor." :
        "Compare the shaded lengths of both equal-sized wholes.");
  };
  return (
    <section aria-label="Guided fraction equivalence lesson" data-mve-family="fraction-equivalence"
      className="space-y-3 rounded-lg border p-4">
      <h3 className="font-semibold">Why equivalent fractions cover the same amount</h3>
      <p className="text-sm">Guided exploration only. No mastery is awarded here.</p>
      <p>Imagine two identical chocolate bars. Shade two of three equal pieces.</p>
      <ProblemVisual spec={{ type: "fraction_bar", numerator: equivalent.numerator,
        denominator: equivalent.denominator, aria_label: "Two of three equal parts shaded" }} />
      <p>Now divide every third into three smaller equal pieces. The shaded length stays the same.</p>
      {stage >= 1 && <ProblemVisual spec={{ type: "fraction_bar",
        numerator: equivalent.expandedNumerator,
        denominator: equivalent.expandedDenominator,
        aria_label: "Six of nine equal parts shaded, same length as two thirds" }} />}
      {stage >= 2 && <p className="text-sm">Visual check: each shaded third becomes three shaded ninths. Both bars represent the same whole.</p>}
      <form onSubmit={check} className="space-y-2">
        <label className="block" htmlFor="equivalent-numerator">
          Complete 2/3 = ?/9. What is the missing numerator?
        </label>
        <input id="equivalent-numerator" type="text" inputMode="numeric"
          value={answer} onChange={(event) => setAnswer(event.target.value)}
          disabled={solved} className="rounded border p-2" />
        <button type="submit" disabled={solved} className="rounded border px-3 py-2">
          Check my reasoning
        </button>
      </form>
      <p role="status" aria-live="polite">{feedback}</p>
      {solved && <p>Explain aloud: why must both numerator and denominator be multiplied by three?</p>}
      {!solved && <button type="button" className="rounded border px-3 py-2"
        onClick={() => setStage(Math.min(2, stage + 1))}>Show another representation</button>}
    </section>
  );
}

function RatioLesson() {
  const [stage, setStage] = useState(0);
  const [answer, setAnswer] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [solved, setSolved] = useState(false);
  const check = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = classifyRatioAnswer(ratio, answer);
    if (result.correct) {
      setSolved(true);
      setFeedback("Correct. Two equal ratio parts contain eight counters; the other three contain twelve.");
      return;
    }
    const next = attempts + 1;
    setAttempts(next);
    setStage(Math.max(stage, Math.min(next, 2)));
    setFeedback(result.misconception === "INVALID_INPUT" ? "Enter a whole-number share." :
      result.misconception === "WHOLE_INSTEAD_OF_SHARE" ?
        "Twenty is the whole collection. How many of the five equal parts belong to the first group?" :
      result.misconception === "WRONG_PART_COUNT" ?
        "The whole is divided into two plus three equal parts, not only two." :
        "Find the value of one equal part, then count two of those parts.");
  };
  return (
    <section aria-label="Guided ratio partition lesson" data-mve-family="ratio-partition"
      className="space-y-3 rounded-lg border p-4">
      <h3 className="font-semibold">Sharing a whole in a ratio</h3>
      <p className="text-sm">Guided exploration only. No mastery is awarded here.</p>
      <p>Share 20 counters between two groups in the ratio 2:3.</p>
      <div aria-label="Five equal ratio parts" className="flex flex-wrap gap-2">
        {Array.from({ length: ratio.totalParts }, (_, index) => (
          <div key={index} className="rounded border p-2 text-center">
            <span className="block text-xs">{index < ratio.firstParts ? "Group A" : "Group B"}</span>
            <span aria-hidden="true">● ● ● ●</span>
            <span className="sr-only">four counters</span>
          </div>
        ))}
      </div>
      {stage >= 1 && <p>There are five equal ratio parts altogether. Each part holds four counters.</p>}
      {stage >= 2 && <p>Group A receives two parts; Group B receives three parts. The parts must add back to twenty.</p>}
      <form onSubmit={check} className="space-y-2">
        <label className="block" htmlFor="ratio-first-share">
          How many counters should Group A receive?
        </label>
        <input id="ratio-first-share" type="text" inputMode="numeric"
          value={answer} onChange={(event) => setAnswer(event.target.value)}
          disabled={solved} className="rounded border p-2" />
        <button type="submit" disabled={solved} className="rounded border px-3 py-2">
          Check my reasoning
        </button>
      </form>
      <p role="status" aria-live="polite">{feedback}</p>
      {solved && <p>Explain why dividing twenty by two would not give the value of one ratio part.</p>}
      {!solved && <button type="button" className="rounded border px-3 py-2"
        onClick={() => setStage(Math.min(2, stage + 1))}>Show another representation</button>}
    </section>
  );
}

/** An explicit assessment boundary, separate from the independent problem scorer. */
export function GuidedConceptPractice(props: GuidedConceptPracticeProps) {
  if (props.independentAssessment) return null;
  return props.concept === "fraction-equivalence" ? <FractionLesson /> : <RatioLesson />;
}
