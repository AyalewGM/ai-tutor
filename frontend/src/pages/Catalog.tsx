import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, BookOpen, CheckCircle2, CircleDashed, GraduationCap, PlayCircle } from "lucide-react";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { LearnerWorkspace } from "../types";

type CatalogSkill = {
  id: string;
  code: string;
  name: string;
  difficulty_level: number;
  mastery_score: number;
  status: string;
  content_ready: boolean;
  has_lesson: boolean;
};

type CatalogStrand = { name: string; skills: CatalogSkill[] };

type CatalogOption = {
  id: string;
  code: string;
  name: string;
  jurisdiction: string | null;
  grade_level: string | null;
  is_enrolled: boolean;
};

type CurriculumCatalog = {
  curriculum_id: string;
  curriculum_name: string;
  jurisdiction: string | null;
  grade_level: string | null;
  is_enrolled: boolean;
  can_select: boolean;
  options: CatalogOption[];
  strands: CatalogStrand[];
  skill_count: number;
  lesson_count: number;
};

function SkillStatus({ skill }: { skill: CatalogSkill }) {
  if (skill.status === "MASTERED") {
    return <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-label="Mastered" />;
  }
  if (skill.mastery_score > 0 || skill.status !== "NOT_STARTED") {
    return <PlayCircle className="h-4 w-4 text-primary" aria-label="In progress" />;
  }
  return <CircleDashed className="h-4 w-4 text-muted-foreground" aria-label="Not started" />;
}

