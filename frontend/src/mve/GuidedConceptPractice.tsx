import { useState, type FormEvent } from "react";
import ProblemVisual from "../components/ProblemVisual";
import {
  classifyEquivalentAnswer,
  classifyRatioAnswer,
  equivalenceModel,
  ratioPartitionModel,
} from "./guidedConceptMath.mjs";

export interface GuidedConceptPracticeProps {
  /** Guided/remediation only. Missing or malformed mode fails closed. */
  independentAssessment: boolean;
  concept: "fraction-equivalence" | "ratio-partition";
}

const equivalent = equivalenceModel(2, 3, 3);
const ratio = ratioPartitionModel(2, 3, 4);
const control = "rounded border p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2";

function FractionLesson() {
  const [prediction, setPrediction] = useState("");
  const [predictionLocked, setPredictionLocked] = useState(false);
  const [predictionFeedback, setPredictionFeedback] = useState("");
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const [numericVerified, setNumericVerified] = useState(false);
  const [explainScale, setExplainScale] = useState("");
  const [explainNumerator, setExplainNumerator] = useState("");
  const [explainSameWhole, setExplainSameWhole] = useState("");
  const [explanationVerified, setExplanationVerified] = useState(false);
  const [repair, setRepair] = useState<"" | "denominator" | "additive" | "sameNumerator">("");
  const [repairAnswer, setRepairAnswer] = useState("");
  const [repairReason, setRepairReason] = useState("");
  const [repairFeedback, setRepairFeedback] = useState("");
  const [transferNumerator, setTransferNumerator] = useState("");
  const [transferScale, setTransferScale] = useState("");
  const [transferReason, setTransferReason] = useState("");
  const [transferFeedback, setTransferFeedback] = useState("");

  const check = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = classifyEquivalentAnswer(equivalent, answer);
    if (result.correct) {
      setNumericVerified(true);
      setFeedback("Numeric practice is correct. Now compare the completed representation and verify the scaling explanation.");
      return;
    }
    if (result.misconception === "NUMERATOR_NOT_SCALED") setRepair("denominator");
    else if (result.misconception === "ADDITIVE_SCALING") setRepair("additive");
    else if (answer.trim() === "2") setRepair("sameNumerator");
    setExplanationVerified(false);
    setNumericVerified(false);
    setFeedback(result.misconception === "INVALID_INPUT" ? "Enter a whole-number numerator." :
      "Not yet. Complete the targeted repair without revealing the worked answer.");
  };

  return <section aria-label="Guided fraction equivalence lesson" data-mve-family="fraction-equivalence"
    className="space-y-3 rounded-lg border p-4">
    <h3 className="font-semibold">Observe and predict: equivalent fractions</h3>
    <p className="text-sm">Guided practice only. No mastery is awarded here.</p>
    <ProblemVisual spec={{ type: "fraction_bar", numerator: equivalent.numerator,
      denominator: equivalent.denominator, aria_label: "Two of three equal parts shaded" }} />
    <label className="block" htmlFor="fraction-prediction">Before seeing the completed ninths bar, how should 2/3 compare with the matching fraction out of 9?</label>
    <select id="fraction-prediction" className={control} value={prediction} disabled={predictionLocked}
      onChange={e => setPrediction(e.target.value)}>
      <option value="">Choose a prediction</option>
      <option value="same">Same value</option>
      <option value="larger">The ninths fraction is larger</option>
      <option value="smaller">The ninths fraction is smaller</option>
    </select>
    <button type="button" className={control} disabled={!prediction || predictionLocked}
      onClick={() => {
        setPredictionLocked(true);
        setPredictionFeedback(prediction === "same" ?
          "Your prediction matches the mathematical relationship: repartitioning the same whole does not change the fraction's value." :
          "Compare your prediction with the revealed bars: the same whole is repartitioned, so an equivalent fraction should name the same value.");
      }}>Lock prediction</button>
    {predictionLocked && <p role="status" aria-live="polite" aria-atomic="true">{predictionFeedback}</p>}

    {predictionLocked && <>
      {numericVerified && !explanationVerified && <ProblemVisual spec={{ type: "fraction_bar",
        numerator: equivalent.expandedNumerator, denominator: equivalent.expandedDenominator,
        aria_label: "Six of nine equal parts shaded, same length as two thirds" }} />}
      <form onSubmit={check} className="space-y-2">
        <label className="block" htmlFor="equivalent-numerator">Complete 2/3 = ?/9. Missing numerator:</label>
        <input id="equivalent-numerator" className={control} inputMode="numeric" value={answer}
          onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
        <button type="submit" className={control}>Check numeric practice</button>
      </form>
      <p role="status" aria-live="polite">{feedback}</p>

      <h3 className="font-semibold">Explain</h3>
      <label className="block" htmlFor="fraction-scale">Scale factor from 3 to 9</label>
      <input id="fraction-scale" className={control} value={explainScale} onChange={e => setExplainScale(e.target.value)} />
      <label className="block" htmlFor="fraction-new-numerator">Numerator after applying the same factor</label>
      <input id="fraction-new-numerator" className={control} value={explainNumerator} onChange={e => setExplainNumerator(e.target.value)} />
      <label className="block" htmlFor="fraction-same-whole">Why are the fractions equal?</label>
      <select id="fraction-same-whole" className={control} value={explainSameWhole} onChange={e => setExplainSameWhole(e.target.value)}>
        <option value="">Choose reasoning</option>
        <option value="same-factor">The same whole is repartitioned, and numerator and denominator use the same multiplicative factor.</option>
        <option value="same-numerator">Equal numerators always mean equal fractions.</option>
        <option value="add">Add the same number to numerator and denominator.</option>
      </select>
      <button type="button" className={control} onClick={() => {
        const ok = explainScale.trim() === "3" && explainNumerator.trim() === "6" && explainSameWhole === "same-factor";
        setExplanationVerified(ok);
        setFeedback(ok ? "Explanation verified. The completed visual now fades for transfer." :
          "Not yet. Reconstruct the same multiplicative scale on numerator and denominator.");
      }}>Check explanation</button>
    </>}

    {repair && <section aria-label="Fraction misconception repair" className="space-y-2 rounded border p-3">
      <h3 className="font-semibold">Repair and verify</h3>
      <p>{repair === "denominator" ? "Repair: 3/4 = ?/8." :
        repair === "additive" ? "Repair: 1/2 = ?/6." :
        "Repair: compare 2/5 and 2/10."}</p>
      <input aria-label="Fraction repair answer" className={control} value={repairAnswer}
        onChange={e => { setRepairAnswer(e.target.value); setRepairFeedback(""); }} />
      <select aria-label="Fraction repair reasoning" className={control} value={repairReason}
        onChange={e => { setRepairReason(e.target.value); setRepairFeedback(""); }}>
        <option value="">Choose reasoning</option>
        <option value="same-factor">Multiply numerator and denominator by the same factor.</option>
        <option value="fifths-larger">With the same numerator, fifths are larger pieces than tenths, so 2/5 &gt; 2/10.</option>
      </select>
      <button type="button" className={control} onClick={() => {
        const ok = repair === "denominator" ? repairAnswer.trim() === "6" && repairReason === "same-factor" :
          repair === "additive" ? repairAnswer.trim() === "3" && repairReason === "same-factor" :
          repairAnswer.trim().replaceAll(" ", "") === "2/5>2/10" && repairReason === "fifths-larger";
        if (ok) {
          setRepairFeedback("Repair verified with a different item.");
          setRepair(""); setRepairAnswer(""); setRepairUnit(""); setRepairReason("");
        } else setRepairFeedback("Not yet. Use the relationship between equal parts rather than copying the original answer.");
      }}>Check repair</button>
      <p role="status" aria-live="polite">{repairFeedback}</p>
    </section>}

    {explanationVerified && !repair && <section aria-label="Fraction transfer" className="space-y-2 rounded border p-3">
      <h3 className="font-semibold">Transfer without the completed bar</h3>
      <p>A strip has 12 equal cells. Write the fraction equivalent to 3/4.</p>
      <input aria-label="Transfer numerator out of twelve" className={control} value={transferNumerator}
        onChange={e => { setTransferNumerator(e.target.value); setTransferFeedback(""); }} />
      <input aria-label="Transfer scale factor" className={control} value={transferScale}
        onChange={e => { setTransferScale(e.target.value); setTransferFeedback(""); }} />
      <select aria-label="Transfer reasoning" className={control} value={transferReason}
        onChange={e => { setTransferReason(e.target.value); setTransferFeedback(""); }}>
        <option value="">Choose reasoning</option>
        <option value="same-factor">Same whole; multiply numerator and denominator by the same factor.</option>
        <option value="add">Add the same amount to both.</option>
      </select>
      <button type="button" className={control} onClick={() => setTransferFeedback(
        transferNumerator.trim() === "9" && transferScale.trim() === "3" && transferReason === "same-factor" ?
          "Transfer verified: 3/4 = 9/12." :
          "Not yet. The transfer stays unworked; reconstruct the multiplicative scale."
      )}>Check transfer</button>
      <p role="status" aria-live="polite">{transferFeedback}</p>
    </section>}
  </section>;
}

