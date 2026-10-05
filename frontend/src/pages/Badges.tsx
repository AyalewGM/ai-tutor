import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Lock } from "lucide-react";
import { ApiError, api } from "../api";
import NavBar from "../components/NavBar";
import LevelCrest from "../components/LevelCrest";
import { Badge as UiBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { Badge, LearnerWorkspace } from "../types";

function BadgeMedal({ earned }: { earned: boolean }) {
  return (
    <svg
      viewBox="0 0 64 64"
      width="56"
      height="56"
      aria-hidden="true"
      className={cn(!earned && "opacity-40 grayscale")}
    >
      <circle cx="32" cy="26" r="20" fill={earned ? "#f59e0b" : "#d1d5db"} />
      <circle cx="32" cy="26" r="15" fill={earned ? "#fff8e6" : "#f3f4f6"} />
      <path
        d="M32 16l3 6.5 7 .8-5.2 4.7 1.4 7-6.2-3.6-6.2 3.6 1.4-7-5.2-4.7 7-.8z"
        fill={earned ? "#d97706" : "#9ca3af"}
      />
      <path
        d="M24 44l-4 14 12-6 12 6-4-14"
        fill={earned ? "#6d28d9" : "#e5e7eb"}
      />
    </svg>
  );
}

export default function Badges() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [badges, setBadges] = useState<Badge[] | null>(null);
  const [growth, setGrowth] = useState<LearnerWorkspace["growth"]>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Badge[]>(`/learner-workspace/sessions/${sessionId}/badges`)
      .then(setBadges)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load badges"),
      );
    api<LearnerWorkspace>(`/learner-workspace/sessions/${sessionId}`)
      .then((ws) => setGrowth(ws.growth ?? null))
      .catch(() => {});
  }, [sessionId]);

  const earnedCount = badges?.filter((b) => b.earned).length ?? 0;

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-8 rounded-2xl bg-gradient-to-br from-primary to-violet-700 p-6 text-primary-foreground shadow-raised">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Badge collection</h1>
              <p className="mt-1 text-sm opacity-85">
                Badges are earned by real learning — correct answers, mastered
                skills, and fixed gaps.
              </p>
            </div>
            <div className="flex items-center gap-3">
              {growth && (
                <span
                  className="inline-flex items-center gap-2 rounded-full bg-amber-400/90 py-1 pl-1 pr-3.5 text-sm font-semibold text-amber-950"
                  title={`${growth.xp_in_level}/${growth.xp_for_next} XP to next level`}
                >
                  <LevelCrest level={growth.level} title={growth.level_title} size="sm" />
                  Lv {growth.level} · {growth.level_title} · {growth.xp} XP
                  {(growth.xp_today ?? 0) > 0 && ` (+${growth.xp_today} today)`}
                </span>
              )}
              {badges && (
                <span className="rounded-full bg-white/15 px-3.5 py-1.5 text-sm font-semibold backdrop-blur">
                  {earnedCount} / {badges.length} earned
                </span>
              )}
              <Button variant="secondary" asChild>
                <Link to={`/learn/${sessionId}`}>
                  <ArrowLeft className="h-4 w-4" /> Back to practice
                </Link>
              </Button>
            </div>
          </div>
          {badges && (
            <Progress
              className="mt-4 h-2 bg-white/20"
              value={badges.length ? (100 * earnedCount) / badges.length : 0}
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

        {!badges && !error && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" role="status">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-44" />
            ))}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {badges?.map((badge) => (
            <Card
              key={badge.code}
              data-testid="badge-card"
              data-earned={badge.earned}
              className={cn(
                "transition-shadow",
                badge.earned ? "border-amber-300/60" : "opacity-90",
              )}
            >
              <CardContent className="flex items-start gap-4 p-5">
                <BadgeMedal earned={badge.earned} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{badge.name}</h3>
                    {badge.earned ? (
                      badge.times_earned > 1 && (
                        <UiBadge variant="secondary">×{badge.times_earned}</UiBadge>
                      )
                    ) : (
                      <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                    )}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {badge.description}
                  </p>
                  {badge.earned && badge.skill_names.length > 0 && (
                    <p className="mt-2 text-xs font-medium text-primary">
                      {badge.skill_names.join(", ")}
                    </p>
                  )}
                  {!badge.earned && badge.progress && (
                    <div className="mt-3 space-y-1">
                      <Progress
                        className="h-1.5"
                        value={
                          (100 * badge.progress.current) / badge.progress.target
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        {badge.progress.current} / {badge.progress.target}{" "}
                        {badge.progress.unit}
                      </p>
                    </div>
                  )}
                  {!badge.earned && !badge.progress && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Not yet earned
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