export default function Catalog() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<LearnerWorkspace | null>(null);
  const [catalog, setCatalog] = useState<CurriculumCatalog | null>(null);
  const [error, setError] = useState("");
  const [busySkill, setBusySkill] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);

  const selectedCurriculum = params.get("curriculum");

  const loadCatalog = useCallback(
    async (studentId: string) => {
      const query = selectedCurriculum ? `?curriculum_id=${selectedCurriculum}` : "";
      setCatalog(
        await api<CurriculumCatalog>(
          `/onboarding/learners/${studentId}/catalog${query}`,
        ),
      );
    },
    [selectedCurriculum],
  );

  useEffect(() => {
    api<LearnerWorkspace>(`/learner-workspace/sessions/${sessionId}`)
      .then((ws) => {
        setWorkspace(ws);
        if (!ws.learner.id) throw new ApiError(409, "Learner identity unavailable");
        return loadCatalog(ws.learner.id);
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load the catalog"),
      );
  }, [sessionId, loadCatalog]);

  async function practice(skillId: string) {
    if (!workspace?.learner.id) return;
    setBusySkill(skillId);
    setError("");
    try {
      const session = await post<{ session_id: string }>("/adaptive-tutor/sessions", {
        student_id: workspace.learner.id,
        skill_id: skillId,
      });
      navigate(`/learn/${session.session_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start practice");
      setBusySkill(null);
    }
  }

  async function switchCurriculum() {
    if (!workspace?.learner.id || !catalog) return;
    setSwitching(true);
    setError("");
    try {
      await post(`/onboarding/learners/${workspace.learner.id}/curriculum`, {
        curriculum_id: catalog.curriculum_id,
      });
      await loadCatalog(workspace.learner.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not switch curriculum");
    } finally {
      setSwitching(false);
    }
  }

  const mastered = catalog
    ? catalog.strands.reduce(
        (n, s) => n + s.skills.filter((k) => k.status === "MASTERED").length,
        0,
      )
    : 0;

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        {/* Header */}
        <div className="mb-8 rounded-2xl bg-gradient-to-br from-primary to-violet-700 p-6 text-primary-foreground shadow-raised">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
                <BookOpen className="h-6 w-6" />
                {catalog ? catalog.curriculum_name : "Curriculum catalog"}
              </h1>
              <p className="mt-1 text-sm opacity-85">
                {catalog
                  ? `${catalog.jurisdiction ?? "Math"}${catalog.grade_level ? ` · Grade ${catalog.grade_level}` : ""} — pick any topic to practice`
                  : "Browse the curriculum by topic."}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {catalog && (
                <>
                  <span className="rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur">
                    {catalog.skill_count} skills
                  </span>
                  <span className="rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur">
                    {catalog.lesson_count} lessons
                  </span>
                  {catalog.is_enrolled && (
                    <span className="rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur">
                      {mastered} mastered
                    </span>
                  )}
                </>
              )}
              <Button variant="secondary" asChild>
                <Link to={`/learn/${sessionId}`}>
                  <ArrowLeft className="h-4 w-4" /> Back to practice
                </Link>
              </Button>
            </div>
          </div>

          {catalog && catalog.options.length > 1 && (
            <div className="mt-5 flex flex-wrap items-center gap-3">
              <Select
                value={catalog.curriculum_id}
                onValueChange={(v) =>
                  setParams(v === catalog.options.find((o) => o.is_enrolled)?.id ? {} : { curriculum: v })
                }
              >
                <SelectTrigger className="w-full max-w-md border-white/30 bg-white/10 text-primary-foreground backdrop-blur">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {catalog.options.map((o) => (
                    <SelectItem key={o.id} value={o.id}>
                      {o.name}
                      {o.is_enrolled ? " · current" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!catalog.is_enrolled &&
                (catalog.can_select ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={switching}
                    onClick={switchCurriculum}
                  >
                    <GraduationCap className="h-4 w-4" />
                    {switching ? "Switching…" : "Make this the curriculum"}
                  </Button>
                ) : (
                  <span className="text-xs opacity-75">
                    Ask a parent to switch to this curriculum to practice it.
                  </span>
                ))}
            </div>
          )}
        </div>

        {error && (
          <p
            className="mb-6 rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive"
            role="alert"
          >
            {error}
          </p>
        )}

        {!catalog && !error && (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3" role="status">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-40" />
            ))}
          </div>
        )}

        {catalog && catalog.strands.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-sm text-muted-foreground">
              This curriculum has no published skills yet.
            </CardContent>
          </Card>
        )}

        {/* Strand sections — IXL-style columns */}
        <div className="grid items-start gap-6 md:grid-cols-2 xl:grid-cols-3">
          {catalog?.strands.map((strand) => (
            <section key={strand.name}>
              <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">
                {strand.name}
              </h2>
              <div className="space-y-2">
                {strand.skills.map((skill) => {
                  const pct = Math.round(skill.mastery_score * 100);
                  const enrolled = catalog.is_enrolled;
                  return (
                    <Card
                      key={skill.id}
                      data-testid="catalog-skill"
                      className={cn(
                        "transition-colors",
                        enrolled && skill.status === "MASTERED"
                          ? "border-emerald-300/70 bg-emerald-50/50"
                          : "border-border bg-card",
                      )}
                    >
                      <CardContent className="flex items-center gap-3 p-3.5">
                        {enrolled ? (
                          <SkillStatus skill={skill} />
                        ) : (
                          <BookOpen className="h-4 w-4 text-muted-foreground" />
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium leading-snug">{skill.name}</p>
                          <div className="mt-1 flex items-center gap-2">
                            {enrolled && (
                              <>
                                <Progress className="h-1.5 w-16" value={pct} />
                                <span className="text-xs tabular-nums text-muted-foreground">
                                  {pct}%
                                </span>
                              </>
                            )}
                            {skill.has_lesson && (
                              <span className="text-[10px] font-semibold uppercase tracking-wide text-primary/70">
                                lesson
                              </span>
                            )}
                          </div>
                        </div>
                        {enrolled && (
                          <Button
                            size="sm"
                            variant={skill.content_ready ? "default" : "secondary"}
                            disabled={!skill.content_ready || busySkill === skill.id}
                            onClick={() => practice(skill.id)}
                          >
                            {busySkill === skill.id ? "…" : "Practice"}
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </main>
    </div>
  );
}
