import { useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import type { CurriculumActivity, RegionActivity } from "./types";

function fmt(n: number): string {
  return n.toLocaleString("en-US");
}

export default function ActivityTab() {
  const [regions, setRegions] = useState<RegionActivity[] | null>(null);
  const [curricula, setCurricula] = useState<CurriculumActivity[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<RegionActivity[]>("/admin/metrics/by-region"),
      api<CurriculumActivity[]>("/admin/metrics/by-curriculum"),
    ])
      .then(([r, c]) => {
        setRegions(r);
        setCurricula(c);
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load activity"),
      );
  }, []);

  if (error) {
    return (
      <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
        {error}
      </p>
    );
  }
  if (!regions || !curricula) {
    return <p className="py-12 text-center text-sm text-slate-500">Loading activity…</p>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
        <h2 className="text-base font-semibold text-slate-950">Activity by state / province</h2>
        <p className="mt-1 text-sm text-slate-500">
          Family saved region, 30-day learning activity. UNSET = families without a saved region.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
                <th className="pb-2 font-medium">Region</th>
                <th className="pb-2 text-right font-medium">Families</th>
                <th className="pb-2 text-right font-medium">Active learners</th>
                <th className="pb-2 text-right font-medium">Attempts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {regions.map((r) => (
                <tr key={`${r.country_code}/${r.region_code}`}>
                  <td className="py-2.5 font-medium text-slate-800">
                    {r.country_code} · {r.region_code}
                  </td>
                  <td className="py-2.5 text-right tabular-nums">{fmt(r.families)}</td>
                  <td className="py-2.5 text-right tabular-nums">{fmt(r.active_learners)}</td>
                  <td className="py-2.5 text-right tabular-nums">{fmt(r.attempts)}</td>
                </tr>
              ))}
              {regions.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-400">
                    No families yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
        <h2 className="text-base font-semibold text-slate-950">Activity by curriculum</h2>
        <p className="mt-1 text-sm text-slate-500">
          Curriculum practiced in sessions, 30-day window.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
                <th className="pb-2 font-medium">Curriculum</th>
                <th className="pb-2 text-right font-medium">Enrolled learners</th>
                <th className="pb-2 text-right font-medium">Active learners</th>
                <th className="pb-2 text-right font-medium">Attempts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {curricula.map((c) => (
                <tr key={c.code}>
                  <td className="py-2.5">
                    <span className="font-medium text-slate-800">{c.code}</span>
                    <span className="ml-2 text-xs text-slate-400">{c.name}</span>
                  </td>
                  <td className="py-2.5 text-right tabular-nums">{fmt(c.learners_total)}</td>
                  <td className="py-2.5 text-right tabular-nums">{fmt(c.active_learners)}</td>
                  <td className="py-2.5 text-right tabular-nums">{fmt(c.attempts)}</td>
                </tr>
              ))}
              {curricula.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-400">
                    No curriculum activity yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
