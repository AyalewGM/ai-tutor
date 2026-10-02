import { Flame, Zap } from "lucide-react";

interface SmartScoreBadgeProps {
  score: number; // 0–100, derived server-side from mastery_score
  streak: number; // correct answers in a row on the active skill
  daysStreak?: number; // consecutive days of practice — separate signal
  level?: string; // practicing | proficient | mastered — tooltip only
  skillName?: string;
}

function tierClass(score: number): string {
  // Tiers mirror the mastery boundary: 85 is the skill's mastery threshold.
  if (score >= 85) return "bg-emerald-100 text-emerald-800 border-emerald-300";
  if (score >= 50) return "bg-amber-100 text-amber-800 border-amber-300";
  return "bg-slate-100 text-slate-700 border-slate-200";
}

export default function SmartScoreBadge({
  score,
  streak,
  daysStreak,
  level,
  skillName,
}: SmartScoreBadgeProps) {
  return (
    <>
      {(daysStreak ?? 0) > 0 && (
        <span
          className="inline-flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-100 px-3.5 py-1.5 text-sm font-semibold text-amber-800"
          title="Consecutive days of practice"
        >
          <Flame className="h-4 w-4" /> {daysStreak}-day streak
        </span>
      )}
      {streak > 1 && (
        <span
          className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-100 px-3.5 py-1.5 text-sm font-semibold text-emerald-800"
          title="Correct answers in a row on this skill"
        >
          <Zap className="h-4 w-4" /> {streak} in a row
        </span>
      )}
      <span
        className={`inline-flex items-center rounded-full border px-3.5 py-1.5 text-sm font-semibold ${tierClass(score)}`}
        title={`SmartScore — ${level ?? "practicing"} on ${skillName ?? "this skill"}`}
      >
        SmartScore {score}
      </span>
    </>
  );
}
