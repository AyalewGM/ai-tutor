import { cn } from "@/lib/utils";

interface BrandProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZES = {
  sm: { mark: "h-7", word: "text-lg" },
  md: { mark: "h-9", word: "text-xl" },
  lg: { mark: "h-11", word: "text-2xl" },
} as const;

/** Mihur mark + wordmark — the single brand lockup used across every page. */
export default function Brand({ size = "md", className }: BrandProps) {
  const s = SIZES[size];
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <img src="/brand/mihur-mark.png" alt="" className={cn(s.mark, "w-auto")} />
      <span className={cn("brand-wordmark", s.word)}>Mihur</span>
    </span>
  );
}
