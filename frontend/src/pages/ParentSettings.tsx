import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api";
import NavBar from "../components/NavBar";

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
    <>
      <NavBar />
      <main className="page parent-page">
        <section className="hero">
          <p className="eyebrow">Parent settings</p>
          <h1>Settings &amp; privacy</h1>
          <p>
            <Link to="/parent">Back to dashboard</Link>
          </p>
        </section>

        {!unlocked && (
          <section className="card" aria-labelledby="settings-unlock-heading">
            <h2 id="settings-unlock-heading">Parent access</h2>
            <p className="muted small">
              Enter your 4-digit parent PIN to open settings and privacy controls.
            </p>
            <form onSubmit={unlock}>
              <label htmlFor="settings-pin">Parent PIN</label>
              <input
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
              <button type="submit" className="primary">Unlock</button>
            </form>
          </section>
        )}

        {unlocked && (
          <>
            <section className="card" aria-labelledby="profile-heading">
              <h2 id="profile-heading">Profile</h2>
              <form onSubmit={saveProfile}>
                <label htmlFor="display-name">Display name</label>
                <input
                  id="display-name"
                  required
                  minLength={1}
                  maxLength={120}
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                />
                <button type="submit" className="secondary">Save</button>
              </form>
              {profile && <p className="muted small">Email: {profile.email}</p>}
            </section>

            <section className="card" aria-labelledby="privacy-heading">
              <h2 id="privacy-heading">Privacy &amp; family data</h2>
              {notice ? (
                <p className="muted small">{notice.title}: {notice.summary}</p>
              ) : (
                <p className="muted small">Loading privacy notice…</p>
              )}
              {notice && !notice.acknowledged && (
                <button type="button" className="secondary" onClick={acknowledgeNotice}>
                  Acknowledge current notice
                </button>
              )}
              {summary && (
                <p className="muted small">
                  Active learners: {summary.active_learner_count}. Stored categories:{" "}
                  {summary.stored_categories.join(", ")}.
                </p>
              )}

              <h3>Delete a learner's data</h3>
              <p className="muted small">
                This permanently deletes the selected learner and their tutoring/progress
                evidence. This is different from removing a child from your dashboard. Shared
                curriculum content is not deleted.
              </p>
              <label htmlFor="delete-learner">Learner</label>
              <select
                id="delete-learner"
                value={deleteLearnerId}
                onChange={(event) => setDeleteLearnerId(event.target.value)}
              >
                <option value="">Select a learner</option>
                {children.map((child) => (
                  <option key={child.id} value={child.id}>
                    {child.first_name} · Grade {child.grade_level}
                  </option>
                ))}
              </select>
              <label htmlFor="delete-confirm">Type DELETE to confirm</label>
              <input
                id="delete-confirm"
                autoComplete="off"
                value={deleteConfirm}
                onChange={(event) => setDeleteConfirm(event.target.value)}
              />
              <button type="button" className="danger" onClick={deleteLearner}>
                Permanently delete learner data
              </button>
            </section>
          </>
        )}

        {status && <p className="success" role="status">{status}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </main>
    </>
  );
}
