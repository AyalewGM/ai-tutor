import { useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import { Progress } from "@/components/ui/progress";
import type { AiUsageSummary } from "./types";

function usd(value: string): string {
  return `$${Number(value).toFixed(4)}`;
}

export default function AiUsageTab() {
  const [data, setData] = useState<AiUsageSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<AiUsageSummary>("/admin/ai-usage/summary")
      .then(setData)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load AI usage"),
      );
  }, []);

  if (error) {
    return (
      <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
        {error}
      </p>
    );
  }
  if (!data) {
    return <p className="py-12 text-center text-sm text-slate-500">Loading usage…</p>;
  }

  const spend = Number(data.spend_usd);
  const cap = Number(data.cap_usd);
  const pct = cap > 0 ? Math.min(100, (spend / cap) * 100) : 0;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-950">
              AI usage · {data.month}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Month-to-date estimated spend against the global cap.
            </p>
          </div>
          <div className="text-right text-sm">
            <p className="font-semibold text-slate-900">
              {usd(data.spend_usd)} <span className="font-normal text-slate-400">/ ${cap.toFixed(2)}</span>
            </p>
            <p className="text-xs text-slate-500">
              {data.generations.toLocaleString()} generations · {data.denied.toLocaleString()} denied
            </p>
          </div>
        </div>
        <Progress value={pct} className="mt-4 h-2.5" />
        <p className="mt-2 text-xs text-slate-400">
          {pct.toFixed(1)}% of the monthly budget. AI switches to built-in tutor
          messages when the cap is reached.
        </p>
      </section>

      <section className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-dashboard">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="px-4 py-3 font-medium">Family</th>
              <th className="px-4 py-3 text-right font-medium">Generations</th>
              <th className="px-4 py-3 text-right font-medium">Denied</th>
              <th className="px-4 py-3 text-right font-medium">Est. spend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.families.map((f, i) => (
              <tr key={f.family_user_id ?? `unknown-${i}`}>
                <td className="px-4 py-3 font-mono text-xs text-slate-700">
                  {f.family_user_id ?? "Unattributed"}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">{f.generations.toLocaleString()}</td>
                <td className="px-4 py-3 text-right tabular-nums">{f.denied.toLocaleString()}</td>
                <td className="px-4 py-3 text-right tabular-nums font-medium text-slate-900">
                  {usd(f.spend_usd)}
                </td>
              </tr>
            ))}
            {data.families.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-slate-400">
                  No AI usage this month.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
