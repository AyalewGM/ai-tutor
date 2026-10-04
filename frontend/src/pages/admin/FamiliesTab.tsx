import { useCallback, useEffect, useState } from "react";
import { api, ApiError, post } from "../../api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { AdminFamily } from "./types";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  APPROVED: "default",
  PENDING: "secondary",
  REJECTED: "destructive",
};

export default function FamiliesTab({ canApprove }: { canApprove: boolean }) {
  const [status, setStatus] = useState<string>("ALL");
  const [families, setFamilies] = useState<AdminFamily[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const query = `?limit=50&offset=${page * 50}${status !== "ALL" ? `&status=${status}` : ""}`;
      setFamilies(await api<AdminFamily[]>(`/admin/families${query}`));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load families");
    } finally {
      setLoading(false);
    }
  }, [status, page]);

  useEffect(() => {
    void load();
  }, [load]);

  async function decide(family: AdminFamily, approve: boolean) {
    let reason: string | null = null;
    if (!approve) {
      reason = window.prompt("Rejection reason (optional, emailed to the family):", "");
      if (reason === null) return;
    }
    setBusyId(family.parent_profile_id);
    setError("");
    try {
      await post<AdminFamily>(
        `/admin/families/${family.parent_profile_id}/${approve ? "approve" : "reject"}`,
        approve ? {} : { reason: reason || null },
      );
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-base font-semibold text-slate-950">Families</h2>
        <Select
          value={status}
          onValueChange={(v) => {
            setStatus(v);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-44 bg-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-dashboard">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Learners</th>
              <th className="px-4 py-3 font-medium">Registered</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {canApprove && <th className="px-4 py-3 text-right font-medium">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {families.map((f) => (
              <tr key={f.parent_profile_id}>
                <td className="px-4 py-3 font-medium text-slate-900">{f.email}</td>
                <td className="px-4 py-3 text-slate-600">{f.display_name ?? "—"}</td>
                <td className="px-4 py-3 tabular-nums text-slate-900">{f.learner_count}</td>
                <td className="px-4 py-3 text-slate-600">
                  {new Date(f.registered_at).toLocaleDateString("en-US")}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={STATUS_VARIANT[f.approval_status] ?? "outline"}>
                    {f.approval_status}
                  </Badge>
                  {f.rejection_reason && (
                    <p className="mt-1 max-w-56 truncate text-xs text-slate-400" title={f.rejection_reason}>
                      {f.rejection_reason}
                    </p>
                  )}
                </td>
                {canApprove && (
                  <td className="px-4 py-3 text-right">
                    {f.approval_status === "PENDING" && (
                      <span className="inline-flex gap-2">
                        <Button
                          size="sm"
                          disabled={busyId === f.parent_profile_id}
                          onClick={() => decide(f, true)}
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          disabled={busyId === f.parent_profile_id}
                          onClick={() => decide(f, false)}
                        >
                          Reject
                        </Button>
                      </span>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {!loading && families.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-400">
                  No families match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm">
        <Button variant="secondary" size="sm" disabled={page === 0 || loading} onClick={() => setPage(page - 1)}>
          Previous
        </Button>
        <span className="text-slate-500">{loading ? "Loading…" : `Page ${page + 1}`}</span>
        <Button
          variant="secondary"
          size="sm"
          disabled={families.length < 50 || loading}
          onClick={() => setPage(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
