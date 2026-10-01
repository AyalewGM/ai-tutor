import { FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Compass, Sparkles } from "lucide-react";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { DiagnosticOut, SessionOut, SkillChoice } from "../types";

const REASON_COPY: Record<string, string> = {
  target_ready: "You're ready for this topic — let's go!",
  prerequisite_ready: "That earlier skill looks solid — building from there.",
  graph_boundary_gap: "We'll build up to your goal from an earlier step.",
  max_questions_reached: "Thanks! We have a good sense of where to start.",
};

export default function Diagnostic() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const learnerId = searchParams.get("learner") ?? "";

  const [payload, setPayload] = useState<DiagnosticOut | null>(
    (location.state as { diagnostic?: DiagnosticOut } | null)?.diagnostic ?? null,
  );
  const [skills, setSkills] = useState<SkillChoice[]>([]);
  const [answer, setAnswer] = useState("");
  const [fracNum, setFracNum] = useState("");
  const [fracDen, setFracDen] = useState("");
  const [selectedChoice, setSelectedChoice] = useState("");
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (payload || !sessionId) return;
    api<DiagnosticOut>(`/diagnostics/sessions/${sessionId}`)
      .then(setPayload)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load diagnostic"));
  }, [payload, sessionId]);

  useEffect(() => {
    if (!learnerId) return;
    api<SkillChoice[]>(`/onboarding/learners/${learnerId}/skills`).then(setSkills).catch(() => {});
  }, [learnerId]);

  const problem = payload?.problem ?? null;
  const problemId = problem?.id;
  useEffect(() => {
    setAnswer("");
    setFracNum("");
    setFracDen("");
    setSelectedChoice("");
  }, [problemId]);

  const problemKind = problem?.answer_kind ?? "FREE_TEXT";
  const effectiveAnswer =
    problemKind === "MULTIPLE_CHOICE"
      ? selectedChoice
      : problemKind === "FRACTION"
        ? fracNum.trim() && fracDen.trim()
          ? `${fracNum.trim()}/${fracDen.trim()}`
          : ""
        : answer;

  const completed = payload?.status === "COMPLETED";
  const recommendedSkill = useMemo(
    () => skills.find((s) => s.id === payload?.recommended_skill_id) ?? null,
    [skills, payload?.recommended_skill_id],
  );
  const progressPct = payload
    ? Math.min(100, Math.round((payload.question_count / Math.max(1, payload.max_questions)) * 100))
    : 0;

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!problem || !effectiveAnswer) return;
    setError("");
    try {
      const result = await post<DiagnosticOut>(`/diagnostics/sessions/${sessionId}/respond`, {
        problem_id: problem.id,
        answer: effectiveAnswer,
      });
      setPayload(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit answer");
    }
  }

  async function startRecommended() {
    if (!learnerId || !payload?.recommended_skill_id) return;
    setStarting(true);
    setError("");
    try {
      const session = await post<SessionOut>("/adaptive-tutor/sessions", {
        student_id: learnerId,
        skill_id: payload.recommended_skill_id,
      });
      navigate(`/learn/${session.session_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start session");
      setStarting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-2xl px-4 py-8">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-widest text-primary">
            Placement check
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">Find your starting point</h1>
          <p className="mt-1 text-muted-foreground">
            Answer on your own — no hints here. Wrong answers help us find the right level.
          </p>
        </div>

        {!payload && !error && (
          <Card>
            <CardContent className="space-y-3 pt-6">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="h-24 w-full" />
            </CardContent>
          </Card>
        )}

        {payload && !completed && problem && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  Question {payload.question_count + 1}
                </CardTitle>
                <span className="text-xs text-muted-foreground">
                  up to {payload.max_questions} questions
                </span>
              </div>
              <div
                className="h-1.5 overflow-hidden rounded-full bg-secondary"
                aria-label={`Question ${payload.question_count + 1} of up to ${payload.max_questions}`}
              >
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </CardHeader>
            <CardContent>
              <p className="problem text-lg font-medium leading-relaxed">{problem.prompt}</p>
              <form onSubmit={submit} className="mt-6 space-y-4">
                {problemKind === "MULTIPLE_CHOICE" && problem.choices ? (
                  <div className="grid gap-2">
                    {problem.choices.map((choice) => (
                      <button
                        key={choice.id}
                        type="button"
                        aria-pressed={selectedChoice === choice.id}
                        onClick={() => setSelectedChoice(choice.id)}
                        className={cn(
                          "rounded-xl border p-3 text-left font-medium transition-colors",
                          selectedChoice === choice.id
                            ? "border-primary bg-primary/10"
                            : "border-border bg-card hover:border-primary/40",
                        )}
                      >
                        {choice.text}
                      </button>
                    ))}
                  </div>
                ) : problemKind === "FRACTION" ? (
                  <div className="flex items-center justify-center gap-2">
                    <Input
                      value={fracNum}
                      onChange={(e) => setFracNum(e.target.value)}
                      className="w-20 text-center"
                      aria-label="Numerator"
                      inputMode="numeric"
                    />
                    <span className="text-2xl font-bold">/</span>
                    <Input
                      value={fracDen}
                      onChange={(e) => setFracDen(e.target.value)}
                      className="w-20 text-center"
                      aria-label="Denominator"
                      inputMode="numeric"
                    />
                  </div>
                ) : (
                  <Input
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Type your answer"
                    aria-label="Your answer"
                    autoFocus
                  />
                )}
                <Button type="submit" className="w-full" disabled={!effectiveAnswer}>
                  Check answer
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {payload && completed && (
          <Card className="text-center">
            <CardHeader>
              <Sparkles className="mx-auto h-10 w-10 text-primary" />
              <CardTitle className="mt-2">Nice work — we found your level</CardTitle>
              <CardDescription>
                {REASON_COPY[payload.placement_reason ?? ""] ?? "Your starting point is ready."}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {payload.question_count} question{payload.question_count === 1 ? "" : "s"} answered
              </p>
              {recommendedSkill && (
                <div className="rounded-xl border border-primary/30 bg-primary/5 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Recommended starting skill
                  </p>
                  <p className="mt-1 text-lg font-semibold">{recommendedSkill.name}</p>
                  <p className="text-xs font-mono text-muted-foreground">{recommendedSkill.code}</p>
                </div>
              )}
              <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
                {payload.recommended_skill_id && learnerId && (
                  <Button onClick={startRecommended} disabled={starting}>
                    <Compass className="h-4 w-4" />
                    {starting ? "Starting…" : "Start practicing"}
                  </Button>
                )}
                <Button variant="secondary" onClick={() => navigate("/learn")}>
                  Choose a topic instead
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <p
            className="mt-6 rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive"
            role="alert"
          >
            {error}
          </p>
        )}
      </main>
    </div>
  );
}
