import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { ApiError, api, post } from "../api";
import { parsePublishedStage, type PublishedStage } from "../publishedLearningFlow";

/**
 * A no-credit lesson overlay anchored to ONE server-issued, incorrectly
 * answered published problem. Does not infer authority from display labels,
 * client flags or taxonomy IDs. Unauthorized GET is invisible.
 */
export default function PublishedLearningRecovery({
  sessionId, problemId, onUnavailable, onClose,
}: {
  sessionId: string;
  problemId: string;
  onUnavailable: () => void;
  onClose: () => void;
}) {
  const labelId = useId();
  const [stage, setStage] = useState<PublishedStage | null>(null);
  const [selection, setSelection] = useState("");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const revision = useRef(0);
  const inFlight = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const unavailable = useRef(onUnavailable);
  unavailable.current = onUnavailable;
  const prefix = "/adaptive-tutor/sessions/" + encodeURIComponent(sessionId);

  useEffect(() => {
    const current = ++revision.current;
    setStage(null);
    setError("");
    setNotice("");
    setSelection("");
    setAnswer("");
    void api<unknown>(prefix + "/published-recovery?problem_id=" +
      encodeURIComponent(problemId)).then((data) => {
      if (current !== revision.current) return;
      const parsed = parsePublishedStage(data);
      if (!parsed || (parsed.problem_id !== undefined && parsed.problem_id !== problemId) ||
          parsed.stage === "INDEPENDENT_EXIT" ||
          (parsed.stage === "MASTERY_VERIFICATION_FEEDBACK_ONLY" && parsed.verification_task)) {
        // Until independently accepted issuance-identity proof exists for
        // recovered independent/mastery tasks, never replay their prompt.
        setStage(null);
        unavailable.current();
        return;
      }
      setStage(parsed);
    }).catch((err: unknown) => {
      if (current !== revision.current) return;
      // A missing, unapproved or revoked publisher stays DEFAULT OFF.
      if (err instanceof ApiError && [403, 404, 409, 422].includes(err.status)) {
        unavailable.current();
      } else {
        setError("This learning support is temporarily unavailable.");
      }
    });
    return () => { revision.current++; };
  }, [prefix, problemId]);

  useEffect(() => {
    if (stage) heading.current?.focus();
  }, [stage?.stage, stage?.guided_retest_task?.variant_id,
      stage?.independent_task?.variant_id, stage?.verification_task?.variant_id]);

  async function advance(path: string, payload?: unknown) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const current = revision.current;
    try {
      const data = await (payload === undefined
        ? api<unknown>(path, { method: "POST" })
        : post<unknown>(path, payload));
      if (current !== revision.current) return;
      const next = parsePublishedStage(data);
      if (!next || next.stage === "CONFIRM_REASONING") {
        setStage(null);
        setError("The server did not authorize the next learning step.");
        return;
      }
      setStage(next);
      setSelection("");
      setAnswer("");
      if (next.correct === false) {
        setNotice("Not yet. Review the prompt and try the allowed next step.");
      } else if (next.correct === true) {
        setNotice("Answer checked. This activity awards no mastery credit.");
      }
    } catch (err) {
      if (current !== revision.current) return;
      // Never continue using a previously issued task after the server denies
      // a stale session, an expired publication or a replay.
      setStage(null);
      setError(err instanceof ApiError && err.status === 409
        ? "This learning step is no longer available. Return to your session."
        : "The learning step could not be verified. Return to your session.");
    } finally {
      if (current === revision.current) {
        inFlight.current = false;
        setBusy(false);
      }
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stage || busy) return;
    const base = prefix + "/published-";
    const source = { problem_id: problemId };
    if (stage.stage === "CONFIRM_REASONING" && selection) {
      void advance(base + "reasoning", { ...source, choice_id: selection });
    } else if ((stage.stage === "SOCRATIC_REPAIR" ||
      stage.stage === "SOCRATIC_REPAIR_RETRY") &&
      (stage.repair_choices?.length ? selection : answer.trim())) {
      void advance(base + "repair", {
        ...source, response: stage.repair_choices?.length ? selection : answer.trim(),
      });
    } else if ((stage.stage === "GUIDED_RETEST" ||
      stage.stage === "GUIDED_RETEST_RETRY") && answer.trim()) {
      void advance(base + "guided-retest", { ...source, answer: answer.trim() });
    } else if (stage.stage === "INDEPENDENT_EXIT" && answer.trim()) {
      void advance(base + "transfer/respond", { ...source, answer: answer.trim() });
    } else if (stage.stage === "MASTERY_VERIFICATION_FEEDBACK_ONLY" &&
      stage.verification_task && answer.trim()) {
      void advance(base + "mastery/respond", { ...source, answer: answer.trim() });
    }
  }

  // No speculative UI while awaiting the server-owned exact problem check.
  if (!stage && !error) return null;
  const guided = stage && [
    "CONFIRM_REASONING", "SOCRATIC_REPAIR", "SOCRATIC_REPAIR_RETRY",
    "GUIDED_RETEST", "GUIDED_RETEST_RETRY",
  ].includes(stage.stage);
  const task = stage?.guided_retest_task ?? stage?.independent_task ??
    stage?.verification_task;
  const choices = stage?.stage === "CONFIRM_REASONING"
    ? stage.choices
    : stage?.repair_choices;
  const choiceStep = Boolean(choices?.length);
  const canSubmit = Boolean(choiceStep ? selection : answer.trim()) &&
    (choiceStep || answer.trim().length <= 64);
  const text = "rounded-md border px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
  const path = prefix + "/published-";

  return (
    <section aria-label="Published learning recovery" className="space-y-3 rounded-xl border p-4">
      <h3 ref={heading} tabIndex={-1} className="text-lg font-semibold">
        {guided ? "Practice and repair your reasoning" :
         stage?.stage === "INDEPENDENT_EXIT" ? "Unhinted transfer practice" :
         stage?.verification_task ? "Separate verification" :
         "Learning feedback"}
      </h3>
      <p className="text-sm text-muted-foreground">
        Feedback only. This recovery journey does not award XP, independent
        mastery evidence, or a mastery badge.
      </p>
      {stage?.stage === "CONFIRM_REASONING" && <p>{stage.prompt}</p>}
      {stage?.stage === "PRACTICE_RETRY" && <p>{stage.neutral_prompt ??
        "Return to the lesson to try a fresh practice problem."}</p>}
      {(stage?.stage === "SOCRATIC_REPAIR" ||
        stage?.stage === "SOCRATIC_REPAIR_RETRY") && (
        <>
          {stage.socratic_repair_questions?.map((question, index) =>
            <p key={index}>{question}</p>)}
          <p>{stage.repair_check}</p>
        </>
      )}
      {task && <div className="space-y-2">
        <p className="font-medium">{task.prompt}</p>
        {task.mode !== "GUIDED" && <p className="text-sm">
          No hints or worked examples are available for this task.
        </p>}
      </div>}
      {stage && (
        <form className="space-y-3" onSubmit={submit}>
          {choiceStep && <fieldset className="space-y-2" disabled={busy}>
            <legend className="font-medium">Choose your reasoning</legend>
            {choices?.map((option) => <label key={option.id}
              className="flex cursor-pointer items-start gap-2 rounded-md border p-2">
              <input type="radio" name={labelId + "-choice"}
                value={option.id} checked={selection === option.id}
                onChange={() => setSelection(option.id)} />
              <span>{option.text}</span>
            </label>)}
          </fieldset>}
          {!choiceStep && (stage.stage === "SOCRATIC_REPAIR" ||
            stage.stage === "SOCRATIC_REPAIR_RETRY" ||
            stage.stage === "GUIDED_RETEST" ||
            stage.stage === "GUIDED_RETEST_RETRY" ||
            stage.stage === "INDEPENDENT_EXIT" ||
            (stage.stage === "MASTERY_VERIFICATION_FEEDBACK_ONLY" &&
              Boolean(stage.verification_task))) && <div className="space-y-2">
            <label htmlFor={labelId + "-answer"} className="block font-medium">
              Your exact answer
            </label>
            <input id={labelId + "-answer"} type="text" value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              maxLength={64} autoComplete="off" disabled={busy}
              aria-describedby={labelId + "-answer-help"} className={text} />
            <p id={labelId + "-answer-help"} className="text-sm text-muted-foreground">
              Enter an exact signed integer or fraction; do not round.
            </p>
          </div>}
          {(choiceStep || stage.stage === "SOCRATIC_REPAIR" ||
            stage.stage === "SOCRATIC_REPAIR_RETRY" ||
            stage.stage === "GUIDED_RETEST" ||
            stage.stage === "GUIDED_RETEST_RETRY" ||
            stage.stage === "INDEPENDENT_EXIT" ||
            Boolean(stage.verification_task)) &&
            <button type="submit" disabled={busy || !canSubmit}
              className={text}>Check response</button>}
        </form>
      )}
      {stage?.stage === "READY_FOR_TRANSFER_CONFIRMATION" &&
        <button type="button" disabled={busy} className={text}
          onClick={() => void advance(path + "transfer/start?problem_id=" +
            encodeURIComponent(problemId))}>
          Start unhinted transfer
        </button>}
      {stage?.stage === "TRANSFER_FEEDBACK_ONLY" && stage.correct === true &&
        <button type="button" disabled={busy} className={text}
          onClick={() => void advance(path + "mastery/start?problem_id=" +
            encodeURIComponent(problemId))}>
          Begin separate feedback-only verification
        </button>}
      {stage?.stage === "GUIDED_RETEST_EXHAUSTED" && <p>
        Guided attempts are complete. Return to your learning session.
      </p>}
      {(stage?.stage === "MASTERY_VERIFICATION_FEEDBACK_ONLY" &&
        !stage.verification_task) && <p>
        Verification recorded. This result does not grant mastery credit.
      </p>}
      {notice && <p role="status" aria-live="polite">{notice}</p>}
      {error && <p role="alert">{error}</p>}
      <button type="button" onClick={onClose} className={text}>
        Return to learning session
      </button>
    </section>
  );
}
