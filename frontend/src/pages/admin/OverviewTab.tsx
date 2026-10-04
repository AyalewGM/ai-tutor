import { useEffect, useState } from "react";
import { Users, UserCheck, LineChart, UserPlus } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ApiError } from "../../api";
import StatCard from "../../components/dashboard/StatCard";
import type { Conversion, MetricsOverview } from "./types";

function fmt(n: number): string {
  return n.toLocaleString("en-US");
}

export default function OverviewTab() {
  const [data, setData] = useState<MetricsOverview | null>(null);
  const [conv, setConv] = useState<Conversion | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<MetricsOverview>("/admin/metrics/overview")
      .then(setData)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load metrics"),
      );
    api<Conversion>("/admin/metrics/conversion").then(setConv).catch(() => {});
  }, []);

  if (error) {
    return (
      <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
        {error}
      </p>
    );
  }
  if (!data) {
    return <p className="py-12 text-center text-sm text-slate-500">Loading metrics…</p>;
  }

  const chartData = data.signups_daily.map((d) => ({
    label: d.date.slice(5), // MM-DD
    count: d.count,
  }));

  const rows: [string, { "1d": number; "7d": number; "30d": number }][] = [
    ["Active learners", data.active_learners],
    ["Active families", data.active_families],
    ["Attempts", data.attempts],
    ["Tutor sessions", data.tutor_sessions],
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Active learners today"
          value={fmt(data.active_learners["1d"])}
          helper={`${fmt(data.active_learners["7d"])} weekly · ${fmt(data.active_learners["30d"])} monthly`}
          icon={<UserCheck size={20} />}
          accent="emerald"
        />
        <StatCard
          label="Active families today"
          value={fmt(data.active_families["1d"])}
          helper={`${fmt(data.active_families["7d"])} weekly · ${fmt(data.active_families["30d"])} monthly`}
          icon={<Users size={20} />}
          accent="indigo"
        />
        <StatCard
          label="Sign-ups (30d)"
          value={fmt(data.signups["30d"])}
          helper={`${fmt(data.signups.total)} families total · ${fmt(data.learners_total)} learners`}
          icon={<UserPlus size={20} />}
          accent="amber"
        />
        <StatCard
          label="Attempts (30d)"
          value={fmt(data.attempts["30d"])}
          helper={`${fmt(data.tutor_sessions["30d"])} tutor sessions`}
          icon={<LineChart size={20} />}
          accent="slate"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
          <h2 className="text-base font-semibold text-slate-950">Daily sign-ups</h2>
          <p className="mt-1 text-sm text-slate-500">New family registrations, last 30 days.</p>
          <div className="mt-4 h-64 w-full" aria-label="Daily sign-ups over the last 30 days">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: -24 }}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  allowDecimals={false}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                />
                <Tooltip
                  cursor={{ fill: "#f8fafc" }}
                  contentStyle={{
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 8px 24px rgba(15,23,42,.08)",
                  }}
                  formatter={(value: number) => [`${value}`, "Sign-ups"]}
                />
                <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} maxBarSize={18} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
          <h2 className="text-base font-semibold text-slate-950">Activity windows</h2>
          <p className="mt-1 text-sm text-slate-500">
            Distinct users with a graded attempt.
          </p>
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                <th className="pb-2 font-medium"></th>
                <th className="pb-2 text-right font-medium">1d</th>
                <th className="pb-2 text-right font-medium">7d</th>
                <th className="pb-2 text-right font-medium">30d</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map(([label, counts]) => (
                <tr key={label}>
                  <td className="py-2.5 font-medium text-slate-700">{label}</td>
                  <td className="py-2.5 text-right tabular-nums text-slate-900">{fmt(counts["1d"])}</td>
                  <td className="py-2.5 text-right tabular-nums text-slate-900">{fmt(counts["7d"])}</td>
                  <td className="py-2.5 text-right tabular-nums text-slate-900">{fmt(counts["30d"])}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-xs leading-5 text-slate-400">
            As of {new Date(data.as_of).toLocaleString("en-US", { timeZoneName: "short" })}
          </p>
        </section>
      </div>

      {conv && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
          <h2 className="text-base font-semibold text-slate-950">Plans &amp; conversion</h2>
          <p className="mt-1 text-sm text-slate-500">
            {fmt(conv.paid_families)} of {fmt(conv.families_total)} families on a paid plan
            ({conv.paid_share_pct}%) · {fmt(conv.trialing_now)} trialing now.
          </p>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="pb-2 font-medium">Plan</th>
                  <th className="pb-2 text-right font-medium">Families</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {conv.plan_breakdown.map((row) => (
                  <tr key={row.tier}>
                    <td className="py-2 font-medium text-slate-700">{row.tier}</td>
                    <td className="py-2 text-right tabular-nums text-slate-900">{fmt(row.families)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="pb-2 font-medium">Stripe funnel</th>
                  <th className="pb-2 text-right font-medium">30d</th>
                  <th className="pb-2 text-right font-medium">All time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {([
                  ["Trials started", conv.funnel.trials_started],
                  ["Activations", conv.funnel.activations],
                  ["Cancellations", conv.funnel.cancellations],
                ] as const).map(([label, counts]) => (
                  <tr key={label}>
                    <td className="py-2 font-medium text-slate-700">{label}</td>
                    <td className="py-2 text-right tabular-nums text-slate-900">{fmt(counts["30d"])}</td>
                    <td className="py-2 text-right tabular-nums text-slate-900">{fmt(counts["total"])}</td>
                  </tr>
                ))}
                <tr>
                  <td className="py-2 font-medium text-slate-700">Trial → paid</td>
                  <td className="py-2 text-right tabular-nums text-slate-900" colSpan={2}>
                    {conv.trial_to_paid_pct === null ? "—" : `${conv.trial_to_paid_pct}%`}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
