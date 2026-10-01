import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Lock, ShieldCheck, Trash2 } from "lucide-react";
import { ApiError } from "../api";
import NavBar from "../components/NavBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type Profile = { display_name: string | null; email: string };
type PrivacyNotice = { version: string; title: string; summary: string; acknowledged: boolean };
type DataSummary = { active_learner_count: number; stored_categories: string[] };
type Child = { id: string; first_name: string; grade_level: string };

async function adultRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem("parentUnlock");
  const response = await fetch(`/api/v1${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(token ? { "X-Parent-Unlock": token } : {}),
    },
  });
  if (response.status === 401) {
    window.location.assign("/login?next=/parent/settings");
    throw new ApiError(401, "Authentication required");
  }
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* no JSON body */
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return null as T;
  return response.json() as Promise<T>;
}

export default function ParentSettings() {
  const [pin, setPin] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [notice, setNotice] = useState<PrivacyNotice | null>(null);
  const [summary, setSummary] = useState<DataSummary | null>(null);
  const [children, setChildren] = useState<Child[]>([]);
  const [deleteLearnerId, setDeleteLearnerId] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const loadAdultSettings = useCallback(async () => {
    const p = await adultRequest<Profile>("/parents/profile");
    setProfile(p);
    setDisplayName(p.display_name ?? "");
    const [n, s, kids] = await Promise.all([
      adultRequest<PrivacyNotice>("/privacy/notice"),
      adultRequest<DataSummary>("/privacy/data-summary"),
      adultRequest<Child[]>("/parents/children"),
    ]);
    setNotice(n);
    setSummary(s);
    setChildren(kids);
    setUnlocked(true);
  }, []);

  useEffect(() => {
    if (!sessionStorage.getItem("parentUnlock")) return;
    loadAdultSettings().catch(() => {
      sessionStorage.removeItem("parentUnlock");
      setUnlocked(false);
    });
  }, [loadAdultSettings]);

  async function unlock(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await adultRequest<{ unlock_token: string }>("/parents/verify-pin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parent_pin: pin }),
      });
      sessionStorage.setItem("parentUnlock", result.unlock_token);
      setPin("");
      await loadAdultSettings();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not verify parent PIN.");
    }
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const p = await adultRequest<Profile>("/parents/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName }),
      });
      setProfile(p);
      setStatus(`Saved as ${p.display_name}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save profile.");
    }
  }

  async function acknowledgeNotice() {
    if (!notice) return;
    setError("");
    try {
      await adultRequest("/privacy/notice/acknowledge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notice_version: notice.version }),
      });
      setStatus("Privacy notice acknowledged.");
      setNotice({ ...notice, acknowledged: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not acknowledge notice.");
    }
  }

  async function deleteLearner() {
    setError("");
    if (!deleteLearnerId) {
      setError("Select a learner.");
      return;
    }
    if (deleteConfirm !== "DELETE") {
      setError("Type DELETE exactly to confirm.");
      return;
    }
    if (!window.confirm("Permanently delete this learner and their learning evidence? This cannot be undone.")) {
      return;
    }
    try {
      await adultRequest(`/privacy/learners/${deleteLearnerId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmation: "DELETE" }),
      });
      setDeleteConfirm("");
      setDeleteLearnerId("");
      setStatus("Learner data deleted.");
      const s = await adultRequest<DataSummary>("/privacy/data-summary");
      setSummary(s);
      setChildren(await adultRequest<Child[]>("/parents/children"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete learner data.");
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-2xl px-4 py-8">
        <div className="mb-8">
          <Link to="/parent" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Back to dashboard
          </Link>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Settings &amp; privacy</h1>
        </div>

        {!unlocked && (
          <Card className="mx-auto max-w-md">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-primary" />
                <CardTitle>Parent access</CardTitle>
              </div>
              <CardDescription>
                Enter your 4-digit parent PIN to open settings and privacy controls.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={unlock} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="settings-pin">Parent PIN</Label>
                  <Input
                    id="settings-pin"
                    type="password"
                    inputMode="numeric"
                    pattern="[0-9]{4}"
                    minLength={4}
                    maxLength={4}
                    required
                    autoComplete="off"
                    value={pin}
                    onChange={(event) => setPin(event.target.value)}
                  />
                </div>
                <Button type="submit" className="w-full">Unlock</Button>
              </form>
            </CardContent>
          </Card>
        )}

        {unlocked && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Profile</CardTitle>
                {profile && <CardDescription>Signed in as {profile.email}</CardDescription>}
              </CardHeader>
              <CardContent>
                <form onSubmit={saveProfile} className="flex items-end gap-3">
                  <div className="flex-1 space-y-1.5">
                    <Label htmlFor="display-name">Display name</Label>
                    <Input
                      id="display-name"
                      required
                      minLength={1}
                      maxLength={120}
                      value={displayName}
                      onChange={(event) => setDisplayName(event.target.value)}
                    />
                  </div>
                  <Button type="submit" variant="secondary">Save</Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  <CardTitle>Privacy &amp; family data</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {notice ? (
                  <p className="text-sm text-muted-foreground">{notice.title}: {notice.summary}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">Loading privacy notice…</p>
                )}
                {notice && !notice.acknowledged && (
                  <Button variant="secondary" onClick={acknowledgeNotice}>
                    Acknowledge current notice
                  </Button>
                )}
                {summary && (
                  <p className="text-sm text-muted-foreground">
                    Active learners: {summary.active_learner_count}. Stored categories:{" "}
                    {summary.stored_categories.join(", ")}.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className="border-destructive/30">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Trash2 className="h-5 w-5 text-destructive" />
                  <CardTitle>Delete a learner's data</CardTitle>
                </div>
                <CardDescription>
                  This permanently deletes the selected learner and their tutoring/progress
                  evidence. This is different from removing a child from your dashboard.
                  Shared curriculum content is not deleted.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="delete-learner">Learner</Label>
                  <Select value={deleteLearnerId} onValueChange={setDeleteLearnerId}>
                    <SelectTrigger id="delete-learner">
                      <SelectValue placeholder="Select a learner" />
                    </SelectTrigger>
                    <SelectContent>
                      {children.map((child) => (
                        <SelectItem key={child.id} value={child.id}>
                          {child.first_name} · Grade {child.grade_level}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="delete-confirm">Type DELETE to confirm</Label>
                  <Input
                    id="delete-confirm"
                    autoComplete="off"
                    value={deleteConfirm}
                    onChange={(event) => setDeleteConfirm(event.target.value)}
                  />
                </div>
                <Button variant="destructive" onClick={deleteLearner}>
                  Permanently delete learner data
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {status && (
          <p className="mt-6 rounded-md bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700" role="status">
            {status}
          </p>
        )}
        {error && (
          <p className="mt-6 rounded-md bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive" role="alert">
            {error}
          </p>
        )}
      </main>
    </div>
  );
}
