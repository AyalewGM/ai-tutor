import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DailyMetric } from "./ParentProgressDashboard";

interface ActivityChartProps {
  data: DailyMetric[];
}

export default function ActivityChart({ data }: ActivityChartProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
      <div className="mb-5">
        <h2 className="text-base font-semibold text-slate-950">Mastery &amp; study activity</h2>
        <p className="mt-1 text-sm text-slate-500">
          Daily learning time compared with demonstrated mastery.
        </p>
      </div>
      <div className="h-80 w-full" aria-label="Study minutes and mastery over time">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: -12 }}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#64748b", fontSize: 12 }}
            />
            <YAxis
              yAxisId="minutes"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#64748b", fontSize: 12 }}
              width={44}
              label={{
                value: "Minutes",
                angle: -90,
                position: "insideLeft",
                fill: "#64748b",
                fontSize: 11,
              }}
            />
            <YAxis
              yAxisId="mastery"
              orientation="right"
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#64748b", fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
              width={44}
            />
            <Tooltip
              cursor={{ fill: "#f8fafc" }}
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 8px 24px rgba(15,23,42,.08)",
              }}
              formatter={(value: number, name: string) => [
                name === "Mastery Score (%)" ? `${value}%` : `${value} min`,
                name,
              ]}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }} />
            <Bar
              yAxisId="minutes"
              dataKey="minutes"
              name="Daily Study Time (mins)"
              fill="#818cf8"
              radius={[6, 6, 0, 0]}
              maxBarSize={34}
            />
            <Line
              yAxisId="mastery"
              type="monotone"
              dataKey="masteryScore"
              name="Mastery Score (%)"
              stroke="#059669"
              strokeWidth={3}
              dot={{ r: 3, fill: "#059669", strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
