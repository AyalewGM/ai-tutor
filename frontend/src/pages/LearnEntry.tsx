import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import type { CurriculumChoice, LearnerChoice, SessionOut, SkillChoice } from "../types";

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
  const [skillsLoading, setSkillsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api<LearnerChoice[]>("/onboarding/learners")
      .then((rows) => { setLearners(rows); if (rows.length === 1) setLearnerId(rows[0].id); })
      .catch(() => setError("Could not load learners"));
    api<CurriculumChoice[]>("/onboarding/curricula").then(setCurricula).catch(() => {});
  }, []);

  useEffect(() => {
    setSkills([]); setSkillId("");
    if (!learnerId) return;
    setSkillsLoading(true);
    api<SkillChoice[]>(`/onboarding/learners/${learnerId}/skills`)
      .then(setSkills)
      .catch(() => setError("Could not load skills"))
      .finally(() => setSkillsLoading(false));
  }, [learnerId]);

  async function addLearner(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    try {
      const created = await post<LearnerChoice & { id: string }>("/onboarding/learners", { first_name: firstName, curriculum_id: curriculumId });
      const rows = await api<LearnerChoice[]>("/onboarding/learners");
      setLearners(rows); setLearnerId(created.id); setFirstName("");
      setNotice(`${created.first_name ?? "Learner"} is ready.`);
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not add learner"); }
  }

  async function startSession(event: FormEvent) {
    event.preventDefault(); setError("");
    try {
      const session = await post<SessionOut>("/adaptive-tutor/sessions", { student_id: learnerId, skill_id: skillId });
      navigate(`/learn/${session.session_id}`);
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not start session"); }
  }

  const selectedLearner = learners.find((learner) => learner.id === learnerId);
  const selectedSkill = skills.find((skill) => skill.id === skillId);
  const readyCount = useMemo(() => skills.filter((skill) => skill.content_ready).length, [skills]);

  return (
    <>
      <NavBar />
      <main className="page learn-home">
        <section className="hero learn-hero">
          <p className="eyebrow">Learner home</p>
          <h1>{selectedLearner ? `Ready to learn, ${selectedLearner.first_name}?` : "Choose your learning path"}</h1>
          <p>Choose a learner, select a ready skill, and begin focused practice.</p>
        </section>

        <section className="learner-switcher" aria-labelledby="learner-heading">
          <div>
            <h2 id="learner-heading">Who is learning?</h2>
            <p className="muted small">Each learner stays connected to their exact curriculum and version.</p>
          </div>
          <label htmlFor="learner">Learner</label>
          <select id="learner" value={learnerId} onChange={(e) => setLearnerId(e.target.value)} required>
            <option value="">Select learner</option>
            {learners.map((learner) => <option key={learner.id} value={learner.id}>{learner.first_name} — {learner.curriculum_code}</option>)}
          </select>
        </section>

        {selectedLearner && (
          <section className="learning-context" aria-label="Learning context">
            <div><span>Curriculum</span><strong>{selectedLearner.curriculum_code}</strong></div>
            <div><span>Version</span><strong>{selectedLearner.curriculum_version}</strong></div>
            <div><span>Jurisdiction</span><strong>{selectedLearner.jurisdiction ?? "Curriculum-defined"}</strong></div>
            <div><span>Ready skills</span><strong>{readyCount}</strong></div>
          </section>
        )}

        <div className="learn-layout">
          <section className="card skill-discovery" aria-labelledby="skill-heading">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Practice</p>
                <h2 id="skill-heading">Choose a skill</h2>
              </div>
              {selectedSkill && <span className="status-pill">Selected</span>}
            </div>

            {!learnerId && <div className="guided-empty"><strong>Start by choosing a learner.</strong><p>We will show only skills assigned to that learner's curriculum.</p></div>}
            {learnerId && skillsLoading && <p className="muted" role="status">Loading curriculum skills…</p>}
            {learnerId && !skillsLoading && (
              <>
                <label htmlFor="skill">Skill</label>
                <select id="skill" value={skillId} onChange={(e) => setSkillId(e.target.value)} required>
                  <option value="">Select skill</option>
                  {skills.map((skill) => <option key={skill.id} value={skill.id} disabled={!skill.content_ready}>{skill.code} · {skill.name}{skill.content_ready ? "" : " (content in progress)"}</option>)}
                </select>

                <div className="skill-grid" aria-label="Available skills">
                  {skills.map((skill) => (
                    <button key={skill.id} type="button"
                      className={skill.id === skillId ? "skill-choice selected" : "skill-choice"}
                      disabled={!skill.content_ready}
                      aria-pressed={skill.id === skillId}
                      onClick={() => setSkillId(skill.id)}>
                      <span className="skill-code">{skill.code}</span>
                      <strong>{skill.name}</strong>
                      <span>{skill.content_ready ? "Ready to practice" : "Content in progress"}</span>
                    </button>
                  ))}
                </div>
                {!skills.length && <div className="guided-empty"><strong>No skills are available yet.</strong><p>This curriculum does not currently have learner-ready practice content.</p></div>}
              </>
            )}

            <form onSubmit={startSession} className="start-panel">
              <div>
                <span className="muted small">Your next session</span>
                <strong>{selectedSkill?.name ?? "Choose a skill to continue"}</strong>
              </div>
              <button type="submit" className="primary" disabled={!learnerId || !skillId}>Start learning</button>
            </form>
          </section>

          <aside>
            <section className="card add-learner-card">
              <p className="eyebrow">Family setup</p>
              <h2>Add a learner</h2>
              <p className="muted small">Connect a learner to an exact curriculum before practice begins.</p>
              <form onSubmit={addLearner}>
                <label htmlFor="firstName">Learner first name</label>
                <input id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
                <label htmlFor="curriculum">Exact curriculum</label>
                <select id="curriculum" value={curriculumId} onChange={(e) => setCurriculumId(e.target.value)} required>
                  <option value="">Select curriculum</option>
                  {curricula.map((curriculum) => <option key={curriculum.id} value={curriculum.id}>{curriculum.code} ({curriculum.version})</option>)}
                </select>
                <button type="submit" className="secondary">Add learner</button>
              </form>
              {notice && <p className="success" role="status">{notice}</p>}
            </section>
          </aside>
        </div>

        {error && <p className="error" role="alert">{error}</p>}
      </main>
    </>
  );
}
