import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, api } from "../api";
import NavBar from "../components/NavBar";
import type { Badge } from "../types";

function BadgeMedal({ earned }: { earned: boolean }) {
  return (
    <svg
      viewBox="0 0 64 64"
      width="56"
      height="56"
      className={`badge-icon ${earned ? "" : "badge-locked"}`}
      aria-hidden="true"
    >
      <circle cx="32" cy="26" r="20" fill={earned ? "#f59e0b" : "#d1d5db"} />
      <circle cx="32" cy="26" r="15" fill={earned ? "#fff8e6" : "#f3f4f6"} />
      <path
        d="M32 16l3 6.5 7 .8-5.2 4.7 1.4 7-6.2-3.6-6.2 3.6 1.4-7-5.2-4.7 7-.8z"
        fill={earned ? "#d97706" : "#9ca3af"}
      />
      <path
        d="M24 44l-4 14 12-6 12 6-4-14"
        fill={earned ? "#6d28d9" : "#e5e7eb"}
      />
    </svg>
  );
}

export default function Badges() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [badges, setBadges] = useState<Badge[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Badge[]>(`/learner-workspace/sessions/${sessionId}/badges`)
      .then(setBadges)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load badges"),
      );
  }, [sessionId]);

  const earnedCount = badges?.filter((b) => b.earned).length ?? 0;

  return (
    <>
      <NavBar />
      <main className="page">
        <section className="hero">
          <div className="hero-row">
            <div>
              <h1>Badge collection</h1>
              <p>
                {badges
                  ? `${earnedCount} of ${badges.length} earned`
                  : "Loading…"}
              </p>
            </div>
            <Link className="secondary link-btn" to={`/learn/${sessionId}`}>
              Back to practice
            </Link>
          </div>
        </section>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <section className="badge-grid">
          {badges?.map((badge) => (
            <div
              key={badge.code}
              className={`card badge-card ${badge.earned ? "" : "locked"}`}
            >
              <BadgeMedal earned={badge.earned} />
              <h3>{badge.name}</h3>
              <p className="muted small">{badge.description}</p>
              {badge.earned && badge.skill_names.length > 0 && (
                <p className="small badge-skill">
                  {badge.skill_names.join(", ")}
                  {badge.times_earned > 1 && ` (×${badge.times_earned})`}
                </p>
              )}
              {badge.earned && badge.skill_names.length === 0 && (
                <p className="small badge-skill">Earned</p>
              )}
              {!badge.earned && badge.progress && (
                <div className="badge-progress">
                  <div className="bar">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${Math.round(
                          (badge.progress.current / badge.progress.target) *
                            100,
                        )}%`,
                      }}
                    />
                  </div>
                  <span className="muted small">
                    {badge.progress.current} / {badge.progress.target}
                  </span>
                </div>
              )}
              {!badge.earned && !badge.progress && (
                <p className="muted small">Not yet earned</p>
              )}
            </div>
          ))}
        </section>
      </main>
    </>
  );
}
