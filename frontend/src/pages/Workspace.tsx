import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import ProblemVisual from "../components/ProblemVisual";
import type {
  Award,
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

const BURST_COLORS = ["#6d28d9", "#0ea5e9", "#f59e0b", "#15803d", "#ec4899"];

function BadgeIcon({ small = false }: { small?: boolean }) {
  const size = small ? 34 : 44;
  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className="badge-icon"
      aria-hidden="true"
    >
      <circle cx="32" cy="26" r="20" fill="#f59e0b" />
      <circle cx="32" cy="26" r="15" fill="#fff8e6" />
      <path
        d="M32 16l3 6.5 7 .8-5.2 4.7 1.4 7-6.2-3.6-6.2 3.6 1.4-7-5.2-4.7 7-.8z"
        fill="#d97706"
      />
      <path d="M24 44l-4 14 12-6 12 6-4-14" fill="#6d28d9" />
    </svg>
  );
}

function ConfettiBurst({
  trigger,
  always = false,
}: {
  trigger: number;
  always?: boolean;
}) {
  if (!always && trigger === 0) return null;
  return (
    <div className="burst" aria-hidden="true" key={trigger}>
      {Array.from({ length: 14 }, (_, i) => (
        <span
          key={i}
          className="burst-piece"
          style={
            {
              "--i": i,
              "--hue": BURST_COLORS[i % BURST_COLORS.length],
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  );
}

export default function Workspace() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [workspace, setWorkspace] = useState<LearnerWorkspace | null>(null);
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("");
  const [statusOk, setStatusOk] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<"" | "correct" | "wrong">("");
  const [streak, setStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  const [celebrate, setCelebrate] = useState(0);
  const [badgeToast, setBadgeToast] = useState<Award[]>([]);

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

  useEffect(() => {
    if (!badgeToast.length) return;
    const timer = setTimeout(() => setBadgeToast([]), 5000);
    return () => clearTimeout(timer);
  }, [badgeToast]);

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
      if (correct) {
        setStreak((s) => {
          const next = s + 1;
          setBestStreak((b) => Math.max(b, next));
          return next;
        });
        setCelebrate((c) => c + 1);
      } else {
        setStreak(0);
      }
      if (result.new_awards?.length) {
        setBadgeToast(result.new_awards);
      }
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
          <div className="hero-row">
            <div>
              <h1>
                {workspace.learner.first_name} · Grade{" "}
                {workspace.learner.grade_level}
              </h1>
              <p>
                {[workspace.curriculum.jurisdiction, workspace.curriculum.name]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </div>
            <div className="hero-stats">
              <Link
                className="chip map-link"
                to={`/learn/${sessionId}/map`}
              >
                Skill map
              </Link>
              {streak >= 2 && (
                <span className="chip streak" role="status">
                  Streak ×{streak}
                </span>
              )}
              {bestStreak >= 3 && (
                <span className="chip best">Best ×{bestStreak}</span>
              )}
              <span className="chip score">Score {masteryPct}</span>
            </div>
          </div>
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

        {badgeToast.length > 0 && (
          <div className="badge-toast" role="status">
            {badgeToast.map((award) => (
              <div key={award.code + (award.skill_name ?? "")} className="badge-toast-card">
                <BadgeIcon />
                <div>
                  <strong>Badge earned — {award.name}</strong>
                  <p>{award.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}

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
                <ConfettiBurst trigger={celebrate} always />
                <div className="medallion" aria-hidden="true">
                  <svg viewBox="0 0 64 64" width="72" height="72">
                    <defs>
                      <linearGradient id="badgeGrad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#f59e0b" />
                        <stop offset="100%" stopColor="#d97706" />
                      </linearGradient>
                    </defs>
                    <circle cx="32" cy="26" r="20" fill="url(#badgeGrad)" />
                    <circle cx="32" cy="26" r="15" fill="#fff8e6" />
                    <path
                      d="M32 16l3 6.5 7 .8-5.2 4.7 1.4 7-6.2-3.6-6.2 3.6 1.4-7-5.2-4.7 7-.8z"
                      fill="#d97706"
                    />
                    <path d="M24 44l-4 14 12-6 12 6-4-14" fill="#6d28d9" />
                  </svg>
                </div>
                <h2>Skill complete</h2>
                <p className="badge-name">Badge earned: {workspace.focus.skill_name}</p>
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
                <div className="problem-wrap">
                  <div className={`problem ${feedback}`} aria-live="polite">
                    {workspace.problem?.prompt ??
                      "No problem is currently assigned."}
                    <ProblemVisual spec={workspace.problem?.visual ?? null} />
                  </div>
                  {feedback === "correct" && (
                    <ConfettiBurst trigger={celebrate} />
                  )}
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

            {workspace.awards.length > 0 && (
              <section className="card">
                <div className="card-title-row">
                  <h2>Badges</h2>
                  <Link
                    className="muted small"
                    to={`/learn/${sessionId}/badges`}
                  >
                    View all
                  </Link>
                </div>
                <ul className="badge-shelf">
                  {workspace.awards.map((award) => (
                    <li
                      key={award.code + (award.skill_name ?? "")}
                      className="badge-item"
                    >
                      <BadgeIcon small />
                      <div>
                        <strong>{award.name}</strong>
                        <span className="muted small">
                          {award.skill_name
                            ? `${award.description} · ${award.skill_name}`
                            : award.description}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </aside>
        </div>
      </main>
    </>
  );
}
