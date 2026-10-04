import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen, CheckCircle2, CircleDashed, MapPin, PlayCircle } from "lucide-react";
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

const NODE_STYLE = {
  mastered: "border-emerald-400 bg-emerald-500 text-white",
  learning: "border-primary bg-primary text-primary-foreground",
  locked: "border-border bg-card text-muted-foreground",
} as const;

const ZONES = [
  "Trailhead",
  "Forest Path",
  "River Crossing",
  "Hill Climb",
  "Summit Ridge",
] as const;

function zoneFor(difficultyLevel: number): string {
  const index = Math.min(Math.max(difficultyLevel - 1, 0), ZONES.length - 1);
  return ZONES[index];
}

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
                <Link to={`/learn/${sessionId}/catalog`}>
                  <BookOpen className="h-4 w-4" /> Catalog
                </Link>
              </Button>
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
          <div className="space-y-6" role="status">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        )}

        {/* Journey path — a spine with alternating stops */}
        <div className="relative">
          <div
            className="absolute bottom-4 left-5 top-4 w-0.5 rounded-full bg-border sm:left-1/2 sm:-translate-x-1/2"
            aria-hidden="true"
          />
          <ol className="relative space-y-6">
            {entries?.flatMap((entry, index) => {
              const pct = Math.round(entry.mastery_score * 100);
              const level = tier(entry);
              const left = index % 2 === 0;
              const zone = zoneFor(entry.difficulty_level);
              const rows = [];
              if (index === 0 || zoneFor(entries[index - 1].difficulty_level) !== zone) {
                rows.push(
                  <li key={`zone-${zone}`} className="relative flex justify-start pl-12 sm:justify-center sm:pl-0" aria-hidden="true">
                    <span className="z-10 rounded-full border border-primary/30 bg-card px-3 py-1 text-[11px] font-bold uppercase tracking-widest text-primary shadow-sm">
                      {zone}
                    </span>
                  </li>,
                );
              }
              rows.push(
                <li
                  key={entry.skill_id}
                  className={cn(
                    "relative flex",
                    left ? "sm:justify-start" : "sm:justify-end",
                  )}
                >
                  {/* stop on the spine */}
                  <span
                    className={cn(
                      "absolute left-5 top-5 z-10 flex h-7 w-7 -translate-x-1/2 items-center justify-center rounded-full border-2 sm:left-1/2",
                      NODE_STYLE[level],
                    )}
                    aria-hidden="true"
                  >
                    {level === "mastered" && (
                      <CheckCircle2 className="h-4 w-4" />
                    )}
                    {entry.is_active && level !== "mastered" && (
                      <MapPin className="h-4 w-4" />
                    )}
                    {entry.is_active && (
                      <span className="absolute inset-0 -z-10 animate-ping rounded-full bg-primary/40" />
                    )}
                  </span>

                  <Card
                    data-testid="map-tile"
                    data-active={entry.is_active}
                    className={cn(
                      "ml-12 w-full sm:ml-0 sm:w-[calc(50%-2.5rem)]",
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
                </li>,
              );
              return rows;
            })}
          </ol>
        </div>
      </main>
    </div>
  );
}
