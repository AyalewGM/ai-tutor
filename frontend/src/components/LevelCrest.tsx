import { Award, Compass, Crown, Puzzle, Sprout, Star, Trophy, Brain } from "lucide-react";
import { cn } from "@/lib/utils";

const CREST_TIERS = [
  { min: 1, icon: Sprout, ring: "border-emerald-300", bg: "bg-emerald-100", text: "text-emerald-700" },
  { min: 2, icon: Compass, ring: "border-teal-300", bg: "bg-teal-100", text: "text-teal-700" },
  { min: 3, icon: Puzzle, ring: "border-sky-300", bg: "bg-sky-100", text: "text-sky-700" },
  { min: 4, icon: Brain, ring: "border-indigo-300", bg: "bg-indigo-100", text: "text-indigo-700" },
  { min: 5, icon: Star, ring: "border-violet-300", bg: "bg-violet-100", text: "text-violet-700" },
  { min: 6, icon: Trophy, ring: "border-amber-300", bg: "bg-amber-100", text: "text-amber-700" },
  { min: 7, icon: Award, ring: "border-orange-300", bg: "bg-orange-100", text: "text-orange-700" },
  { min: 8, icon: Crown, ring: "border-yellow-400", bg: "bg-yellow-100", text: "text-yellow-700" },
] as const;

export default function LevelCrest({
  level,
  title,
  size = "md",
}: {
  level: number;
  title?: string;
  size?: "sm" | "md" | "lg";
}) {
  const tier =
    [...CREST_TIERS].reverse().find((t) => level >= t.min) ?? CREST_TIERS[0];
  const Icon = tier.icon;
  const dim =
    size === "lg"
      ? "h-14 w-14 text-2xl"
      : size === "sm"
        ? "h-8 w-8"
        : "h-10 w-10";
  const iconSize = size === "lg" ? "h-7 w-7" : size === "sm" ? "h-4 w-4" : "h-5 w-5";
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full border-2",
        tier.ring,
        tier.bg,
        tier.text,
        dim,
      )}
      role="img"
      aria-label={title ? `Level ${level} ${title}` : `Level ${level}`}
      title={title ? `Level ${level} · ${title}` : `Level ${level}`}
    >
      <Icon className={iconSize} />
    </span>
  );
}
