import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import type {
  HintResponse,
  LearnerWorkspace,
  RespondOut,
  TutorState,
} from "../types";

const STEP_ORDER = [
  "DIAGNOSE",
  "GUIDED_PRACTICE",
  "INDEPENDENT_PRACTICE",
  "MASTERY_CHECK",
  "COMPLETE",
];
const STEP_ALIAS: Partial<Record<TutorState, string>> = {
  REMEDIATION: "GUIDED_PRACTICE",
  REVIEW: "DIAGNOSE",
};
const STEP_LABELS = [
  "Diagnose",
  "Guided",
  "Independent",
  "Mastery check",
  "Complete",
];

function friendly(value: string) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/(^|\s)\S/g, (c: string) => c.toUpperCase());
}

const RING_LENGTH = 226.2;

export default function Workspace() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [workspace, setWorkspace] = useState<LearnerWorkspace | null>(null);
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("");
  const [statusOk, setStatusOk] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<"" | "correct" | "wrong">("");

  const load = useCallback(async () => {
    try {
      setWorkspace(
        await api<LearnerWorkspace>(`/learner-workspace/sessions/${sessionId}`),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load session");
    }
  }, [sessionId]);

  useEffect(() => {
    load();
  }, [load]);

  const hasAction = (action: string) =>
    workspace?.allowed_actions.includes(action) ?? false;

  async function submitAnswer(event: FormEvent) {
    event.preventDefault();
    if (!workspace?.problem) return;
    setError("");
    setStatus("Checking your work…");
    try {
      const result = await post<RespondOut>(
        `/adaptive-tutor/sessions/${sessionId}/respond`,
        {
          problem_id: workspace.problem.id,
          answer,
          assistance_level: 0,
        },
      );
      setAnswer("");
      const correct = result.evaluation.correct;
      setFeedback("");
      requestAnimationFrame(() => setFeedback(correct ? "correct" : "wrong"));
      setStatus(
        correct
          ? "Correct. Keep going."
          : "Not yet. Use the feedback and try the next step.",
      );
      setStatusOk(correct);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Submit failed");
      setStatus("");
    }
  }

  async function requestHelp(reason: "HINT" | "I_DONT_UNDERSTAND") {
    if (!workspace?.problem) return;
    setError("");
    setStatus("");
    try {
      const result = await post<HintResponse>(
        `/adaptive-tutor/sessions/${sessionId}/hint`,
        { problem_id: workspace.problem.id, reason },
      );
      setStatus(
        result.message || "Support is not available in this learning state.",
      );
      setStatusOk(result.allowed);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Hint failed");
    }
  }

  if (!workspace) {
    return (
      <>
        <NavBar />
        <main className="page">
          {error ? (
            <p className="error" role="alert">
              {error}
            </p>
          ) : (
            <p className="muted">Loading your session…</p>
          )}
        </main>
      </>
    );
  }

  const complete = workspace.state === "COMPLETE";
  const effective = STEP_ALIAS[workspace.state] ?? workspace.state;
  const activeIndex = STEP_ORDER.indexOf(effective);
  const masteryPct = Math.round(workspace.evidence.mastery_score * 100);

  return (
    <>
      <NavBar />
      <main className="page">
        <section className="hero">
          <h1>
            {workspace.learner.first_name} · Grade{" "}
            {workspace.learner.grade_level}
          </h1>
          <p>
            {[workspace.curriculum.jurisdiction, workspace.curriculum.name]
              .filter(Boolean)
              .join(" · ")}
          </p>
          <ol className="stepper" aria-label="Learning state">
            {STEP_ORDER.map((step, index) => (
              <li
                key={step}
                className={
                  index === activeIndex
                    ? "step active"
                    : index < activeIndex
                      ? "step done"
                      : "step"
                }
              >
                {STEP_LABELS[index]}
              </li>
            ))}
          </ol>
        </section>

        {workspace.reviews_due.length > 0 && (
          <div className="banner" role="status">
            <strong>Quick refresh:</strong>{" "}
            {workspace.reviews_due.map((r) => r.skill_name).join(", ")}
          </div>
        )}

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <div className="grid two">
          <div className="col">
            {complete ? (
              <section className="card completion" id="completionPanel">
                <div className="completion-badge" aria-hidden="true">
                  ✓
                </div>
                <h2>Skill complete</h2>
                <p>
                  You answered correctly and independently in the mastery check.
                </p>
                {workspace.recommended_next && (
                  <p className="muted">
                    Up next: {workspace.recommended_next.skill_name}
                  </p>
                )}
              </section>
            ) : (
              <section className="card">
                <h2>Current problem</h2>
                <p className="muted small">
                  {workspace.focus.skill_name} · {friendly(workspace.state)}
                </p>
                <div className={`problem ${feedback}`} aria-live="polite">
                  {workspace.problem?.prompt ??
                    "No problem is currently assigned."}
                </div>
                <form onSubmit={submitAnswer}>
                  <label htmlFor="answer">Your answer</label>
                  <input
                    id="answer"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    disabled={
                      !hasAction("SUBMIT_ANSWER") || !workspace.problem
                    }
                    autoComplete="off"
                  />
                  <div className="actions">
                    <button
                      type="submit"
                      className="primary"
                      disabled={
                        !hasAction("SUBMIT_ANSWER") ||
                        !workspace.problem ||
                        !answer.trim()
                      }
                    >
                      Submit answer
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => requestHelp("HINT")}
                      disabled={
                        !hasAction("REQUEST_HINT") || !workspace.problem
                      }
                    >
                      Hint
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => requestHelp("I_DONT_UNDERSTAND")}
                      disabled={
                        !hasAction("I_DONT_UNDERSTAND") || !workspace.problem
                      }
                    >
                      I don&apos;t understand
                    </button>
                  </div>
                </form>
                <p className={statusOk ? "success" : "muted"} aria-live="polite">
                  {status}
                </p>
              </section>
            )}

            <section className="card coach">
              <h2>Coach</h2>
              <div className="bubble" aria-live="polite">
                {complete
                  ? "Nice work. Your independent mastery check is complete."
                  : workspace.coaching_message ??
                    "Work through the problem carefully."}
              </div>
            </section>
          </div>

          <aside className="col">
            <section className="card">
              <h2>Progress</h2>
              <div className="mastery-row">
                <svg viewBox="0 0 80 80" className="ring" aria-hidden="true">
                  <defs>
                    <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#6d28d9" />
                      <stop offset="100%" stopColor="#0ea5e9" />
                    </linearGradient>
                  </defs>
                  <circle cx="40" cy="40" r="36" className="ring-track" />
                  <circle
                    cx="40"
                    cy="40"
                    r="36"
                    className="ring-fill"
                    strokeDasharray={RING_LENGTH}
                    strokeDashoffset={RING_LENGTH * (1 - masteryPct / 100)}
                  />
                </svg>
                <div>
                  <div className="mastery-pct">{masteryPct}%</div>
                  <div className="muted small">mastery</div>
                </div>
              </div>
              <div className="bar">
                <div
                  className="bar-fill"
                  style={{ width: `${masteryPct}%` }}
                />
              </div>
              <div className="metric">
                <strong>Independent correct</strong>
                <div>
                  {workspace.evidence.independent_correct_count} /{" "}
                  {workspace.evidence.independent_attempt_count}
                </div>
              </div>
              <div className="metric">
                <strong>Assisted successes</strong>
                <div>{workspace.evidence.hinted_correct_count}</div>
              </div>
              <p className="muted small">
                Help can support learning, but assisted success is not counted
                as independent mastery evidence.
              </p>
              {workspace.recommended_next && !complete && (
                <p className="muted small">
                  Up next: {workspace.recommended_next.skill_name}
                </p>
              )}
            </section>
          </aside>
        </div>
      </main>
    </>
  );
}
