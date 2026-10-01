import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, CircleDashed, MapPin, PlayCircle } from "lucide-react";
import { ApiError, api } from "../api";
import NavBar from "../components/NavBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { SkillMapEntry } from "../types";

function tier(entry: SkillMapEntry): "mastered" | "learning" | "locked" {
  if (entry.status === "MASTERED") return "mastered";
  if (entry.mastery_score > 0 || entry.status !== "NOT_STARTED")
    return "learning";
  return "locked";
}

const TIER_LABEL = {
  mastered: "Mastered",
  learning: "In progress",
  locked: "Not started",
} as const;

const TIER_STYLE = {
  mastered: "border-emerald-300/70 bg-emerald-50/50",
  learning: "border-primary/40 bg-primary/5",
  locked: "border-border",
} as const;

const TIER_ICON = {
  mastered: <CheckCircle2 className="h-4 w-4 text-emerald-600" />,
  learning: <PlayCircle className="h-4 w-4 text-primary" />,
  locked: <CircleDashed className="h-4 w-4 text-muted-foreground" />,
} as const;

export default function SkillMap() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [entries, setEntries] = useState<SkillMapEntry[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<SkillMapEntry[]>(`/learner-workspace/sessions/${sessionId}/skill-map`)
      .then(setEntries)
      .catch((err) =>
        setError(
          err instanceof ApiError ? err.message : "Could not load skill map",
        ),
      );
  }, [sessionId]);

  const mastered = entries?.filter((e) => e.status === "MASTERED").length ?? 0;

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-8 rounded-2xl bg-gradient-to-br from-primary to-violet-700 p-6 text-primary-foreground shadow-raised">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Skill map</h1>
              <p className="mt-1 text-sm opacity-85">
                Your path through the curriculum — mastered skills stay sharp
                through review.
              </p>
            </div>
            <div className="flex items-center gap-3">
              {entries && (
                <span className="rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur">
                  {mastered} / {entries.length} mastered
                </span>
              )}
              <Button variant="secondary" asChild>
                <Link to={`/learn/${sessionId}`}>
                  <ArrowLeft className="h-4 w-4" /> Back to practice
                </Link>
              </Button>
            </div>
          </div>
          {entries && (
            <Progress
              className="mt-4 h-2 bg-white/20"
              value={entries.length ? (100 * mastered) / entries.length : 0}
            />
          )}
        </div>

        {error && (
          <p
            className="rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive"
            role="alert"
          >
            {error}
          </p>
        )}

        {!entries && !error && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" role="status">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {entries?.map((entry) => {
            const pct = Math.round(entry.mastery_score * 100);
            const level = tier(entry);
            return (
              <Card
                key={entry.skill_id}
                className={cn(
                  TIER_STYLE[level],
                  entry.is_active && "ring-2 ring-primary",
                )}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {entry.code}
                    </span>
                    {entry.is_active ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
                        <MapPin className="h-3.5 w-3.5" /> You are here
                      </span>
                    ) : (
                      TIER_ICON[level]
                    )}
                  </div>
                  <p className="mt-1.5 font-medium leading-snug">{entry.name}</p>
                  <div className="mt-3 flex items-center gap-2">
                    <Progress className="h-1.5 flex-1" value={pct} />
                    <span className="text-xs font-medium tabular-nums text-muted-foreground">
                      {pct}%
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs text-muted-foreground">
                    {TIER_LABEL[level]}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </main>
    </div>
  );
}
