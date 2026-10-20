import { InteractivePolynomialDivision } from "../mve/InteractivePolynomialDivision";
import { showPolynomialDivisionExploration } from "../mve/polynomialDivision";
import { InteractiveEquationEquivalence } from "../mve/InteractiveEquationEquivalence";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BookOpen, CheckCircle2, ChevronDown, Flag, Lightbulb, Map as MapIcon, HelpCircle, RefreshCcw, Target, Undo2 } from "lucide-react";
import { ApiError, api, post } from "../api";
import {
  isCurrentSessionOperationResponse,
  isCurrentSessionResponse,
  isCurrentWorkspaceResponse,
} from "../workspaceSessionGuard";
import NavBar from "../components/NavBar";
import Avatar from "../components/Avatar";
import ProblemVisual from "../components/ProblemVisual";
import VoiceChatControls from "../components/chat/VoiceChatControls";
import MathText from "../components/MathText";
import ChatMessage from "../components/chat/ChatMessage";
import LearnPanel from "../components/LearnPanel";
import {
  equationEquivalenceEligible,
  equationEquivalenceExampleIndex,
  integerAdditionEligible,
} from "../learningFlowInteractions";
import { integerSeedFromString } from "../mve/integerPractice";
import { InteractiveFractionBars, fractionComparisonTarget } from "../mve/InteractiveFractionBars";
import { InteractiveFractionAddition } from "../mve/InteractiveFractionAddition";
import LevelCrest from "../components/LevelCrest";
import MathKeypad from "../components/MathKeypad";
import ScratchPad from "../components/ScratchPad";
import SmartScoreBadge from "../components/SmartScoreBadge";
import StepWork from "../components/StepWork";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type {
  Award,
  HintResponse,
  LearnerWorkspace,
  RespondOut,
  SessionSummary,
  TutorState,
  WorkspaceProblem,
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
  const [workspaceSnapshot, setWorkspace] = useState<LearnerWorkspace | null>(null);
  const workspace =
    workspaceSnapshot?.session_id === sessionId ? workspaceSnapshot : null;
  const [answer, setAnswer] = useState("");
  const [fracNum, setFracNum] = useState("");
  const [fracDen, setFracDen] = useState("");
  const [status, setStatus] = useState("");
  const [statusOk, setStatusOk] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<"" | "correct" | "wrong">("");
  const [celebrate, setCelebrate] = useState(0);
  const [badgeToast, setBadgeToast] = useState<Award[]>([]);
  const [levelUp, setLevelUp] = useState<{ level: number; title: string } | null>(null);
  const [masteryWin, setMasteryWin] = useState<Award | null>(null);
  const [learnOpen, setLearnOpen] = useState(false);
  const [goalOpen, setGoalOpen] = useState(false);
  const [extensionProblem, setExtensionProblem] = useState<WorkspaceProblem | null>(null);
  const [extensionSessionId, setExtensionSessionId] = useState<string | null>(null);
  const [recap, setRecap] = useState<SessionSummary | null>(null);
  const [goalWasReached, setGoalWasReached] = useState(false);
  const answerRef = useRef<HTMLInputElement>(null);
  const workspaceRequestRef = useRef(0);
  const extensionRequestRef = useRef(0);
  const answerRequestRef = useRef(0);
  const helpRequestRef = useRef(0);
  const recapRequestRef = useRef(0);
  const goalRequestRef = useRef(0);
  const activeSessionRef = useRef(sessionId);
  activeSessionRef.current = sessionId;

  const load = useCallback(async () => {
    const requestedSessionId = sessionId;
    const requestId = ++workspaceRequestRef.current;
    try {
      const nextWorkspace = await api<LearnerWorkspace>(
        `/learner-workspace/sessions/${requestedSessionId}`,
      );
      if (
        requestId !== workspaceRequestRef.current ||
        !isCurrentWorkspaceResponse(
          requestedSessionId,
          activeSessionRef.current,
          nextWorkspace.session_id,
        )
      ) {
        return;
      }
      setWorkspace(nextWorkspace);
    } catch (err) {
      if (
        requestId !== workspaceRequestRef.current ||
        !isCurrentSessionResponse(requestedSessionId, activeSessionRef.current)
      ) {
        return;
      }
      setError(err instanceof ApiError ? err.message : "Could not load session");
    }
  }, [sessionId]);

  useEffect(() => {
    workspaceRequestRef.current += 1;
    extensionRequestRef.current += 1;
    answerRequestRef.current += 1;
    helpRequestRef.current += 1;
    recapRequestRef.current += 1;
    goalRequestRef.current += 1;
    setWorkspace(null);
    setExtensionProblem(null);
    setExtensionSessionId(null);
    setAnswer("");
    setFracNum("");
    setFracDen("");
    setStatus("");
    setError("");
    setFeedback("");
    setRecap(null);
    setGoalOpen(false);
    setLearnOpen(false);
    setBadgeToast([]);
    setLevelUp(null);
    setMasteryWin(null);
    void load();
    return () => {
      workspaceRequestRef.current += 1;
      extensionRequestRef.current += 1;
      answerRequestRef.current += 1;
      helpRequestRef.current += 1;
      recapRequestRef.current += 1;
      goalRequestRef.current += 1;
    };
  }, [load, sessionId]);

  useEffect(() => {
    if (!badgeToast.length) return;
    const timer = setTimeout(() => setBadgeToast([]), 5000);
    return () => clearTimeout(timer);
  }, [badgeToast]);

  useEffect(() => {
    if (!levelUp) return;
    const timer = setTimeout(() => setLevelUp(null), 5000);
    return () => clearTimeout(timer);
  }, [levelUp]);

  useEffect(() => {
    if (!masteryWin) return;
    const timer = setTimeout(() => setMasteryWin(null), 6000);
    return () => clearTimeout(timer);
  }, [masteryWin]);

  const hasAction = (action: string) =>
    workspace?.allowed_actions.includes(action) ?? false;

  // The optional challenge tier: while an extension problem is active it is
  // the problem being answered; it never changes mastery or progress.
  const activeExtensionProblem =
    extensionSessionId === sessionId ? extensionProblem : null;
  const currentProblem = activeExtensionProblem ?? workspace?.problem ?? null;

  const problemKind = currentProblem?.answer_kind ?? "FREE_TEXT";
  const effectiveAnswer =
    problemKind === "FRACTION"
      ? fracNum.trim() && fracDen.trim()
        ? `${fracNum.trim()}/${fracDen.trim()}`
        : ""
      : answer;

  const problemId = currentProblem?.id;
  useEffect(() => {
    setAnswer("");
    setFracNum("");
    setFracDen("");
  }, [problemId]);

  const activeSkillId = workspace?.focus.active_skill_id;
  const learn = workspace?.focus.learn ?? null;
  const equationEquivalenceEnabled = equationEquivalenceEligible(
    workspace?.state ?? "",
    workspace ? {
      curriculumName: workspace.curriculum.name,
      jurisdiction: workspace.curriculum.jurisdiction,
      skillName: workspace.focus.skill_name,
    } : null,
    import.meta.env.VITE_ENABLE_DRAFT_MTH1W_EQUATION_FLOW === "true",
  );
  useEffect(() => {
    setLearnOpen(Boolean(workspace?.focus.in_remediation && learn));
  }, [activeSkillId]);

  const goalReached = workspace?.daily_goal?.reached ?? false;
  useEffect(() => {
    if (goalReached) setGoalWasReached(true);
  }, [goalReached]);

  function insertToken(token: string) {
    const el = answerRef.current;
    const s = el?.selectionStart ?? answer.length;
    const e = el?.selectionEnd ?? s;
    let next: string;
    let cursor: number;
    if (token === "\b") {
      const from = s === e ? Math.max(0, s - 1) : s;
      next = answer.slice(0, from) + answer.slice(e);
      cursor = from;
    } else {
      next = answer.slice(0, s) + token + answer.slice(e);
      cursor = s + token.length;
    }
    setAnswer(next);
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(cursor, cursor);
    });
  }

  async function saveDailyGoal(questions: number | null) {
    if (!sessionId) return;
    const requestedSessionId = sessionId;
    const requestId = ++goalRequestRef.current;
    try {
      await api<unknown>(
        `/learner-workspace/sessions/${requestedSessionId}/daily-goal`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ questions_per_day: questions }),
        },
      );
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          goalRequestRef.current,
        )
      ) {
        return;
      }
      setGoalOpen(false);
      await load();
    } catch (err) {
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          goalRequestRef.current,
        )
      ) {
        return;
      }
      setError(err instanceof ApiError ? err.message : "Could not save goal");
    }
  }

  async function openRecap() {
    if (!sessionId) return;
    const requestedSessionId = sessionId;
    const requestId = ++recapRequestRef.current;
    try {
      const summary = await api<SessionSummary>(
        `/learner-workspace/sessions/${requestedSessionId}/summary`,
      );
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          recapRequestRef.current,
        )
      ) {
        return;
      }
      setRecap(summary);
    } catch (err) {
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          recapRequestRef.current,
        )
      ) {
        return;
      }
      setError(err instanceof ApiError ? err.message : "Could not load recap");
    }
  }

  async function submitAnswerText(text: string) {
    if (!currentProblem || !text || !sessionId) return;
    const requestedSessionId = sessionId;
    const requestId = ++answerRequestRef.current;
    const submittedProblemId = currentProblem.id;
    const submittedExtension = Boolean(activeExtensionProblem);
    setError("");
    setStatus("Checking your work…");
    try {
      const result = await post<RespondOut>(
        `/adaptive-tutor/sessions/${requestedSessionId}/respond`,
        {
          problem_id: submittedProblemId,
          answer: text,
          assistance_level: 0,
        },
      );
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          answerRequestRef.current,
        )
      ) {
        return;
      }
      setAnswer("");
      setFracNum("");
      setFracDen("");
      const correct = result.evaluation.correct;
      setFeedback("");
      requestAnimationFrame(() => {
        if (
          isCurrentSessionOperationResponse(
            requestedSessionId,
            activeSessionRef.current,
            requestId,
            answerRequestRef.current,
          )
        ) {
          setFeedback(correct ? "correct" : "wrong");
        }
      });
      setStatus(
        correct
          ? "Correct. Keep going."
          : "Not yet. Use the feedback and try the next step.",
      );
      setStatusOk(correct);
      if (correct) {
        setCelebrate((c) => c + 1);
      }
      if (result.xp_earned) {
        setStatus((currentStatus) => `${currentStatus} +${result.xp_earned} XP`);
      }
      if (result.new_awards?.length) {
        setBadgeToast(result.new_awards);
        const mastered = result.new_awards.find((a) => a.code === "SKILL_MASTERED");
        if (mastered) setMasteryWin(mastered);
      }
      if (result.growth?.leveled_up) {
        setLevelUp({
          level: result.growth.level,
          title: result.growth.level_title,
        });
      }
      if (submittedExtension) {
        // Challenge streak: retain it only for the session that requested it.
        setExtensionProblem(result.next_problem ?? null);
        setExtensionSessionId(
          result.next_problem ? requestedSessionId : null,
        );
        if (!result.next_problem) {
          setStatus("Challenge set complete — nice work!");
          setStatusOk(true);
        }
      }
      await load();
    } catch (err) {
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          answerRequestRef.current,
        )
      ) {
        return;
      }
      setError(err instanceof ApiError ? err.message : "Submit failed");
      setStatus("");
    }
  }

  function submitAnswer(event: FormEvent) {
    event.preventDefault();
    void submitAnswerText(effectiveAnswer);
  }

  async function requestExtension() {
    if (activeExtensionProblem || !sessionId) return;
    const requestedSessionId = sessionId;
    const requestId = ++extensionRequestRef.current;
    setError("");
    setStatus("Loading a challenge…");
    try {
      const problem = await post<WorkspaceProblem>(
        `/adaptive-tutor/sessions/${requestedSessionId}/extension`,
      );
      if (
        requestId !== extensionRequestRef.current ||
        !isCurrentSessionResponse(requestedSessionId, activeSessionRef.current)
      ) {
        return;
      }
      setExtensionProblem(problem);
      setExtensionSessionId(requestedSessionId);
      setStatus("Challenge mode — optional, doesn't affect your mastery.");
      setStatusOk(true);
    } catch (err) {
      if (
        requestId !== extensionRequestRef.current ||
        !isCurrentSessionResponse(requestedSessionId, activeSessionRef.current)
      ) {
        return;
      }
      setStatus("");
      setError(
        err instanceof ApiError && err.status === 404
          ? "No challenge problems for this skill yet."
          : err instanceof ApiError
            ? err.message
            : "Could not load a challenge",
      );
    }
  }

  function exitExtension() {
    extensionRequestRef.current += 1;
    setExtensionProblem(null);
    setExtensionSessionId(null);
    setStatus("");
  }

  async function requestHelp(reason: "HINT" | "I_DONT_UNDERSTAND") {
    if (!currentProblem || !sessionId) return;
    const requestedSessionId = sessionId;
    const requestId = ++helpRequestRef.current;
    const requestedProblemId = currentProblem.id;
    setError("");
    setStatus("");
    try {
      const result = await post<HintResponse>(
        `/adaptive-tutor/sessions/${requestedSessionId}/hint`,
        { problem_id: requestedProblemId, reason },
      );
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          helpRequestRef.current,
        )
      ) {
        return;
      }
      setStatus(
        result.message || "Support is not available in this learning state.",
      );
      setStatusOk(result.allowed);
      await load();
    } catch (err) {
      if (
        !isCurrentSessionOperationResponse(
          requestedSessionId,
          activeSessionRef.current,
          requestId,
          helpRequestRef.current,
        )
      ) {
        return;
      }
      setError(err instanceof ApiError ? err.message : "Hint failed");
    }
  }

  if (!workspace) {
    return (
      <div className="min-h-screen bg-background">
        <NavBar />
        <main className="mx-auto max-w-6xl px-4 py-12">
          {error ? (
            <p className="rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive" role="alert">
              {error}
            </p>
          ) : (
            <p className="text-muted-foreground">Loading your session…</p>
          )}
        </main>
      </div>
    );
  }

  const complete = workspace.state === "COMPLETE";
  const effective = STEP_ALIAS[workspace.state] ?? workspace.state;
  const activeIndex = STEP_ORDER.indexOf(effective);
  const masteryPct = Math.round(workspace.evidence.mastery_score * 100);

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-6">
        {/* Session header */}
        <div className="mb-6 rounded-2xl bg-gradient-to-br from-primary to-violet-700 p-6 text-primary-foreground shadow-raised">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="flex items-center gap-2.5 text-2xl font-bold tracking-tight">
                <Avatar avatarId={workspace.learner.avatar_id ?? "avatar-1"} size={40} />
                {workspace.learner.first_name} · Grade {workspace.learner.grade_level}
              </h1>
              <p className="mt-1 text-sm opacity-85">
                {[workspace.curriculum.jurisdiction, workspace.curriculum.name]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {workspace.growth && (
                <span
                  className="inline-flex items-center gap-2 rounded-full bg-white/15 py-1 pl-1 pr-3.5 text-sm font-semibold backdrop-blur"
                  title={`${workspace.growth.xp_in_level}/${workspace.growth.xp_for_next} XP to next level`}
                >
                  <LevelCrest level={workspace.growth.level} title={workspace.growth.level_title} size="sm" />
                  Lv {workspace.growth.level} · {workspace.growth.level_title}
                </span>
              )}
              {(workspace.growth?.xp_today ?? 0) > 0 && (
                <span
                  className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur"
                  title="XP earned today"
                >
                  Today +{workspace.growth?.xp_today} XP
                </span>
              )}
              <Link
                to={`/learn/${sessionId}/map`}
                className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-medium backdrop-blur transition-colors hover:bg-white/25"
              >
                <MapIcon className="h-4 w-4" /> Skill map
              </Link>
              <Link
                to={`/learn/${sessionId}/catalog`}
                className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-medium backdrop-blur transition-colors hover:bg-white/25"
              >
                <BookOpen className="h-4 w-4" /> Catalog
              </Link>
              <Link to="/help/progress-and-mastery" className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-medium backdrop-blur transition-colors hover:bg-white/25">
                <HelpCircle className="h-4 w-4" /> Help
              </Link>
              {workspace.daily_goal ? (
                <button
                  type="button"
                  onClick={() => setGoalOpen((o) => !o)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-semibold backdrop-blur transition-colors",
                    workspace.daily_goal.reached
                      ? "bg-emerald-300 text-emerald-950"
                      : "bg-white/15 hover:bg-white/25",
                  )}
                  title="Daily goal — tap to change"
                  aria-label={`Daily goal: ${workspace.daily_goal.done} of ${workspace.daily_goal.target} questions`}
                >
                  <Target className="h-4 w-4" />
                  {workspace.daily_goal.reached
                    ? "Goal met!"
                    : `Goal ${workspace.daily_goal.done}/${workspace.daily_goal.target}`}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setGoalOpen((o) => !o)}
                  className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-medium backdrop-blur transition-colors hover:bg-white/25"
                  title="Set a daily goal"
                >
                  <Target className="h-4 w-4" /> Set a goal
                </button>
              )}
              <button
                type="button"
                onClick={() => void openRecap()}
                className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-medium backdrop-blur transition-colors hover:bg-white/25"
              >
                <Flag className="h-4 w-4" /> Wrap up
              </button>
              <SmartScoreBadge
                score={workspace.evidence.smartscore}
                streak={workspace.evidence.streak_count}
                daysStreak={workspace.streak_days}
                level={workspace.evidence.mastery_level}
                skillName={workspace.focus.skill_name}
              />
            </div>
          </div>
          {goalOpen && (
            <div className="mt-3 inline-flex flex-wrap items-center gap-2 rounded-xl bg-white/10 px-4 py-3 backdrop-blur" role="group" aria-label="Choose a daily goal">
              <span className="text-sm font-medium text-white/90">Questions per day:</span>
              {[5, 10, 20].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => void saveDailyGoal(n)}
                  className={cn(
                    "rounded-full px-3 py-1 text-sm font-semibold transition-colors",
                    workspace.daily_goal?.target === n
                      ? "bg-amber-300 text-amber-950"
                      : "bg-white/15 hover:bg-white/25",
                  )}
                >
                  {n}
                </button>
              ))}
              {workspace.daily_goal && (
                <button
                  type="button"
                  onClick={() => void saveDailyGoal(null)}
                  className="rounded-full bg-white/15 px-3 py-1 text-sm font-medium transition-colors hover:bg-white/25"
                >
                  Clear
                </button>
              )}
              <button
                type="button"
                onClick={() => setGoalOpen(false)}
                className="rounded-full bg-white/15 px-3 py-1 text-sm font-medium transition-colors hover:bg-white/25"
              >
                Done
              </button>
            </div>
          )}
          {workspace.growth && (
            <div className="mt-3 flex items-center gap-2" aria-label={`Level progress: ${workspace.growth.xp_in_level} of ${workspace.growth.xp_for_next} XP`}>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/20">
                <div
                  className="h-full rounded-full bg-amber-300 transition-all"
                  style={{
                    width: `${Math.min(100, Math.round((workspace.growth.xp_in_level / Math.max(1, workspace.growth.xp_for_next)) * 100))}%`,
                  }}
                />
              </div>
              <span className="text-xs font-medium text-white/80">
                {workspace.growth.xp_in_level}/{workspace.growth.xp_for_next} XP
              </span>
            </div>
          )}
          {/* Stepper */}
          <ol className="mt-5 flex flex-wrap items-center gap-x-1 gap-y-2" aria-label="Learning state">
            {STEP_ORDER.map((step, index) => (
              <li key={step} className="flex items-center">
                <span
                  className={cn(
                    "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold",
                    index === activeIndex
                      ? "bg-white text-primary"
                      : index < activeIndex
                        ? "bg-white/20 text-white"
                        : "text-white/60",
                  )}
                >
                  {index < activeIndex && <CheckCircle2 className="h-3.5 w-3.5" />}
                  {STEP_LABELS[index]}
                </span>
                {index < STEP_ORDER.length - 1 && (
                  <span className="mx-1 h-px w-4 bg-white/30" aria-hidden="true" />
                )}
              </li>
            ))}
          </ol>
        </div>

        {/* Badge toast */}
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

        {/* Session recap */}
        {recap && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-label="Session recap">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Flag className="h-5 w-5 text-primary" /> Session recap
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {recap.daily_goal?.reached && (
                  <p className="rounded-md bg-emerald-500/10 px-3 py-2 text-sm font-semibold text-emerald-700">
                    Daily goal met — {recap.daily_goal.done}/{recap.daily_goal.target} questions today.
                  </p>
                )}
                <dl className="grid grid-cols-2 gap-3 text-center">
                  <div className="rounded-lg bg-secondary px-3 py-2">
                    <dt className="text-xs font-medium text-muted-foreground">Questions</dt>
                    <dd className="text-xl font-bold">{recap.attempts}</dd>
                  </div>
                  <div className="rounded-lg bg-secondary px-3 py-2">
                    <dt className="text-xs font-medium text-muted-foreground">Correct</dt>
                    <dd className="text-xl font-bold">
                      {recap.correct}
                      <span className="text-sm font-normal text-muted-foreground"> ({recap.independent_correct} solo)</span>
                    </dd>
                  </div>
                  <div className="rounded-lg bg-secondary px-3 py-2">
                    <dt className="text-xs font-medium text-muted-foreground">XP earned</dt>
                    <dd className="text-xl font-bold">+{recap.xp_earned}</dd>
                  </div>
                  <div className="rounded-lg bg-secondary px-3 py-2">
                    <dt className="text-xs font-medium text-muted-foreground">SmartScore</dt>
                    <dd className="text-xl font-bold">
                      {recap.smartscore_now}
                      {recap.smartscore_start !== null && recap.smartscore_now !== recap.smartscore_start && (
                        <span className="text-sm font-normal text-emerald-700">
                          {" "}(+{recap.smartscore_now - recap.smartscore_start})
                        </span>
                      )}
                    </dd>
                  </div>
                </dl>
                <div className="space-y-1 text-sm">
                  {recap.minutes > 0 && <p>Time practicing: about {recap.minutes} min</p>}
                  {recap.skills_practiced.length > 0 && (
                    <p>Skills: {recap.skills_practiced.join(", ")}</p>
                  )}
                  {recap.misconceptions.length > 0 && (
                    <ul className="space-y-1">
                      {recap.misconceptions.map((m) => (
                        <li key={m.code} className="flex items-center gap-2">
                          {m.resolved ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          ) : (
                            <HelpCircle className="h-4 w-4 text-amber-600" />
                          )}
                          {m.resolved
                            ? `Worked through: ${m.name}`
                            : `Still working on: ${m.name}`}
                        </li>
                      ))}
                    </ul>
                  )}
                  {recap.awards.length > 0 && (
                    <p className="font-medium">
                      Badges: {recap.awards.map((a) => a.name).join(", ")}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 pt-1">
                  <Button onClick={() => setRecap(null)} className="flex-1">
                    Keep practicing
                  </Button>
                  <Link to="/learn" className="flex-1">
                    <Button variant="outline" className="w-full">
                      Done for now
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Level-up celebration */}
        {levelUp && (
          <div
            className="fixed inset-0 z-50 grid place-items-center bg-black/40"
            role="alertdialog"
            aria-label={`Level up! You reached level ${levelUp.level}`}
            onClick={() => setLevelUp(null)}
          >
            <div className="relative rounded-3xl bg-gradient-to-br from-amber-300 to-orange-400 p-10 text-center text-amber-950 shadow-2xl">
              <ConfettiBurst trigger={1} always />
              <p className="text-sm font-bold uppercase tracking-widest">
                Level up
              </p>
              <p className="mt-1 text-4xl font-extrabold">
                Level {levelUp.level}
              </p>
              <p className="mt-2 text-lg font-semibold">
                You're now a {levelUp.title}
              </p>
              <p className="mt-3 text-sm opacity-80">
                Keep practicing to reach the next level
              </p>
            </div>
          </div>
        )}

        {/* Skill-mastery celebration */}
        {masteryWin && (
          <div
            className="fixed inset-0 z-50 grid place-items-center bg-black/40"
            role="alertdialog"
            aria-label={`Skill mastered: ${masteryWin.skill_name ?? masteryWin.name}`}
            onClick={() => setMasteryWin(null)}
          >
            <div className="relative rounded-3xl bg-gradient-to-br from-emerald-300 to-teal-500 p-10 text-center text-emerald-950 shadow-2xl">
              <ConfettiBurst trigger={1} always />
              <p className="text-sm font-bold uppercase tracking-widest">
                Skill mastered
              </p>
              <p className="mt-1 text-3xl font-extrabold">
                {masteryWin.skill_name ?? masteryWin.name}
              </p>
              <p className="mt-3 text-sm opacity-80">
                Mastery verified — review will keep it sharp
              </p>
            </div>
          </div>
        )}

        {/* Review banner */}
        {workspace.reviews_due.length > 0 && (
          <div className="mb-4 rounded-xl border-l-4 border-primary bg-secondary/60 px-4 py-3 text-sm" role="status">
            <strong>Quick refresh:</strong>{" "}
            {workspace.reviews_due.map((r) => r.skill_name).join(", ")}
          </div>
        )}

        {error && (
          <p className="mb-4 rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive" role="alert">
            {error}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <div className="space-y-6">
            {workspace.focus.in_remediation && !complete && (
              <div
                className="flex items-start gap-3 rounded-xl border border-sky-300/70 bg-sky-50 px-4 py-3"
                role="status"
                data-testid="remediation-banner"
              >
                {workspace.focus.remediation_reason === "SPACED_REVIEW" ? (
                  <>
                    <RefreshCcw className="mt-0.5 h-5 w-5 shrink-0 text-sky-700" aria-hidden="true" />
                    <p className="text-sm leading-relaxed text-sky-900">
                      Quick review — a few questions on{" "}
                      <strong>{workspace.focus.skill_name}</strong> to keep it
                      fresh, then we move on.
                    </p>
                  </>
                ) : (
                  <>
                    <Undo2 className="mt-0.5 h-5 w-5 shrink-0 text-sky-700" aria-hidden="true" />
                    <p className="text-sm leading-relaxed text-sky-900">
                      Stepping back on purpose: practicing{" "}
                      <strong>{workspace.focus.skill_name}</strong> first makes{" "}
                      <strong>{workspace.focus.primary_skill_name}</strong> much
                      easier. Once you&apos;ve got it, we go straight back.
                    </p>
                  </>
                )}
              </div>
            )}
            {complete ? (
              <Card className="completion" id="completionPanel">
                <ConfettiBurst trigger={celebrate} always />
                <CardContent className="flex flex-col items-center py-10 text-center">
                  <svg viewBox="0 0 64 64" width="72" height="72" aria-hidden="true">
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
                  <h2 className="mt-4 text-2xl font-bold">Skill complete</h2>
                  <Badge className="mt-2">Badge earned: {workspace.focus.skill_name}</Badge>
                  <p className="mt-3 text-muted-foreground">
                    You answered correctly and independently in the mastery check.
                  </p>
                  {workspace.recommended_next && (
                    <p className="mt-2 text-sm text-muted-foreground">
                      Up next: {workspace.recommended_next.skill_name}
                    </p>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle>
                      {activeExtensionProblem ? "Challenge" : "Current problem"}
                    </CardTitle>
                    {activeExtensionProblem ? (
                      <Badge variant="secondary">Optional</Badge>
                    ) : (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => void requestExtension()}
                        title="Try a harder problem — optional, doesn't affect your mastery"
                      >
                        <Target className="h-4 w-4" /> Challenge me
                      </Button>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {activeExtensionProblem
                      ? `${workspace.focus.skill_name} · stretch — doesn't count toward mastery`
                      : `${workspace.focus.skill_name} · ${friendly(workspace.state)}`}
                  </p>
                  {activeExtensionProblem && (
                    <button
                      type="button"
                      className="text-left text-xs font-medium text-primary hover:underline"
                      onClick={exitExtension}
                    >
                      Back to practice
                    </button>
                  )}
                </CardHeader>
                <CardContent className="space-y-4">
                  {learn && (workspace.state === "GUIDED_PRACTICE" || workspace.state === "REMEDIATION") && (
                    <div className="rounded-lg border border-accent/50 bg-accent/5">
                      <button
                        type="button"
                        onClick={() => setLearnOpen((o) => !o)}
                        aria-expanded={learnOpen}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-sm font-semibold text-accent"
                      >
                        <BookOpen className="h-4 w-4 text-accent" />
                        Learn the idea first
                        <ChevronDown
                          className={cn(
                            "ml-auto h-4 w-4 transition-transform",
                            learnOpen && "rotate-180",
                          )}
                        />
                      </button>
                      {learnOpen && (
                        <div className="border-t border-accent/30 px-4 py-3">
                          <LearnPanel
                            learn={learn}
                            integerPracticeSeed={
                              integerAdditionEligible(workspace.state, learn)
                                ? integerSeedFromString(
                                    currentProblem?.id ??
                                      workspace.focus.active_skill_id,
                                  )
                                : undefined
                            }
                            independentAssessment={
                              workspace.state !== "GUIDED_PRACTICE" &&
                              workspace.state !== "REMEDIATION"
                            }
                          />
                        </div>
                      )}
                    </div>
                  )}
                  {/* Distributive, linear and balance lessons stay disabled until
                      the API supplies separately reviewed exact capabilities. Display
                      names and sibling labels never authorize a guided mount. */}
                  {equationEquivalenceEnabled && (
                    <InteractiveEquationEquivalence
                      key={`equation-equivalence-${currentProblem?.id ?? workspace.focus.active_skill_id}`}
                      exampleIndex={equationEquivalenceExampleIndex(
                        currentProblem?.id ?? workspace.focus.active_skill_id,
                        workspace.focus.skill_name,
                      )}
                      independentAssessment={false}
                    />
                  )}
                  {/* Dot-plot exploration remains fail-closed without an accepted
                      server-owned capability contract. */}
                  {/* Default off until LearnerWorkspace exposes an approved server-owned capability. */}
                  {/* Probability-tree route remains disabled until an approved server-owned capability is available. */}
                  {showPolynomialDivisionExploration(workspace.state, undefined) && (
                    <InteractivePolynomialDivision
                      key={workspace.focus.active_skill_id}
                      independentAssessment={workspace.state !== "GUIDED_PRACTICE" && workspace.state !== "REMEDIATION"}
                    />
                  )}
                  <div className="problem-wrap">
                    <div className={`problem ${feedback}`} aria-live="polite">
                      <MathText
                        text={
                          currentProblem?.prompt ??
                          "No problem is currently assigned."
                        }
                      />
                    </div>
                    <ProblemVisual spec={currentProblem?.visual ?? null} />
                    {(workspace.state === "GUIDED_PRACTICE" ||
                      workspace.state === "REMEDIATION") &&
                      currentProblem?.visual?.type === "fraction_bar" && (
                        <InteractiveFractionBars
                          key={currentProblem.id}
                          independentAssessment={
                            workspace.state !== "GUIDED_PRACTICE" &&
                            workspace.state !== "REMEDIATION"
                          }
                          denominator={currentProblem.visual.denominator}
                          initialNumerator={currentProblem.visual.numerator}
                          compareWith={
                            fractionComparisonTarget(currentProblem.visual) ??
                            undefined
                          }
                        />
                      )}
                    {(workspace.state === "GUIDED_PRACTICE" ||
                      workspace.state === "REMEDIATION") &&
                      currentProblem?.visual?.type === "fraction_operation" &&
                      currentProblem.visual.operation === "+" && (
                        <InteractiveFractionAddition
                          key={currentProblem.id}
                          independentAssessment={
                            workspace.state !== "GUIDED_PRACTICE" &&
                            workspace.state !== "REMEDIATION"
                          }
                          first={currentProblem.visual.first}
                          second={currentProblem.visual.second}
                        />
                      )}
                    <ScratchPad />
                    {feedback === "correct" && <ConfettiBurst trigger={celebrate} />}
                  </div>
                  <form onSubmit={submitAnswer} className="space-y-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="answer">
                        {currentProblem?.supports_steps
                          ? "Your work"
                          : "Your answer"}
                      </Label>
                      {currentProblem?.supports_steps && sessionId ? (
                        <StepWork
                          key={currentProblem.id}
                          sessionId={sessionId}
                          problemId={currentProblem.id}
                          problemType={currentProblem.problem_type}
                          disabled={!hasAction("SUBMIT_ANSWER")}
                          onSolved={(line) => void submitAnswerText(line)}
                          onError={setError}
                        />
                      ) : problemKind === "MULTIPLE_CHOICE" &&
                      currentProblem?.choices?.length ? (
                        <div
                          role="radiogroup"
                          aria-label="Answer choices"
                          className="grid gap-2 sm:grid-cols-2"
                        >
                          {currentProblem.choices.map((choice) => (
                            <button
                              key={choice.id}
                              type="button"
                              role="radio"
                              aria-checked={answer === choice.id}
                              onClick={() => setAnswer(choice.id)}
                              disabled={
                                !hasAction("SUBMIT_ANSWER") ||
                                !currentProblem
                              }
                              className={cn(
                                "rounded-lg border px-4 py-3 text-left text-base transition-colors",
                                "hover:border-primary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                                "disabled:cursor-not-allowed disabled:opacity-50",
                                answer === choice.id
                                  ? "border-primary bg-primary/10 font-medium"
                                  : "border-border bg-card",
                              )}
                            >
                              <MathText text={choice.text} />
                            </button>
                          ))}
                        </div>
                      ) : problemKind === "FRACTION" ? (
                        <div className="inline-flex flex-col items-center gap-1">
                          <Input
                            id="answer-num"
                            aria-label="Numerator"
                            className="h-12 w-24 text-center text-lg"
                            inputMode="numeric"
                            value={fracNum}
                            onChange={(e) => setFracNum(e.target.value)}
                            disabled={
                              !hasAction("SUBMIT_ANSWER") || !currentProblem
                            }
                            autoComplete="off"
                          />
                          <div className="h-0.5 w-24 bg-foreground" aria-hidden="true" />
                          <Input
                            id="answer-den"
                            aria-label="Denominator"
                            className="h-12 w-24 text-center text-lg"
                            inputMode="numeric"
                            value={fracDen}
                            onChange={(e) => setFracDen(e.target.value)}
                            disabled={
                              !hasAction("SUBMIT_ANSWER") || !currentProblem
                            }
                            autoComplete="off"
                          />
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <Input
                            id="answer"
                            ref={answerRef}
                            className="h-12 text-lg"
                            inputMode={
                              problemKind === "INTEGER" ? "numeric" : undefined
                            }
                            value={answer}
                            onChange={(e) => setAnswer(e.target.value)}
                            disabled={
                              !hasAction("SUBMIT_ANSWER") || !currentProblem
                            }
                            autoComplete="off"
                          />
                          <MathKeypad
                            onKey={insertToken}
                            variables={problemKind === "FREE_TEXT"}
                            disabled={
                              !hasAction("SUBMIT_ANSWER") || !currentProblem
                            }
                          />
                        </div>
                      )}
                    </div>
                    {!currentProblem?.supports_steps && (
                      <VoiceChatControls
                        onTranscript={setAnswer}
                        promptToRead={workspace.coaching_message}
                        disabled={!hasAction("SUBMIT_ANSWER") || !currentProblem}
                      />
                    )}
                    <div className="flex flex-wrap gap-2">
                      {!currentProblem?.supports_steps && (
                        <Button
                          type="submit"
                          size="lg"
                          disabled={
                            !hasAction("SUBMIT_ANSWER") ||
                            !currentProblem ||
                            !effectiveAnswer
                          }
                        >
                          Submit answer
                        </Button>
                      )}
                      <Button
                        type="button"
                        variant="outline"
                        size="lg"
                        onClick={() => requestHelp("HINT")}
                        disabled={!hasAction("REQUEST_HINT") || !currentProblem}
                      >
                        <Lightbulb className="h-4 w-4" /> Hint
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="lg"
                        onClick={() => requestHelp("I_DONT_UNDERSTAND")}
                        disabled={
                          !hasAction("I_DONT_UNDERSTAND") || !currentProblem
                        }
                      >
                        <HelpCircle className="h-4 w-4" /> I don&apos;t understand
                      </Button>
                    </div>
                  </form>
                  {status && (
                    <p
                      className={cn(
                        "text-sm font-medium",
                        statusOk ? "text-emerald-700" : "text-muted-foreground",
                      )}
                      aria-live="polite"
                    >
                      {status}
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Coach */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle>Coach</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary font-bold text-primary-foreground">
                    T
                  </span>
                  <ChatMessage
                    content={
                      complete
                        ? "Nice work. Your independent mastery check is complete."
                        : (workspace.coaching_message ??
                          "Work through the problem carefully.")
                    }
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <aside className="space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle>Progress</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
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
                    <div className="text-sm font-medium capitalize text-muted-foreground">
                      {workspace.evidence.mastery_level}
                    </div>
                  </div>
                </div>
                <Progress value={masteryPct} />
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg bg-secondary/60 p-3">
                    <p className="text-xs font-medium text-muted-foreground">Independent correct</p>
                    <p className="mt-1 text-xl font-bold text-primary">
                      {workspace.evidence.independent_correct_count} /{" "}
                      {workspace.evidence.independent_attempt_count}
                    </p>
                  </div>
                  <div className="rounded-lg bg-secondary/60 p-3">
                    <p className="text-xs font-medium text-muted-foreground">Assisted successes</p>
                    <p className="mt-1 text-xl font-bold text-primary">
                      {workspace.evidence.hinted_correct_count}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Help can support learning, but assisted success is not counted
                  as independent mastery evidence.
                </p>
                {workspace.recommended_next && !complete && (
                  <p className="text-sm text-muted-foreground">
                    Up next: <strong>{workspace.recommended_next.skill_name}</strong>
                  </p>
                )}
              </CardContent>
            </Card>

            {workspace.awards.length > 0 && (
              <Card data-testid="badge-shelf">
                <CardHeader className="flex-row items-center justify-between pb-3">
                  <CardTitle>Badges</CardTitle>
                  <Link
                    className="text-sm text-muted-foreground hover:text-foreground"
                    to={`/learn/${sessionId}/badges`}
                  >
                    View all
                  </Link>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {workspace.awards.map((award) => (
                      <li
                        key={award.code + (award.skill_name ?? "")}
                        className="flex items-center gap-3"
                      >
                        <BadgeIcon small />
                        <div className="min-w-0">
                          <p className="text-sm font-semibold">{award.name}</p>
                          <p className="truncate text-xs text-muted-foreground">
                            {award.skill_name
                              ? `${award.description} · ${award.skill_name}`
                              : award.description}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
