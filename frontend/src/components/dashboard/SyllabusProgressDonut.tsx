import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { SyllabusStatus } from "./ParentProgressDashboard";

interface SyllabusProgressDonutProps {
  data: SyllabusStatus[];
}

const statusStyles: Record<SyllabusStatus["status"], { color: string; dot: string }> = {
  Mastered: { color: "#059669", dot: "bg-emerald-600" },
  "In Progress": { color: "#d97706", dot: "bg-amber-600" },
  "Not Started": { color: "#94a3b8", dot: "bg-slate-400" },
};

export default function SyllabusProgressDonut({ data }: SyllabusProgressDonutProps) {
  const total = data.reduce((sum, item) => sum + item.count, 0);
  const mastered = data.find((item) => item.status === "Mastered")?.count ?? 0;
  const percent = total ? Math.round((mastered / total) * 100) : 0;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
      <div>
        <h2 className="text-base font-semibold text-slate-950">Syllabus progress</h2>
        <p className="mt-1 text-sm text-slate-500">
          Where current curriculum topics stand.
        </p>
      </div>
      <div className="relative mx-auto mt-3 h-56 max-w-xs">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="status"
              cx="50%"
              cy="50%"
              innerRadius={66}
              outerRadius={88}
              paddingAngle={3}
              stroke="none"
            >
              {data.map((item) => (
                <Cell key={item.status} fill={statusStyles[item.status].color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [`${value} topics`, "Topics"]}
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 8px 24px rgba(15,23,42,.08)",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-content-center text-center">
          <strong className="text-3xl font-bold text-slate-950">{percent}%</strong>
          <span className="text-xs font-medium text-slate-500">mastered</span>
        </div>
      </div>
      <div className="mt-2 space-y-2">
        {data.map((item) => (
          <div key={item.status} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className={`h-2.5 w-2.5 rounded-full ${statusStyles[item.status].dot}`} />
              {item.status}
            </span>
            <strong className="text-slate-900">{item.count}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
