import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { api, ApiError, post } from "../../api";
import Brand from "../../components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import OverviewTab from "./OverviewTab";
import FamiliesTab from "./FamiliesTab";
import ActivityTab from "./ActivityTab";
import AiUsageTab from "./AiUsageTab";
import PlansTab from "./PlansTab";
import AuditTab from "./AuditTab";
import type { MfaSetup, StaffMe } from "./types";

type Stage = "loading" | "denied" | "enroll" | "verify" | "ready";

type TabDef = { id: string; label: string; permission: string };

const TABS: TabDef[] = [
  { id: "overview", label: "Overview", permission: "admin.metrics.read" },
  { id: "families", label: "Families", permission: "admin.families.read" },
  { id: "activity", label: "Activity", permission: "admin.metrics.read" },
  { id: "ai", label: "AI usage", permission: "admin.ai_usage.read" },
  { id: "plans", label: "Plans", permission: "admin.metrics.read" },
  { id: "audit", label: "Audit", permission: "admin.audit.read" },
];

function MfaGate({
  me,
  onComplete,
}: {
  me: StaffMe;
  onComplete: (updated: StaffMe) => void;
}) {
  const enrolling = !me.mfa_enrolled;
  const [setup, setSetup] = useState<MfaSetup | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!enrolling) return;
    post<MfaSetup>("/admin/mfa/setup").then(setSetup).catch((err) => {
      setError(err instanceof ApiError ? err.message : "Could not start enrollment");
    });
  }, [enrolling]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const updated = await post<StaffMe>(
        enrolling ? "/admin/mfa/confirm" : "/admin/mfa/verify",
        { code },
      );
      onComplete(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Verification failed");
      setCode("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid flex-1 place-items-center px-4 pb-16">
      <Card className="w-full max-w-md shadow-raised">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <ShieldCheck className="h-5 w-5 text-primary" />
            {enrolling ? "Set up two-factor sign-in" : "Two-factor verification"}
          </CardTitle>
          <CardDescription>
            {enrolling
              ? "Staff accounts require an authenticator app. Enter the setup key below, then type the 6-digit code it generates."
              : "Enter the 6-digit code from your authenticator app."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {enrolling &&
            (setup ? (
              <div className="space-y-3">
                <div className="rounded-lg border border-dashed border-slate-300 bg-secondary/60 p-3 text-center">
                  <p className="font-mono text-lg tracking-[0.2em] text-slate-900">
                    {setup.secret}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Manual entry key — keep it private
                  </p>
                </div>
                <details className="text-xs text-slate-500">
                  <summary className="cursor-pointer font-medium">
                    otpauth:// URI (advanced)
                  </summary>
                  <p className="mt-1 break-all font-mono">{setup.otpauth_uri}</p>
                </details>
              </div>
            ) : (
              !error && <p className="text-sm text-slate-500">Preparing enrollment…</p>
            ))}
          <form onSubmit={submit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="totp">6-digit code</Label>
              <Input
                id="totp"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]{6}"
                minLength={6}
                maxLength={6}
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              />
            </div>
            {error && (
              <p
                className="rounded-md bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive"
                role="alert"
              >
                {error}
              </p>
            )}
            <Button type="submit" className="w-full" disabled={busy || (enrolling && !setup)}>
              {busy ? "Verifying…" : enrolling ? "Enable two-factor" : "Verify"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function AdminDashboard() {
  const [stage, setStage] = useState<Stage>("loading");
  const [me, setMe] = useState<StaffMe | null>(null);
  const [tab, setTab] = useState("overview");

  useEffect(() => {
    api<StaffMe>("/admin/me")
      .then((staff) => {
        setMe(staff);
        setStage(!staff.mfa_enrolled ? "enroll" : staff.mfa_verified ? "ready" : "verify");
      })
      .catch((err) => {
        // 401 already redirected to /login; 404 = signed in but not staff.
        if (!(err instanceof ApiError && err.status === 401)) setStage("denied");
      });
  }, []);

  const visibleTabs = useMemo(
    () => (me ? TABS.filter((t) => me.permissions.includes(t.permission)) : []),
    [me],
  );
  const activeTab = visibleTabs.some((t) => t.id === tab)
    ? tab
    : (visibleTabs[0]?.id ?? "overview");

  const onMfaComplete = useCallback((updated: StaffMe) => {
    setMe(updated);
    setStage("ready");
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <Link to="/" aria-label="Mihur home">
          <Brand size="md" />
        </Link>
        {me && (
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
              {me.role}
            </span>
            <span className="hidden sm:inline">{me.email}</span>
          </div>
        )}
      </header>

      {stage === "loading" && (
        <p className="grid flex-1 place-items-center text-sm text-slate-500">Loading…</p>
      )}

      {stage === "denied" && (
        <div className="grid flex-1 place-items-center px-4">
          <Card className="max-w-md text-center">
            <CardHeader>
              <CardTitle>Staff access only</CardTitle>
              <CardDescription>
                This area requires a staff account. If you reached it by accident,
                head back to the app.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="secondary">
                <Link to="/learn">Back to Mihur</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {(stage === "enroll" || stage === "verify") && me && (
        <MfaGate me={me} onComplete={onMfaComplete} />
      )}

      {stage === "ready" && me && (
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
          <nav
            className="mb-6 flex flex-wrap gap-1 rounded-xl bg-white p-1 shadow-sm ring-1 ring-slate-200"
            role="tablist"
            aria-label="Admin sections"
          >
            {visibleTabs.map((t) => (
              <button
                key={t.id}
                role="tab"
                aria-selected={activeTab === t.id}
                onClick={() => setTab(t.id)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === t.id
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          {activeTab === "overview" && <OverviewTab />}
          {activeTab === "families" && (
            <FamiliesTab canApprove={me.permissions.includes("admin.families.approve")} />
          )}
          {activeTab === "activity" && <ActivityTab />}
          {activeTab === "ai" && <AiUsageTab />}
          {activeTab === "plans" && (
            <PlansTab canManage={me.permissions.includes("admin.plans.manage")} />
          )}
          {activeTab === "audit" && <AuditTab />}
        </main>
      )}
    </div>
  );
}
