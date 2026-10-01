import { FormEvent, useEffect, useState } from "react";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import ParentProgressDashboard from "../components/dashboard/ParentProgressDashboard";
import type { ChildSummary } from "../types";

export default function ParentDashboard() {
  const [children, setChildren] = useState<ChildSummary[]>([]);
  const [childId, setChildId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [pin, setPin] = useState("");
  const [unlockToken, setUnlockToken] = useState(
    () => sessionStorage.getItem("parentUnlock") || "",
  );

  useEffect(() => {
    api<ChildSummary[]>("/parents/children")
      .then((rows) => {
        setChildren(rows);
        if (rows.length) setChildId((current) => current || rows[0].id);
      })
      .catch(() => setError("Could not load family dashboard."))
      .finally(() => setLoading(false));
  }, []);

  async function unlockParentView(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await post<{ verified: boolean; unlock_token: string }>(
        "/parents/verify-pin",
        { parent_pin: pin },
      );
      sessionStorage.setItem("parentUnlock", result.unlock_token);
      setUnlockToken(result.unlock_token);
      setPin("");
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Could not verify parent PIN.");
    }
  }

  return (
    <>
      <NavBar />
      <main className="page parent-page">
        <section className="hero hero-row">
          <div>
            <p className="eyebrow">Parent dashboard</p>
            <h1>Family learning overview</h1>
            <p>
              A clear weekly view of independent progress, learning activity, and areas where
              your child may need support.
            </p>
          </div>
          <a className="secondary link-btn" href="/parent/settings">
            Settings &amp; privacy
          </a>
        </section>

        {!unlockToken && (
          <section className="card" aria-labelledby="parent-unlock-heading">
            <h2 id="parent-unlock-heading">Parent access</h2>
            <p className="muted small">
              Enter your 4-digit parent PIN to view progress and adult settings.
            </p>
            <form onSubmit={unlockParentView}>
              <label htmlFor="parent-pin">Parent PIN</label>
              <input
                id="parent-pin"
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
              <button type="submit" className="primary">
                Unlock parent view
              </button>
            </form>
          </section>
        )}

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {loading && (
          <p className="muted" role="status">
            Loading family profiles…
          </p>
        )}
        {!loading && !children.length && (
          <section className="card empty-state">
            <h2>No learners yet</h2>
            <p>Add a learner from Practice to begin building an evidence-backed progress view.</p>
          </section>
        )}

        {!loading && unlockToken && children.length > 0 && childId && (
          <ParentProgressDashboard
            unlockToken={unlockToken}
            children={children}
            selectedStudentId={childId}
            onStudentChange={setChildId}
          />
        )}
      </main>
    </>
  );
}
