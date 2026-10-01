import { useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown } from "lucide-react";
import type { MisconceptionItem } from "./ParentProgressDashboard";

interface MisconceptionListProps {
  items: MisconceptionItem[];
}

export default function MisconceptionList({ items }: MisconceptionListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(items[0]?.id ?? null);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-dashboard">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-950">Learning hurdles &amp; next steps</h2>
          <p className="mt-1 text-sm text-slate-500">
            Parent-friendly patterns detected from tutoring evidence—not raw student conversations.
          </p>
        </div>
        <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
          {items.filter((item) => item.status === "Needs Review").length} active
        </span>
      </div>

      {items.length === 0 ? (
        <div className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">
          No active misconceptions are currently flagged.
        </div>
      ) : (
        <div className="mt-5 divide-y divide-slate-100">
          {items.map((item) => {
            const expanded = expandedId === item.id;
            const resolved = item.status === "Resolved";
            return (
              <article key={item.id} className="py-4 first:pt-0 last:pb-0">
                <button
                  type="button"
                  className="flex min-h-0 w-full items-start justify-between gap-4 bg-transparent p-0 text-left"
                  aria-expanded={expanded}
                  onClick={() => setExpandedId(expanded ? null : item.id)}
                >
                  <span className="flex min-w-0 gap-3">
                    <span
                      className={`mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg ${
                        resolved
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-amber-50 text-amber-700"
                      }`}
                      aria-hidden="true"
                    >
                      {resolved ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                    </span>
                    <span className="min-w-0">
                      <strong className="block text-sm text-slate-950">{item.topicName}</strong>
                      <span className="mt-1 block text-sm leading-5 text-slate-600">
                        {item.misconception}
                      </span>
                      <span className="mt-2 block text-xs text-slate-400">
                        Flagged {new Date(item.flaggedAt).toLocaleDateString()}
                      </span>
                    </span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <span
                      className={`hidden rounded-full px-2.5 py-1 text-xs font-semibold sm:inline ${
                        resolved
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-amber-50 text-amber-700"
                      }`}
                    >
                      {item.status}
                    </span>
                    <ChevronDown
                      size={18}
                      className={`text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
                    />
                  </span>
                </button>
                {expanded && (
                  <div className="ml-12 mt-3 rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                      Suggested parent support
                    </p>
                    <p className="mt-1 text-sm leading-6 text-slate-700">{item.suggestion}</p>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
