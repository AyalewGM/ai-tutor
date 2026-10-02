import { useState } from "react";
import { CheckCircle2, ChevronDown, Lightbulb, XCircle } from "lucide-react";
import type { StepTrail } from "../../types";
import MathText from "../MathText";

interface StepTrailsProps {
  trails: StepTrail[];
}

const STATUS_STYLE: Record<string, { label: string; className: string }> = {
  SOLVED: {
    label: "Worked through",
    className: "bg-emerald-50 text-emerald-700",
  },
  STRUGGLED: {
    label: "Needed support",
    className: "bg-amber-50 text-amber-700",
  },
  IN_PROGRESS: {
    label: "In progress",
    className: "bg-slate-100 text-slate-600",
  },
};

export default function StepTrails({ trails }: StepTrailsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(trails[0]?.problem_id ?? null);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-950">Recent written work</h2>
          <p className="mt-1 text-sm text-slate-500">
            Step-by-step lines your learner wrote — the math itself, not chat messages.
          </p>
        </div>
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
          {trails.length} {trails.length === 1 ? "problem" : "problems"}
        </span>
      </div>

      {trails.length === 0 ? (
        <div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
          No line-by-line work recorded yet. It appears here when your learner uses the
          step-by-step mode on supported problems.
        </div>
      ) : (
        <div className="mt-5 divide-y divide-slate-100">
          {trails.map((trail) => {
            const expanded = expandedId === trail.problem_id;
            const status = STATUS_STYLE[trail.status] ?? STATUS_STYLE.IN_PROGRESS;
            return (
              <article key={trail.problem_id} className="py-4 first:pt-0 last:pb-0">
                <button
                  type="button"
                  className="flex min-h-0 w-full items-start justify-between gap-4 bg-transparent p-0 text-left"
                  aria-expanded={expanded}
                  onClick={() => setExpandedId(expanded ? null : trail.problem_id)}
                >
                  <span className="min-w-0">
                    <span className="block text-sm font-medium text-slate-950">
                      <MathText text={trail.prompt} />
                    </span>
                    <span className="mt-1 block text-xs text-slate-500">
                      {trail.skill_name} · {new Date(trail.updated_at).toLocaleDateString()}
                    </span>
                    {trail.misconception_names.length > 0 && (
                      <span className="mt-1 block text-xs text-amber-700">
                        {trail.misconception_names.join(" · ")}
                      </span>
                    )}
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <span
                      className={`hidden rounded-full px-2.5 py-1 text-xs font-semibold sm:inline ${status.className}`}
                    >
                      {status.label}
                    </span>
                    <ChevronDown
                      size={18}
                      className={`text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
                    />
                  </span>
                </button>
                {expanded && (
                  <ol className="mt-3 space-y-1.5">
                    {trail.lines.map((line, index) => {
                      const ok = line.status === "valid" || line.status === "solved";
                      return (
                        <li
                          key={index}
                          className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                            ok
                              ? "border-emerald-100 bg-emerald-50/60"
                              : "border-rose-100 bg-rose-50/60"
                          }`}
                        >
                          {ok ? (
                            <CheckCircle2
                              size={15}
                              className="shrink-0 text-emerald-600"
                              aria-label="accepted step"
                            />
                          ) : (
                            <XCircle
                              size={15}
                              className="shrink-0 text-rose-500"
                              aria-label="rejected step"
                            />
                          )}
                          <MathText text={line.line} />
                          {line.revealed && (
                            <span className="ml-auto inline-flex items-center gap-1 text-[11px] font-medium text-indigo-600">
                              <Lightbulb size={12} />
                              hint revealed after
                            </span>
                          )}
                        </li>
                      );
                    })}
                  </ol>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
