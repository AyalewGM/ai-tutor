import { Fragment, useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import { Button } from "@/components/ui/button";
import type { AuditEvent } from "./types";

export default function AuditTab() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [cursor, setCursor] = useState<string | null>(null);

  const load = useCallback(async (before: string | null, append: boolean) => {
    setLoading(true);
    setError("");
    try {
      const query = before ? `?limit=50&before=${encodeURIComponent(before)}` : "?limit=50";
      const batch = await api<AuditEvent[]>(`/admin/audit-log${query}`);
      setEvents((prev) => (append ? [...prev, ...batch] : batch));
      setCursor(batch.length === 50 ? batch[batch.length - 1].created_at : null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load audit log");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(null, false);
  }, [load]);

  return (
    <div className="space-y-4">
      <h2 className="text-base font-semibold text-slate-950">Audit log</h2>
      <p className="-mt-2 text-sm text-slate-500">
        Every state-changing staff action, newest first.
      </p>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-dashboard">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="px-4 py-3 font-medium">When</th>
              <th className="px-4 py-3 font-medium">Actor</th>
              <th className="px-4 py-3 font-medium">Action</th>
              <th className="px-4 py-3 font-medium">Target</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {events.map((e) => {
              const hasDiff = e.before !== null || e.after !== null;
              return (
                <Fragment key={e.id}>
                  <tr>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                      {new Date(e.created_at).toLocaleString("en-US")}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800">{e.actor_label}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">{e.action}</td>
                    <td className="max-w-56 truncate px-4 py-3 text-xs text-slate-500" title={e.target_id ?? ""}>
                      {e.target_type ? `${e.target_type} · ${e.target_id ?? ""}` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {hasDiff && (
                        <button
                          className="text-xs font-medium text-primary hover:underline"
                          onClick={() => setExpanded(expanded === e.id ? null : e.id)}
                        >
                          {expanded === e.id ? "Hide" : "Details"}
                        </button>
                      )}
                    </td>
                  </tr>
                  {expanded === e.id && hasDiff && (
                    <tr>
                      <td colSpan={5} className="bg-slate-50 px-4 py-3">
                        <div className="grid gap-3 sm:grid-cols-2">
                          {(["before", "after"] as const).map((side) => (
                            <div key={side}>
                              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                                {side}
                              </p>
                              <pre className="max-h-48 overflow-auto rounded-lg bg-white p-3 text-xs text-slate-700 ring-1 ring-slate-200">
                                {e[side] ? JSON.stringify(e[side], null, 2) : "—"}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            {!loading && events.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-slate-400">
                  No audited actions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {cursor && (
        <div className="text-center">
          <Button variant="secondary" size="sm" disabled={loading} onClick={() => load(cursor, true)}>
            {loading ? "Loading…" : "Load older events"}
          </Button>
        </div>
      )}
    </div>
  );
}
