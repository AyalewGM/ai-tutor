import { useId, useState } from "react";
import ProblemVisual from "../components/ProblemVisual";
import type { MathInteractionEvent } from "./interactions";
import { formatRational } from "./linearExplorer";
import {
  checkProbabilityTreeAnswer,
  isEquivalentProbabilityAnswer,
  MAX_PROBABILITY_TOTAL,
  MIN_PROBABILITY_TOTAL,
  probabilityTreeModel,
  PROBABILITY_TREE_PRACTICE,
  updateProbabilityStage,
  type ProbabilityTreeState,
} from "./probabilityTree";

export interface InteractiveProbabilityTreeProps {
  independentAssessment: boolean;
  onMathEvent?: (event: MathInteractionEvent) => void;
}

const INITIAL_TREE: ProbabilityTreeState = {
  first: { label: "red", favorable: 3, total: 8 },
  second: { label: "heads", favorable: 1, total: 2 },
};

export function InteractiveProbabilityTree(props: InteractiveProbabilityTreeProps) {
  if (props.independentAssessment !== false) return null;
  return <GuidedProbabilityTree {...props} />;
}

function GuidedProbabilityTree({ onMathEvent }: InteractiveProbabilityTreeProps) {
  const id = useId();
  const [state, setState] = useState(INITIAL_TREE);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const [prediction, setPrediction] = useState("");
  const [predictionCommitted, setPredictionCommitted] = useState(false);
  const [reasoning, setReasoning] = useState("");
  const [reasoningFeedback, setReasoningFeedback] = useState("");
  const [scaffoldFaded, setScaffoldFaded] = useState(false);
  const [predictionEvidence, setPredictionEvidence] = useState("");
  const [repair, setRepair] = useState<"" | "add" | "atLeast" | "complement">("");
  const [repairAnswer, setRepairAnswer] = useState("");
  const [repairReason, setRepairReason] = useState("");
  const [repairFeedback, setRepairFeedback] = useState("");
  const [transferChoice, setTransferChoice] = useState<"" | "independent" | "dependent">("");
  const [transferReason, setTransferReason] = useState("");
  const [transferFeedback, setTransferFeedback] = useState("");
  const model = probabilityTreeModel(state);
  const item = PROBABILITY_TREE_PRACTICE[index];
  const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50";

  function change(stage: "first" | "second", field: "favorable" | "total", value: number) {
    const next = updateProbabilityStage(state, stage, field, value);
    if (predictionCommitted && stage === "first" && field === "favorable" && value > state.first.favorable) {
      const before = probabilityTreeModel(state).bothProbability;
      const after = probabilityTreeModel(next).bothProbability;
      const relation = before.numerator * after.denominator < after.numerator * before.denominator ? "increase" :
        before.numerator * after.denominator > after.numerator * before.denominator ? "decrease" : "same";
      setPredictionEvidence(
        `Observed both-favorable probability ${relation}d from ${formatRational(before)} to ${formatRational(after)}. Your prediction ${prediction === relation ? "matched" : "did not match"} the observation.`
      );
    }
    setState(next);
    onMathEvent?.({
      schema_version: 1,
      type: "PROBABILITY_TREE_CHANGED",
      first_favorable: next.first.favorable,
      first_total: next.first.total,
      second_favorable: next.second.favorable,
      second_total: next.second.total,
    });
  }

  return <section aria-label="Guided probability tree exploration" className="space-y-4 rounded-lg border p-4">
    <h3 className="font-semibold">Observe: an independent compound event has two stages</h3>
    <p>This separate synthetic model does not count toward mastery. Each path through the tree is one ordered outcome type.</p>
    <p>
      This tree assumes the second stage is independent of the first stage, so the second-stage probabilities stay the same on every first-stage branch.
      If the first result changes the second-stage chances, use conditional branch probabilities instead of multiplying the same marginal probability on both branches.
    </p>
    <h3 className="font-semibold">Predict</h3>
    <label className="block" htmlFor={`${id}-prediction`}>
      Before revealing the tree values: if the first-event favorable chance increases while the second stage stays fixed, what happens to the probability that both favorable events occur?
    </label>
    <select id={`${id}-prediction`} className={control} value={prediction}
      disabled={predictionCommitted} onChange={e => setPrediction(e.target.value)}>
      <option value="">Choose a prediction</option>
      <option value="increase">It increases</option>
      <option value="same">It stays the same</option>
      <option value="decrease">It decreases</option>
    </select>
    <button type="button" className={control} disabled={!prediction || predictionCommitted}
      onClick={() => setPredictionCommitted(true)}>Lock prediction</button>
    {predictionCommitted && <p role="status" aria-live="polite">
      Prediction recorded. Now increase the first-event favorable outcomes and compare what changes.
    </p>}
    {predictionEvidence && <p role="status" aria-live="polite" aria-atomic="true">{predictionEvidence}</p>}
    {predictionCommitted && <ProblemVisual spec={{
      type: "probability_tree",
      first_label: state.first.label,
      first_favorable: state.first.favorable,
      first_total: state.first.total,
      second_label: state.second.label,
      second_favorable: state.second.favorable,
      second_total: state.second.total,
      aria_label: `Independent probability tree for ${state.first.favorable} of ${state.first.total} ${state.first.label} outcomes followed by ${state.second.favorable} of ${state.second.total} ${state.second.label} outcomes.`,
    }} />}
    <h3 className="font-semibold">Manipulate</h3>
    <fieldset disabled={!predictionCommitted} className="grid gap-3 md:grid-cols-2">
      <div>
        <label className="block" htmlFor={`${id}-first-total`}>First event total outcomes: {state.first.total}</label>
        <input id={`${id}-first-total`} className={`w-full ${control}`} type="range" min={MIN_PROBABILITY_TOTAL} max={MAX_PROBABILITY_TOTAL} step={1}
          value={state.first.total} onChange={e => change("first", "total", Number(e.target.value))} />
        <label className="block" htmlFor={`${id}-first-fav`}>First event favorable outcomes: {state.first.favorable}</label>
        <input id={`${id}-first-fav`} className={`w-full ${control}`} type="range"
          min={predictionCommitted && !predictionEvidence ? state.first.favorable : 1}
          max={state.first.total - 1} step={1}
          value={state.first.favorable} onChange={e => change("first", "favorable", Number(e.target.value))} />
      </div>
      <div>
        <label className="block" htmlFor={`${id}-second-total`}>Second event total outcomes: {state.second.total}</label>
        <input id={`${id}-second-total`} className={`w-full ${control}`} type="range" min={MIN_PROBABILITY_TOTAL} max={MAX_PROBABILITY_TOTAL} step={1}
          value={state.second.total} onChange={e => change("second", "total", Number(e.target.value))} />
        <label className="block" htmlFor={`${id}-second-fav`}>Second event favorable outcomes: {state.second.favorable}</label>
        <input id={`${id}-second-fav`} className={`w-full ${control}`} type="range" min={1} max={state.second.total - 1} step={1}
          value={state.second.favorable} onChange={e => change("second", "favorable", Number(e.target.value))} />
      </div>
    </fieldset>
    <p>Use arrow keys on any slider. Increasing a total adds possible outcomes; increasing favorable outcomes thickens the favorable branch. The same second-stage branch values appear under both first-stage outcomes because this model is independent.</p>
    <h3 className="font-semibold">Explain</h3>
    {!scaffoldFaded && <p role="status" aria-live="polite" aria-atomic="true">
      Both favorable: {formatRational(model.bothProbability)}. At least one favorable: {formatRational(model.atLeastOneProbability)}. Neither: {formatRational(model.neitherProbability)}. Sample space: {model.sampleSpaceSize} ordered outcomes.
    </p>}
    {!scaffoldFaded && <table className="w-full text-left">
      <caption>Path probabilities for independent stages: multiply along each branch</caption>
      <thead><tr><th scope="col">Path</th><th scope="col">Probability</th></tr></thead>
      <tbody>{model.outcomes.map(outcome => <tr key={outcome.label}><th scope="row">{outcome.label}</th><td>{formatRational(outcome.probability)}</td></tr>)}</tbody>
    </table>}
    {!scaffoldFaded && <p>The probability of both favorable events is one independent path. The probability of at least one favorable event is the sum of three paths, or one minus the neither path.</p>}
    <label className="block" htmlFor={`${id}-reasoning`}>Which explanation justifies the probability of both favorable events?</label>
    <select id={`${id}-reasoning`} className={control} value={reasoning}
      onChange={e => { setReasoning(e.target.value); setReasoningFeedback(""); }}>
      <option value="">Choose your explanation</option>
      <option value="multiply">Multiply the two independent branch probabilities along one path.</option>
      <option value="add">Add the two stage probabilities because there are two stages.</option>
      <option value="complement">Multiply the two complement branches.</option>
    </select>
    <button type="button" className={control} disabled={!reasoning}
      onClick={() => {
        if (reasoning === "multiply") {
          setReasoningFeedback("Reasoning verified. One ordered path uses one branch from each independent stage, so the branch probabilities multiply.");
          setScaffoldFaded(true);
        } else if (reasoning === "add") {
          setReasoningFeedback("Not yet. Adding stage probabilities mixes separate stages. Complete a different path repair before continuing.");
          setRepair("add"); setScaffoldFaded(false);
        } else {
          setReasoningFeedback("Not yet. Complement branches describe the neither path, not the both-favorable path. Complete a complement repair.");
          setRepair("complement"); setScaffoldFaded(false);
        }
      }}>Check explanation</button>
    <p role="status" aria-live="polite" aria-atomic="true">{reasoningFeedback}</p>
    {scaffoldFaded && <p className="text-sm">Scaffold faded: use the next practice without relying on the path table first.</p>}
    <h3 className="font-semibold">Practice</h3>
    <p>Separate practice {index + 1} of {PROBABILITY_TREE_PRACTICE.length}: find {item.measure.replaceAll("_", " ")} for {item.state.first.favorable}/{item.state.first.total} and {item.state.second.favorable}/{item.state.second.total}.</p>
    <label className="block" htmlFor={`${id}-answer`}>Probability practice answer</label>
    <input id={`${id}-answer`} className={control} value={answer} maxLength={10} aria-describedby={`${id}-feedback`}
      onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
    <div className="flex gap-2">
      <button type="button" className={control} onClick={() => {
        const result = checkProbabilityTreeAnswer(index, answer);
        setFeedback(result.feedback);
        if (!result.correct) {
          setScaffoldFaded(false);
          if (result.misconception === "ADD_BRANCH_PROBABILITIES") setRepair("add");
          if (result.misconception === "AT_LEAST_ONE_AS_BOTH") setRepair("atLeast");
          if (result.misconception === "BRANCH_COMPLEMENT_CONFUSION") setRepair("complement");
        }
      }}>Check probability</button>
      <button type="button" className={control} onClick={() => {
        setIndex((index + 1) % PROBABILITY_TREE_PRACTICE.length);
        setAnswer(""); setFeedback(""); setReasoning(""); setReasoningFeedback("");
        setPrediction(""); setPredictionCommitted(false);
      }}>Next probability practice</button>
    </div>
    <p id={`${id}-feedback`} role="status" aria-live="polite">{feedback}</p>

    {repair && <section aria-label="Misconception repair" className="space-y-2 rounded border p-3">
      <h3 className="font-semibold">Repair and verify</h3>
      <p>{repair === "add" ? "A fair coin is followed by a fair 4-section spinner with one target section. Find P(head and target)." :
        repair === "atLeast" ? "For independent events with P(A)=1/2 and P(B)=1/4, find P(at least one)." :
        "If P(A)=2/3 and P(B)=1/5, find P(A and not B)."}</p>
      <label className="block" htmlFor={`${id}-repair-answer`}>Repair probability</label>
      <input id={`${id}-repair-answer`} className={control} value={repairAnswer}
        onChange={e => { setRepairAnswer(e.target.value); setRepairFeedback(""); }} />
      <label className="block" htmlFor={`${id}-repair-reason`}>Reasoning choice</label>
      <select id={`${id}-repair-reason`} className={control} value={repairReason}
        onChange={e => { setRepairReason(e.target.value); setRepairFeedback(""); }}>
        <option value="">Choose reasoning</option>
        <option value="multiply">One complete path: multiply branch probabilities.</option>
        <option value="complement">Use one minus the probability of neither.</option>
        <option value="notb">Use the complement of B, then multiply along the path.</option>
      </select>
      <button type="button" className={control} onClick={() => {
        const expected = repair === "add" ? [1, 8] : repair === "atLeast" ? [5, 8] : [8, 15];
        const expectedReason = repair === "add" ? "multiply" : repair === "atLeast" ? "complement" : "notb";
        if (isEquivalentProbabilityAnswer(repairAnswer, expected[0], expected[1]) && repairReason === expectedReason) {
          setRepairFeedback("Repair verified with a different problem. Return to transfer.");
          setRepair(""); setRepairAnswer(""); setRepairReason(""); setScaffoldFaded(true);
        } else {
          setRepairFeedback("Not yet. Rebuild the event structure before calculating; the worked answer stays hidden.");
        }
      }}>Check repair</button>
      <p role="status" aria-live="polite" aria-atomic="true">{repairFeedback}</p>
    </section>}

    {scaffoldFaded && !repair && <section aria-label="Probability model transfer" className="space-y-2 rounded border p-3">
      <h3 className="font-semibold">Transfer</h3>
      <p>A bag has 3 red and 2 blue counters. One counter is drawn and kept out, then a second counter is drawn. Can the same second-stage probabilities be reused after every first draw?</p>
      <label className="block" htmlFor={`${id}-transfer-choice`}>Classify the situation</label>
      <select id={`${id}-transfer-choice`} className={control} value={transferChoice}
        onChange={e => { setTransferChoice(e.target.value as "" | "independent" | "dependent"); setTransferFeedback(""); }}>
        <option value="">Choose classification</option>
        <option value="independent">Independent</option>
        <option value="dependent">Dependent</option>
      </select>
      <label className="block" htmlFor={`${id}-transfer-reason`}>Why?</label>
      <select id={`${id}-transfer-reason`} className={control} value={transferReason}
        onChange={e => { setTransferReason(e.target.value); setTransferFeedback(""); }}>
        <option value="">Choose a reason</option>
        <option value="same">The second-stage probabilities stay the same.</option>
        <option value="changes">Removing the first counter changes the remaining total and possibly the favorable count.</option>
      </select>
      <button type="button" className={control} onClick={() => {
        setTransferFeedback(transferChoice === "dependent" && transferReason === "changes" ?
          "Transfer verified. The fixed-marginal independent tree is not the right model for this dependent situation." :
          "Not yet. Ask whether the first result changes the probabilities available at stage two.");
      }}>Check transfer</button>
      <p role="status" aria-live="polite" aria-atomic="true">{transferFeedback}</p>
    </section>}
  </section>;
}