function RatioLesson() {
  const [prediction, setPrediction] = useState("");
  const [predictionLocked, setPredictionLocked] = useState(false);
  const [predictionFeedback, setPredictionFeedback] = useState("");
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const [parts, setParts] = useState("");
  const [unit, setUnit] = useState("");
  const [firstShare, setFirstShare] = useState("");
  const [recompose, setRecompose] = useState("");
  const [explanationVerified, setExplanationVerified] = useState(false);
  const [repair, setRepair] = useState<"" | "whole" | "part" | "unequal">("");
  const [repairAnswer, setRepairAnswer] = useState("");
  const [repairUnit, setRepairUnit] = useState("");
  const [repairFeedback, setRepairFeedback] = useState("");
  const [transfer, setTransfer] = useState({ parts: "", unit: "", first: "", second: "" });
  const [transferFeedback, setTransferFeedback] = useState("");

  const check = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = classifyRatioAnswer(ratio, answer);
    if (result.correct) {
      setFeedback("Numeric practice is correct. Now reconstruct the ratio parts.");
      return;
    }
    if (result.misconception === "WHOLE_INSTEAD_OF_SHARE") setRepair("whole");
    else if (result.misconception === "WRONG_PART_COUNT") setRepair("part");
    else setRepair("unequal");
    setExplanationVerified(false);
    setFeedback(result.misconception === "INVALID_INPUT" ? "Enter a whole-number share." :
      "Not yet. Complete the targeted ratio repair.");
  };

  return <section aria-label="Guided ratio partition lesson" data-mve-family="ratio-partition"
    className="space-y-3 rounded-lg border p-4">
    <h3 className="font-semibold">Observe and predict: sharing in a ratio</h3>
    <p className="text-sm">Guided practice only. No mastery is awarded here.</p>
    <p>Share 20 counters in the ratio 2:3. Before grouping them, is the first share less than, equal to, or greater than half?</p>
    <select aria-label="Ratio prediction" className={control} value={prediction} disabled={predictionLocked}
      onChange={e => setPrediction(e.target.value)}>
      <option value="">Choose a prediction</option>
      <option value="less">Less than half</option>
      <option value="equal">Equal to half</option>
      <option value="greater">Greater than half</option>
    </select>
    <button type="button" className={control} disabled={!prediction || predictionLocked}
      onClick={() => {
        setPredictionLocked(true);
        setPredictionFeedback(prediction === "less" ?
          "Your prediction matches the ratio structure: 2 of 5 equal parts is less than one half of the whole." :
          "Compare your prediction with the part structure: the first share is 2 of 5 equal parts, so it is less than half.");
      }}>Lock prediction</button>
    {predictionLocked && <p role="status" aria-live="polite" aria-atomic="true">{predictionFeedback}</p>}

    {predictionLocked && <>
      {!explanationVerified && <div aria-label="Five equal ratio parts" className="flex flex-wrap gap-2">
        {Array.from({ length: ratio.totalParts }, (_, index) => (
          <div key={index} className="rounded border p-2 text-center">
            <span className="block text-xs">{index < ratio.firstParts ? "Group A" : "Group B"}</span>
            <span aria-hidden="true">● ● ● ●</span><span className="sr-only">four counters</span>
          </div>
        ))}
      </div>}
      <form onSubmit={check} className="space-y-2">
        <label className="block" htmlFor="ratio-first-share">How many counters should Group A receive?</label>
        <input id="ratio-first-share" className={control} inputMode="numeric" value={answer}
          onChange={e => { setAnswer(e.target.value); setFeedback(""); }} />
        <button type="submit" className={control}>Check numeric practice</button>
      </form>
      <p role="status" aria-live="polite">{feedback}</p>

      <h3 className="font-semibold">Explain</h3>
      <input aria-label="Total ratio parts" className={control} value={parts} onChange={e => setParts(e.target.value)} />
      <input aria-label="Common unit value" className={control} value={unit} onChange={e => setUnit(e.target.value)} />
      <input aria-label="First share from two units" className={control} value={firstShare} onChange={e => setFirstShare(e.target.value)} />
      <input aria-label="Recomposition equation total" className={control} value={recompose} onChange={e => setRecompose(e.target.value)} />
      <button type="button" className={control} onClick={() => {
        const ok = parts.trim() === "5" && unit.trim() === "4" && firstShare.trim() === "8" &&
          recompose.trim().replaceAll(" ", "") === "8+12=20";
        setExplanationVerified(ok);
        setFeedback(ok ? "Ratio explanation verified. The counter scaffold now fades for transfer." :
          "Not yet. Reconstruct total parts, common unit, first share, and recomposition.");
      }}>Check explanation</button>
    </>}

    {repair && <section aria-label="Ratio misconception repair" className="space-y-2 rounded border p-3">
      <h3 className="font-semibold">Repair and verify</h3>
      <p>{repair === "whole" ? "Share 24 in ratio 1:3. Find the common unit value and both shares." :
        repair === "part" ? "Share 30 in ratio 2:3. Find the common unit value and both shares." :
        "Share 28 in ratio 3:4. Find the common unit value and both shares."}</p>
      <input aria-label="Ratio repair common unit" className={control} value={repairUnit}
        onChange={e => { setRepairUnit(e.target.value); setRepairFeedback(""); }} />
      <input aria-label="Ratio repair shares" className={control} value={repairAnswer}
        onChange={e => { setRepairAnswer(e.target.value); setRepairFeedback(""); }} />
      <button type="button" className={control} onClick={() => {
        const expected = repair === "whole" ? "6,18" : repair === "part" ? "12,18" : "12,16";
        const expectedUnit = repair === "unequal" ? "4" : "6";
        if (repairUnit.trim() === expectedUnit && repairAnswer.replaceAll(" ", "") === expected) {
          setRepairFeedback("Repair verified with a different partition.");
          setRepair(""); setRepairAnswer("");
        } else setRepairFeedback("Not yet. Find one common unit value before assigning shares.");
      }}>Check repair</button>
      <p role="status" aria-live="polite">{repairFeedback}</p>
    </section>}

    {explanationVerified && !repair && <section aria-label="Ratio transfer" className="space-y-2 rounded border p-3">
      <h3 className="font-semibold">Transfer without counters</h3>
      <p>A 35-minute session is split warm-up:drills = 2:5. Enter total parts, unit minutes, warm-up, and drills.</p>
      {(["parts","unit","first","second"] as const).map(key => <input key={key} aria-label={`Transfer ${key}`}
        className={control} value={transfer[key]} onChange={e => {
          setTransfer({ ...transfer, [key]: e.target.value }); setTransferFeedback("");
        }} />)}
      <button type="button" className={control} onClick={() => setTransferFeedback(
        transfer.parts.trim() === "7" && transfer.unit.trim() === "5" &&
        transfer.first.trim() === "10" && transfer.second.trim() === "25" ?
          "Transfer verified: 10 + 25 = 35 minutes." :
          "Not yet. Reconstruct seven equal ratio parts before assigning the two shares."
      )}>Check transfer</button>
      <p role="status" aria-live="polite">{transferFeedback}</p>
    </section>}
  </section>;
}

/** Explicit assessment boundary, separate from the trusted scorer. */
export function GuidedConceptPractice(props: GuidedConceptPracticeProps) {
  if (props.independentAssessment !== false) return null;
  return props.concept === "fraction-equivalence" ? <FractionLesson /> : <RatioLesson />;
}
