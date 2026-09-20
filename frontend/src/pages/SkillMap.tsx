import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, api } from "../api";
import NavBar from "../components/NavBar";
import type { SkillMapEntry } from "../types";

function tier(entry: SkillMapEntry): "mastered" | "learning" | "locked" {
  if (entry.status === "MASTERED") return "mastered";
  if (entry.mastery_score > 0 || entry.status !== "NOT_STARTED")
    return "learning";
  return "locked";
}

const TIER_LABEL = {
  mastered: "Mastered",
  learning: "In progress",
  locked: "Not started",
};

export default function SkillMap() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [entries, setEntries] = useState<SkillMapEntry[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<SkillMapEntry[]>(`/learner-workspace/sessions/${sessionId}/skill-map`)
      .then(setEntries)
      .catch((err) =>
        setError(
          err instanceof ApiError ? err.message : "Could not load skill map",
        ),
      );
  }, [sessionId]);

  const mastered = entries?.filter((e) => e.status === "MASTERED").length ?? 0;

  return (
    <>
      <NavBar />
      <main className="page">
        <section className="hero">
          <div className="hero-row">
            <div>
              <h1>Skill map</h1>
              <p>
                {entries
                  ? `${mastered} of ${entries.length} skills mastered`
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

        <div className="map-legend">
          <span className="legend-key mastered" /> Mastered
          <span className="legend-key learning" /> In progress
          <span className="legend-key locked" /> Not started
        </div>

        <section className="skill-map">
          {entries?.map((entry) => {
            const pct = Math.round(entry.mastery_score * 100);
            const level = tier(entry);
            return (
              <div
                key={entry.skill_id}
                className={`map-tile ${level} ${entry.is_active ? "active" : ""}`}
              >
                {entry.is_active && (
                  <span className="map-active-tag">You are here</span>
                )}
                <div className="map-code">{entry.code}</div>
                <div className="map-name">{entry.name}</div>
                <div className="map-score">{pct}</div>
                <div className="bar">
                  <div
                    className={`bar-fill map-${level}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="muted small">{TIER_LABEL[level]}</div>
              </div>
            );
          })}
        </section>
      </main>
    </>
  );
}
