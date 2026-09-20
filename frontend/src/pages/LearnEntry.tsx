import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import type {
  CurriculumChoice,
  LearnerChoice,
  SessionOut,
  SkillChoice,
} from "../types";

export default function LearnEntry() {
  const [learners, setLearners] = useState<LearnerChoice[]>([]);
  const [curricula, setCurricula] = useState<CurriculumChoice[]>([]);
  const [skills, setSkills] = useState<SkillChoice[]>([]);
  const [learnerId, setLearnerId] = useState("");
  const [skillId, setSkillId] = useState("");
  const [firstName, setFirstName] = useState("");
  const [curriculumId, setCurriculumId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api<LearnerChoice[]>("/onboarding/learners")
      .then((rows) => {
        setLearners(rows);
        if (rows.length === 1) setLearnerId(rows[0].id);
      })
      .catch(() => setError("Could not load learners"));
    api<CurriculumChoice[]>("/onboarding/curricula")
      .then(setCurricula)
      .catch(() => {});
  }, []);

  useEffect(() => {
    setSkills([]);
    setSkillId("");
    if (!learnerId) return;
    api<SkillChoice[]>(`/onboarding/learners/${learnerId}/skills`)
      .then(setSkills)
      .catch(() => setError("Could not load skills"));
  }, [learnerId]);

  async function addLearner(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      const created = await post<LearnerChoice & { id: string }>(
        "/onboarding/learners",
        { first_name: firstName, curriculum_id: curriculumId },
      );
      const rows = await api<LearnerChoice[]>("/onboarding/learners");
      setLearners(rows);
      setLearnerId(created.id);
      setFirstName("");
      setNotice(`${created.first_name ?? "Learner"} is ready.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add learner");
    }
  }

  async function startSession(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const session = await post<SessionOut>("/adaptive-tutor/sessions", {
        student_id: learnerId,
        skill_id: skillId,
      });
      navigate(`/learn/${session.session_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start session");
    }
  }

  const selectedLearner = learners.find((l) => l.id === learnerId);

  return (
    <>
      <NavBar />
      <main className="page">
        <section className="hero">
          <h1>Start a learning session</h1>
          <p>Choose a learner and curriculum, or start learning.</p>
        </section>
        <div className="grid two">
          <section className="card">
            <h2>Learner</h2>
            <form onSubmit={startSession}>
              <label htmlFor="learner">Learner</label>
              <select
                id="learner"
                value={learnerId}
                onChange={(e) => setLearnerId(e.target.value)}
                required
              >
                <option value="">Select learner</option>
                {learners.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.first_name} — {l.curriculum_code}
                  </option>
                ))}
              </select>
              <label htmlFor="skill">Skill</label>
              <select
                id="skill"
                value={skillId}
                onChange={(e) => setSkillId(e.target.value)}
                required
                disabled={!learnerId}
              >
                <option value="">
                  {learnerId ? "Select skill" : "Pick a learner first"}
                </option>
                {skills.map((s) => (
                  <option key={s.id} value={s.id} disabled={!s.content_ready}>
                    {s.code} · {s.name}
                    {s.content_ready ? "" : " (content in progress)"}
                  </option>
                ))}
              </select>
              <button
                type="submit"
                className="primary"
                disabled={!learnerId || !skillId}
              >
                Start learning
              </button>
            </form>
            {selectedLearner && (
              <p className="muted small">
                Curriculum {selectedLearner.curriculum_code} (
                {selectedLearner.curriculum_version})
              </p>
            )}
          </section>
          <section className="card">
            <h2>Add a learner</h2>
            <form onSubmit={addLearner}>
              <label htmlFor="firstName">Learner first name</label>
              <input
                id="firstName"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
              />
              <label htmlFor="curriculum">Exact curriculum</label>
              <select
                id="curriculum"
                value={curriculumId}
                onChange={(e) => setCurriculumId(e.target.value)}
                required
              >
                <option value="">Select curriculum</option>
                {curricula.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} ({c.version})
                  </option>
                ))}
              </select>
              <button type="submit" className="secondary">
                Add learner
              </button>
            </form>
            {notice && <p className="success">{notice}</p>}
          </section>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </main>
    </>
  );
}
