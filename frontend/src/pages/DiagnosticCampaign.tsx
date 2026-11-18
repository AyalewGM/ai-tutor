import { FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Compass, Map, MinusCircle, Sparkles } from "lucide-react";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { CampaignOut, CampaignReport, CampaignStrand, SessionOut } from "../types";

const READINESS_STYLE: Record<CampaignStrand["readiness"], { icon: typeof CheckCircle2; label: string; className: string }> = {
  STRONG: { icon: CheckCircle2, label: "Strong", className: "border-emerald-200 bg-emerald-50 text-emerald-700" },
  DEVELOPING: { icon: MinusCircle, label: "Developing", className: "border-amber-200 bg-amber-50 text-amber-700" },
  EMERGING: { icon: AlertTriangle, label: "Emerging", className: "border-rose-200 bg-rose-50 text-rose-700" },
  NOT_PROBED: { icon: MinusCircle, label: "Not probed", className: "border-border bg-muted text-muted-foreground" },
};

export default function DiagnosticCampaign() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const learnerId = searchParams.get("learner") ?? "";

  const [payload, setPayload] = useState<CampaignOut | null>(
    (location.state as { campaign?: CampaignOut } | null)?.campaign ?? null,
  );
  const [report, setReport] = useState<CampaignReport | null>(null);
  const [answer, setAnswer] = useState("");
  const [fracNum, setFracNum] = useState("");
  const [fracDen, setFracDen] = useState("");
  const [selectedChoice, setSelectedChoice] = useState("");
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (payload || !campaignId) return;
    api<CampaignOut>(`/diagnostics/campaigns/${campaignId}`)
      .then(setPayload)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load knowledge check"));
  }, [payload, campaignId]);

  const completed = payload?.status === "COMPLETED";
  useEffect(() => {
    if (!completed || report || !campaignId) return;
    api<CampaignReport>(`/diagnostics/campaigns/${campaignId}/report`)
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load report"));
  }, [completed, report, campaignId]);

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

  const progressPct = payload
    ? Math.min(100, Math.round((payload.question_count / Math.max(1, payload.max_questions)) * 100))
    : 0;

  const strands = useMemo(() => report?.strands ?? [], [report]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!problem || !effectiveAnswer) return;
    setError("");
    try {
      const result = await post<CampaignOut>(`/diagnostics/campaigns/${campaignId}/respond`, {
        problem_id: problem.id,
        answer: effectiveAnswer,
      });
      setPayload(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit answer");
    }
  }

  async function startRecommended() {
    if (!learnerId || !report?.recommended) return;
    setStarting(true);
    setError("");
    try {
      const session = await post<SessionOut>("/adaptive-tutor/sessions", {
        student_id: learnerId,
        skill_id: report.recommended.id,
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
            Knowledge check
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">Map what you know</h1>
          <p className="mt-1 text-muted-foreground">
            Answer on your own — no hints. We'll sample across the course and build your knowledge map.
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
                  area {Math.min(payload.targets_probed, payload.targets_planned)} of {payload.targets_planned} · up to {payload.max_questions} questions
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
              {payload.current_skill && (
                <p className="text-xs text-muted-foreground">
                  Now checking: <span className="font-medium text-foreground">{payload.current_skill.name}</span>
                </p>
              )}
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
          <div className="space-y-4">
            <Card className="text-center">
              <CardHeader>
                <Sparkles className="mx-auto h-10 w-10 text-primary" />
                <CardTitle className="mt-2">Your knowledge map is ready</CardTitle>
                <CardDescription>
                  {payload.question_count} questions answered across {payload.targets_probed} areas
                </CardDescription>
              </CardHeader>
              {report?.recommended && (
                <CardContent>
                  <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 text-left">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Best place to start
                    </p>
                    <p className="mt-1 text-lg font-semibold">{report.recommended.name}</p>
                    <p className="text-xs font-mono text-muted-foreground">{report.recommended.code}</p>
                  </div>
                  <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-center">
                    {learnerId && (
                      <Button onClick={startRecommended} disabled={starting}>
                        <Compass className="h-4 w-4" />
                        {starting ? "Starting…" : "Start practicing"}
                      </Button>
                    )}
                    <Button variant="secondary" onClick={() => navigate("/learn")}>
                      Back to topics
                    </Button>
                  </div>
                </CardContent>
              )}
            </Card>

            {strands.length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Map className="h-4 w-4 text-primary" /> Strand by strand
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {strands.map((strand) => {
                    const style = READINESS_STYLE[strand.readiness];
                    const Icon = style.icon;
                    return (
                      <div
                        key={strand.name}
                        className={cn("flex items-center gap-3 rounded-xl border p-3", style.className)}
                      >
                        <Icon className="h-5 w-5 shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{strand.name}</p>
                          <p className="text-xs opacity-80">
                            {strand.skills_ready} of {strand.skills_probed} probed skills solid
                            {strand.skills_total > strand.skills_probed &&
                              ` · ${strand.skills_probed} of ${strand.skills_total} skills checked`}
                          </p>
                          {strand.deepest_gap && (
                            <p className="mt-0.5 text-xs opacity-80">
                              Build first: {strand.deepest_gap.name}
                            </p>
                          )}
                        </div>
                        <span className="shrink-0 text-xs font-semibold">{style.label}</span>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            )}

            {!report && !error && (
              <Card>
                <CardContent className="space-y-3 pt-6">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </CardContent>
              </Card>
            )}
          </div>
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
