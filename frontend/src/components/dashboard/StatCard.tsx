import type { ReactNode } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";

export type StatAccent = "indigo" | "emerald" | "amber" | "slate";

interface StatCardProps {
  label: string;
  value: string;
  helper: string;
  icon: ReactNode;
  trend?: number | null;
  accent?: StatAccent;
}

const accentClasses: Record<StatAccent, string> = {
  indigo: "bg-indigo-50 text-indigo-700 ring-indigo-100",
  emerald: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  amber: "bg-amber-50 text-amber-700 ring-amber-100",
  slate: "bg-slate-100 text-slate-700 ring-slate-200",
};

export default function StatCard({
  label,
  value,
  helper,
  icon,
  trend = null,
  accent = "indigo",
}: StatCardProps) {
  const trendIsPositive = trend !== null && trend >= 0;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
      <div className="flex items-start justify-between gap-4">
        <div
          className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ring-1 ${accentClasses[accent]}`}
          aria-hidden="true"
        >
          {icon}
        </div>
        {trend !== null && (
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
              trendIsPositive
                ? "bg-emerald-50 text-emerald-700"
                : "bg-rose-50 text-rose-700"
            }`}
          >
            {trendIsPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {trendIsPositive ? "+" : ""}
            {trend}% vs last week
          </span>
        )}
      </div>
      <p className="mt-5 text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-slate-950">{value}</p>
      <p className="mt-1 text-xs leading-5 text-slate-500">{helper}</p>
    </article>
  );
}
