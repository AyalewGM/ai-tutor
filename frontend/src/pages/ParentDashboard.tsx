import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import NavBar from "../components/NavBar";
import type { ChildDashboard, ChildSummary } from "../types";

function friendly(value: string | null | undefined) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function nextStep(code: string) {
  const copy: Record<string, string> = {
    COLLECT_MORE_EVIDENCE: "Keep practicing so the tutor can collect enough evidence.",
    CONTINUE_CURRENT_LEARNING: "Continue the current learning plan.",
    ENCOURAGE_INDEPENDENT_ATTEMPT: "Try a fresh problem independently when the tutor presents one.",
    RECOGNIZE_INDEPENDENT_PROGRESS: "Recognize the independent progress and continue the plan.",
    RECOGNIZE_MASTERY: "Celebrate the independently demonstrated mastery.",
    FOLLOW_EXISTING_REVIEW_PLAN: "Complete the review already scheduled by the tutoring engine.",
  };
  return copy[code] ?? "Continue the tutor plan.";
}

export default function ParentDashboard() {
  const [children, setChildren] = useState<ChildSummary[]>([]);
  const [childId, setChildId] = useState("");
  const [dashboard, setDashboard] = useState<ChildDashboard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<ChildSummary[]>("/parents/children")
      .then((rows) => {
        setChildren(rows);
        if (rows.length) setChildId(rows[0].id);
      })
      .catch(() => setError("Could not load family dashboard."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!childId) {
      setDashboard(null);
      return;
    }
    setLoading(true);
    setError("");
    api<ChildDashboard>(`/parents/children/${childId}/dashboard`)
      .then(setDashboard)
      .catch(() => setError("Could not load this learner's progress."))
      .finally(() => setLoading(false));
  }, [childId]);

  const counts = useMemo(() => {
    const skills = dashboard?.skills ?? [];
    return {
      mastered: skills.filter((s) => s.learning_state === "INDEPENDENT_MASTERY").length,
      progressing: skills.filter((s) => s.learning_state === "INDEPENDENT_PROGRESS").length,
      assisted: skills.filter((s) => s.learning_state === "ASSISTED_SUCCESS").length,
      evidence: skills.filter((s) => s.evidence_status === "INSUFFICIENT_EVIDENCE").length,
    };
  }, [dashboard]);

  return (
    <>
      <NavBar />
      <main className="page parent-page">
        <section className="hero hero-row">
          <div>
            <h1>Family learning overview</h1>
            <p>See what your child can do independently, where support is helping, and what comes next.</p>
          </div>
          <a className="secondary link-btn" href="/parent/settings">Settings &amp; privacy</a>
        </section>

        <section className="card parent-selector" aria-labelledby="child-heading">
          <div>
            <h2 id="child-heading">Choose a learner</h2>
            <p className="muted small">Progress is always scoped to the learner's exact curriculum and version.</p>
          </div>
          <label htmlFor="parent-child">Learner</label>
          <select id="parent-child" value={childId} onChange={(e) => setChildId(e.target.value)}>
            <option value="">Select learner</option>
            {children.map((child) => (
              <option key={child.id} value={child.id}>
                {child.first_name} — Grade {child.grade_level}
              </option>
            ))}
          </select>
        </section>

        {error && <p className="error" role="alert">{error}</p>}
        {loading && <p className="muted" role="status">Loading learning progress…</p>}
        {!loading && !children.length && (
          <section className="card empty-state">
            <h2>No learners yet</h2>
            <p>Add a learner from Practice to begin building an evidence-backed progress view.</p>
          </section>
        )}

        {dashboard && !loading && (
          <>
            <section className="card parent-overview">
              <div className="hero-row">
                <div>
                  <p className="eyebrow">Current learning picture</p>
                  <h2>{dashboard.child.first_name} · Grade {dashboard.child.grade_level}</h2>
                  <p className="muted">
                    {[dashboard.child.curriculum_name, dashboard.child.jurisdiction].filter(Boolean).join(" · ")}
                  </p>
                </div>
                <div className="next-focus">
                  <span>Recommended next</span>
                  <strong>{dashboard.recommended_next?.skill_name ?? dashboard.active_skill_name ?? "Keep practicing"}</strong>
                </div>
              </div>
              <p className="evidence-note">
                Assisted success is shown separately and never counted as independent mastery.
              </p>
            </section>

            <section aria-labelledby="summary-heading">
              <h2 id="summary-heading">At a glance</h2>
              <div className="parent-summary">
                <article className="summary-tile"><span>Independent mastery</span><strong>{counts.mastered}</strong></article>
                <article className="summary-tile"><span>Independent progress</span><strong>{counts.progressing}</strong></article>
                <article className="summary-tile"><span>Assisted success</span><strong>{counts.assisted}</strong></article>
                <article className="summary-tile"><span>More evidence needed</span><strong>{counts.evidence}</strong></article>
              </div>
            </section>

            <section className="card" aria-labelledby="skills-heading">
              <div className="card-title-row">
                <div>
                  <h2 id="skills-heading">Skills and next steps</h2>
                  <p className="muted small">Independent evidence is the source of truth for mastery.</p>
                </div>
              </div>
              <div className="parent-skill-grid">
                {dashboard.skills.map((skill) => (
                  <article className="parent-skill" key={skill.skill_id}>
                    <div className="hero-row">
                      <strong>{skill.skill_name}</strong>
                      <span className="status-pill">{friendly(skill.learning_state)}</span>
                    </div>
                    <p>{nextStep(skill.action_code)}</p>
                    <details>
                      <summary>Supporting evidence</summary>
                      <p className="muted small">
                        Independent: {skill.independent_correct_count}/{skill.independent_attempt_count} ·
                        Assisted successes: {skill.hinted_correct_count} · {friendly(skill.evidence_status)}
                      </p>
                    </details>
                  </article>
                ))}
                {!dashboard.skills.length && <p className="muted">No skill evidence recorded yet.</p>}
              </div>
            </section>

            <div className="grid two">
              <section className="card">
                <h2>Reviews due</h2>
                {dashboard.reviews_due.length ? (
                  <ul className="clean-list">
                    {dashboard.reviews_due.map((review) => (
                      <li key={review.skill_id}><strong>{review.skill_name}</strong><span>{friendly(review.status)}</span></li>
                    ))}
                  </ul>
                ) : <p className="muted">No reviews are due right now.</p>}
              </section>
              <section className="card">
                <h2>Current support areas</h2>
                {dashboard.support_areas.length ? (
                  <ul className="clean-list">
                    {dashboard.support_areas.map((area) => (
                      <li key={area.code}><strong>{area.name}</strong><span>{area.occurrence_count} observed</span></li>
                    ))}
                  </ul>
                ) : <p className="muted">No current support areas recorded.</p>}
              </section>
            </div>
          </>
        )}
      </main>
    </>
  );
}
