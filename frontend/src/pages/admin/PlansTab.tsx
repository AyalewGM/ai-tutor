import { useCallback, useEffect, useState } from "react";
import { api, ApiError, patch, post } from "../../api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { AdminPlan, PlansAdmin } from "./types";

type Draft = {
  name: string;
  monthly_price_usd: string;
  monthly_price_cad: string;
  max_students: string;
  ai_daily_generations: string;
};

function draftOf(plan: AdminPlan): Draft {
  return {
    name: plan.name,
    monthly_price_usd: plan.monthly_price_usd,
    monthly_price_cad: String(plan.monthly_price_cad),
    max_students: String(plan.max_students),
    ai_daily_generations: String(plan.ai_daily_generations),
  };
}

export default function PlansTab({ canManage }: { canManage: boolean }) {
  const [data, setData] = useState<PlansAdmin | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const load = useCallback(async () => {
    try {
      const next = await api<PlansAdmin>("/admin/plans");
      setData(next);
      setDrafts(Object.fromEntries(next.plans.map((p) => [p.code, draftOf(p)])));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load plans");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function setDraft(code: string, field: keyof Draft, value: string) {
    setDrafts((d) => ({ ...d, [code]: { ...d[code], [field]: value } }));
  }

  async function save(code: string) {
    const d = drafts[code];
    setBusy(code);
    setError("");
    setStatus("");
    try {
      await patch<AdminPlan>(`/admin/plans/${code}`, {
        name: d.name,
        monthly_price_usd: d.monthly_price_usd,
        monthly_price_cad: Number(d.monthly_price_cad),
        max_students: Number(d.max_students),
        ai_daily_generations: Number(d.ai_daily_generations),
      });
      setStatus(`Saved ${code}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed");
    } finally {
      setBusy("");
    }
  }

  async function recalc() {
    if (!window.confirm("Fetch the Bank of Canada 3-year-average rate and re-price every plan's CAD amount?")) {
      return;
    }
    setBusy("recalc");
    setError("");
    setStatus("");
    try {
      await post("/admin/plans/recalc-cad");
      setStatus("CAD prices recalculated from the stored 3-year-average rate.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Recalculation failed");
    } finally {
      setBusy("");
    }
  }

  if (error && !data) {
    return (
      <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
        {error}
      </p>
    );
  }
  if (!data) {
    return <p className="py-12 text-center text-sm text-slate-500">Loading plans…</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600">
          Stored USD→CAD 3-yr-average rate:{" "}
          <span className="font-semibold text-slate-900">{Number(data.usd_to_cad_rate).toFixed(4)}</span>
          <span className="ml-2 text-slate-400">(CAD is fixed — recalc is an audited action)</span>
        </p>
        {canManage && (
          <Button variant="secondary" size="sm" disabled={busy === "recalc"} onClick={recalc}>
            {busy === "recalc" ? "Recalculating…" : "Recalculate CAD prices"}
          </Button>
        )}
      </div>

      {status && (
        <p className="rounded-lg bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
          {status}
        </p>
      )}
      {error && (
        <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-dashboard">
        <table className="w-full min-w-[860px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="px-4 py-3 font-medium">Plan</th>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">USD/mo</th>
              <th className="px-4 py-3 font-medium">CAD/mo</th>
              <th className="px-4 py-3 font-medium">Seats</th>
              <th className="px-4 py-3 font-medium">AI/day</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {canManage && <th className="px-4 py-3 text-right font-medium"></th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.plans.map((p) => {
              const d = drafts[p.code];
              const input = "h-8 w-full text-sm";
              return (
                <tr key={p.code} className={p.active ? "" : "opacity-60"}>
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-800">
                    {p.code}
                  </td>
                  <td className="px-4 py-3">
                    {canManage && d ? (
                      <Input className={input} value={d.name} onChange={(e) => setDraft(p.code, "name", e.target.value)} />
                    ) : (
                      p.name
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {canManage && d ? (
                      <Input className={`${input} w-24`} value={d.monthly_price_usd} onChange={(e) => setDraft(p.code, "monthly_price_usd", e.target.value)} />
                    ) : (
                      `$${Number(p.monthly_price_usd).toFixed(2)}`
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {canManage && d ? (
                      <Input className={`${input} w-20`} value={d.monthly_price_cad} onChange={(e) => setDraft(p.code, "monthly_price_cad", e.target.value)} />
                    ) : (
                      `CA$${p.monthly_price_cad}`
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {canManage && d ? (
                      <Input className={`${input} w-16`} value={d.max_students} onChange={(e) => setDraft(p.code, "max_students", e.target.value)} />
                    ) : (
                      p.max_students
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {canManage && d ? (
                      <Input className={`${input} w-20`} value={d.ai_daily_generations} onChange={(e) => setDraft(p.code, "ai_daily_generations", e.target.value)} />
                    ) : (
                      p.ai_daily_generations
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={p.active ? "default" : "outline"}>
                      {p.active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  {canManage && (
                    <td className="px-4 py-3 text-right">
                      <Button size="sm" disabled={busy === p.code} onClick={() => save(p.code)}>
                        {busy === p.code ? "Saving…" : "Save"}
                      </Button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400">
        Editing a USD price without a CAD override re-derives CAD from the stored
        rate (whole dollars, cents dropped). Plan seat and AI caps apply to
        families whose profile has no override.
      </p>
    </div>
  );
}
