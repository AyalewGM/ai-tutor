import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BookOpen, CheckCircle2, ChevronDown, Flame, Lightbulb, Map as MapIcon, HelpCircle } from "lucide-react";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import ProblemVisual from "../components/ProblemVisual";
import VoiceChatControls from "../components/chat/VoiceChatControls";
import MathText from "../components/MathText";
import LearnPanel from "../components/LearnPanel";
import ScratchPad from "../components/ScratchPad";
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
  const [fracNum, setFracNum] = useState("");
  const [fracDen, setFracDen] = useState("");
  const [status, setStatus] = useState("");
  const [statusOk, setStatusOk] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<"" | "correct" | "wrong">("");
  const [celebrate, setCelebrate] = useState(0);
  const [badgeToast, setBadgeToast] = useState<Award[]>([]);
  const [learnOpen, setLearnOpen] = useState(false);

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

  const problemKind = workspace?.problem?.answer_kind ?? "FREE_TEXT";
  const effectiveAnswer =
    problemKind === "FRACTION"
      ? fracNum.trim() && fracDen.trim()
        ? `${fracNum.trim()}/${fracDen.trim()}`
        : ""
      : answer;

  const problemId = workspace?.problem?.id;
  useEffect(() => {
    setAnswer("");
    setFracNum("");
    setFracDen("");
  }, [problemId]);

  const activeSkillId = workspace?.focus.active_skill_id;
  const learn = workspace?.focus.learn ?? null;
  useEffect(() => {
    setLearnOpen(Boolean(workspace?.focus.in_remediation && learn));
  }, [activeSkillId]);

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
          answer: effectiveAnswer,
          assistance_level: 0,
        },
      );
      setAnswer("");
      setFracNum("");
      setFracDen("");
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
        setCelebrate((c) => c + 1);
      }
      if (result.xp_earned) {
        setStatus((s) => `${s} +${result.xp_earned} XP`);
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
              <h1 className="text-2xl font-bold tracking-tight">
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
                  className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur"
                  title={`${workspace.growth.xp_in_level}/${workspace.growth.xp_for_next} XP to next level`}
                >
                  Lv {workspace.growth.level} · {workspace.growth.level_title}
                </span>
              )}
              {(workspace.streak_days ?? 0) > 0 && (
                <span
                  className="inline-flex items-center gap-1.5 rounded-full bg-amber-400/90 px-3.5 py-1.5 text-sm font-semibold text-amber-950"
                  title="Consecutive days of practice"
                >
                  <Flame className="h-4 w-4" /> {workspace.streak_days}-day streak
                </span>
              )}
              <Link
                to={`/learn/${sessionId}/map`}
                className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-medium backdrop-blur transition-colors hover:bg-white/25"
              >
                <MapIcon className="h-4 w-4" /> Skill map
              </Link>
              <span className="rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur">
                Score {masteryPct}
              </span>
            </div>
          </div>
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
                  <CardTitle>Current problem</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {workspace.focus.skill_name} · {friendly(workspace.state)}
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  {learn && (
                    <div className="rounded-lg border border-accent/50 bg-accent/5">
                      <button
                        type="button"
                        onClick={() => setLearnOpen((o) => !o)}
                        aria-expanded={learnOpen}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-sm font-medium text-accent-foreground"
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
                          <LearnPanel learn={learn} />
                        </div>
                      )}
                    </div>
                  )}
                  <div className="problem-wrap">
                    <div className={`problem ${feedback}`} aria-live="polite">
                      <MathText
                        text={
                          workspace.problem?.prompt ??
                          "No problem is currently assigned."
                        }
                      />
                    </div>
                    <ProblemVisual spec={workspace.problem?.visual ?? null} />
                    <ScratchPad />
                    {feedback === "correct" && <ConfettiBurst trigger={celebrate} />}
                  </div>
                  <form onSubmit={submitAnswer} className="space-y-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="answer">Your answer</Label>
                      {problemKind === "MULTIPLE_CHOICE" &&
                      workspace.problem?.choices?.length ? (
                        <div
                          role="radiogroup"
                          aria-label="Answer choices"
                          className="grid gap-2 sm:grid-cols-2"
                        >
                          {workspace.problem.choices.map((choice) => (
                            <button
                              key={choice.id}
                              type="button"
                              role="radio"
                              aria-checked={answer === choice.id}
                              onClick={() => setAnswer(choice.id)}
                              disabled={
                                !hasAction("SUBMIT_ANSWER") ||
                                !workspace.problem
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
                              !hasAction("SUBMIT_ANSWER") || !workspace.problem
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
                              !hasAction("SUBMIT_ANSWER") || !workspace.problem
                            }
                            autoComplete="off"
                          />
                        </div>
                      ) : (
                        <Input
                          id="answer"
                          className="h-12 text-lg"
                          inputMode={
                            problemKind === "INTEGER" ? "numeric" : undefined
                          }
                          value={answer}
                          onChange={(e) => setAnswer(e.target.value)}
                          disabled={
                            !hasAction("SUBMIT_ANSWER") || !workspace.problem
                          }
                          autoComplete="off"
                        />
                      )}
                    </div>
                    <VoiceChatControls
                      onTranscript={setAnswer}
                      promptToRead={workspace.coaching_message}
                      disabled={!hasAction("SUBMIT_ANSWER") || !workspace.problem}
                    />
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="submit"
                        size="lg"
                        disabled={
                          !hasAction("SUBMIT_ANSWER") ||
                          !workspace.problem ||
                          !effectiveAnswer
                        }
                      >
                        Submit answer
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="lg"
                        onClick={() => requestHelp("HINT")}
                        disabled={!hasAction("REQUEST_HINT") || !workspace.problem}
                      >
                        <Lightbulb className="h-4 w-4" /> Hint
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="lg"
                        onClick={() => requestHelp("I_DONT_UNDERSTAND")}
                        disabled={
                          !hasAction("I_DONT_UNDERSTAND") || !workspace.problem
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
                  <div className="rounded-xl rounded-tl-sm bg-secondary px-4 py-3 text-sm leading-relaxed" aria-live="polite">
                    {complete
                      ? "Nice work. Your independent mastery check is complete."
                      : workspace.coaching_message ??
                        "Work through the problem carefully."}
                  </div>
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
                    <div className="text-sm text-muted-foreground">mastery</div>
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
