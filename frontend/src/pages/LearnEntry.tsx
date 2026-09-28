import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api, post } from "../api";
import NavBar from "../components/NavBar";
import type {
  CurriculumChoice,
  LearnerChoice,
  LearnerLaunchpad,
  SessionOut,
  SkillChoice,
} from "../types";

const recommendationCopy: Record<string, { eyebrow: string; action: string; detail: string }> = {
  CONTINUE_SESSION: {
    eyebrow: "Continue where you left off",
    action: "Continue learning",
    detail: "Your current problem and learning stage are waiting for you.",
  },
  RESUME_IN_PROGRESS: {
    eyebrow: "Recommended next",
    action: "Keep going",
    detail: "This skill is already in progress. Continue building independent evidence.",
  },
  PREREQUISITE_GAP: {
    eyebrow: "Build the foundation",
    action: "Strengthen this skill",
    detail: "The tutor found a building block that will make the next skill easier.",
  },
  READY_TO_START: {
    eyebrow: "Recommended next",
    action: "Start learning",
    detail: "This is the best next step based on the curriculum learning path.",
  },
};

export default function LearnEntry() {
  const [learners, setLearners] = useState<LearnerChoice[]>([]);
  const [curricula, setCurricula] = useState<CurriculumChoice[]>([]);
  const [skills, setSkills] = useState<SkillChoice[]>([]);
  const [launchpad, setLaunchpad] = useState<LearnerLaunchpad | null>(null);
  const [learnerId, setLearnerId] = useState("");
  const [skillId, setSkillId] = useState("");
  const [firstName, setFirstName] = useState("");
  const [curriculumId, setCurriculumId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api<LearnerChoice[]>("/onboarding/learners"),
      api<CurriculumChoice[]>("/onboarding/curricula"),
    ])
      .then(([learnerRows, curriculumRows]) => {
        setLearners(learnerRows);
        setCurricula(curriculumRows);
        if (learnerRows.length) setLearnerId(learnerRows[0].id);
      })
      .catch(() => setError("We could not load your family learning space."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setSkills([]);
    setSkillId("");
    setLaunchpad(null);
    if (!learnerId) return;
    setLoading(true);
    setError("");
    Promise.all([
      api<SkillChoice[]>(`/onboarding/learners/${learnerId}/skills`),
      api<LearnerLaunchpad>(`/onboarding/learners/${learnerId}/launchpad`),
    ])
      .then(([skillRows, summary]) => {
        setSkills(skillRows);
        setLaunchpad(summary);
      })
      .catch(() => setError("We could not load this learner's next step."))
      .finally(() => setLoading(false));
  }, [learnerId]);

  async function addLearner(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      const created = await post<LearnerChoice & { id: string }>("/onboarding/learners", {
        first_name: firstName,
        curriculum_id: curriculumId,
      });
      const rows = await api<LearnerChoice[]>("/onboarding/learners");
      setLearners(rows);
      setLearnerId(created.id);
      setFirstName("");
      setNotice(`${created.first_name ?? "Learner"} is ready.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add learner");
    }
  }

  async function openSkill(targetSkillId: string) {
    if (!learnerId || !targetSkillId || starting) return;
    setStarting(true);
    setError("");
    try {
      const session = await post<SessionOut>("/adaptive-tutor/sessions", {
        student_id: learnerId,
        skill_id: targetSkillId,
      });
      navigate(`/learn/${session.session_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start learning");
      setStarting(false);
    }
  }

  async function continueLearning() {
    const recommendation = launchpad?.recommended;
    if (!recommendation || starting) return;
    if (recommendation.session_id) {
      navigate(`/learn/${recommendation.session_id}`);
      return;
    }
    await openSkill(recommendation.id);
  }

  async function startSelected(event: FormEvent) {
    event.preventDefault();
    await openSkill(skillId);
  }

  const learner = learners.find((row) => row.id === learnerId);
  const selectedSkill = skills.find((row) => row.id === skillId);
  const recommendation = launchpad?.recommended;
  const copy = recommendation ? recommendationCopy[recommendation.reason] : null;
  const masteryPercent = Math.round((recommendation?.mastery_score ?? 0) * 100);

  return (
    <>
      <NavBar />
      <main className="page learner-launchpad">
        <section className="launchpad-header">
          <div>
            <p className="eyebrow">Learner home</p>
            <h1>{learner ? `Welcome back, ${learner.first_name}` : "Your learning journey starts here"}</h1>
            <p>{learner ? "One focused step at a time. Your tutor has the next move ready." : "Choose a learner to see a personalized path."}</p>
          </div>
          {!!learners.length && (
            <div className="learner-picker">
              <label htmlFor="learner">Learner</label>
              <select id="learner" value={learnerId} onChange={(event) => setLearnerId(event.target.value)}>
                {learners.map((row) => <option key={row.id} value={row.id}>{row.first_name} — {row.curriculum_code}</option>)}
              </select>
            </div>
          )}
        </section>

        {loading && <section className="launchpad-skeleton" aria-live="polite" aria-label="Loading learner home"><div /><div /><div /></section>}

        {!loading && learner && launchpad && (
          <>
            <section className="continue-card" aria-labelledby="continue-heading">
              <div className="continue-copy">
                <p className="eyebrow">{copy?.eyebrow ?? "Learning path"}</p>
                <h2 id="continue-heading">{recommendation?.name ?? "Choose a skill to begin"}</h2>
                <p>{copy?.detail ?? "Explore the skill library and choose a learner-ready activity."}</p>
                {recommendation && (
                  <div className="continue-progress" aria-label={`${masteryPercent}% mastery`}>
                    <span><strong>{masteryPercent}</strong>% mastery</span>
                    <div className="progress-track"><span style={{ width: `${masteryPercent}%` }} /></div>
                  </div>
                )}
                <button className="primary continue-action" type="button" disabled={!recommendation || starting} onClick={continueLearning}>
                  {starting ? "Opening…" : copy?.action ?? "Explore skills"}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
              <div className="journey-orbit" aria-hidden="true">
                <span className="orbit-ring" />
                <span className="orbit-core">{masteryPercent || "Start"}</span>
                <span className="orbit-dot dot-one" />
                <span className="orbit-dot dot-two" />
              </div>
            </section>

            <section className="launchpad-metrics" aria-label="Learning progress">
              <article><span className="metric-icon mastery-icon" aria-hidden="true">✓</span><div><strong>{launchpad.mastered_count}</strong><span>Skills mastered</span></div></article>
              <article><span className="metric-icon learning-icon" aria-hidden="true">↗</span><div><strong>{launchpad.learning_count}</strong><span>Skills in progress</span></div></article>
              <article><span className="metric-icon review-icon" aria-hidden="true">↻</span><div><strong>{launchpad.reviews_due.length}</strong><span>Reviews due</span></div></article>
              <article><span className="metric-icon award-icon" aria-hidden="true">★</span><div><strong>{launchpad.award_count}</strong><span>Badges earned</span></div></article>
            </section>

            <div className="launchpad-grid">
              <section className="card journey-card" aria-labelledby="journey-heading">
                <div className="section-heading">
                  <div><p className="eyebrow">Your journey</p><h2 id="journey-heading">Learning momentum</h2></div>
                  <span className="status-pill">{learner.curriculum_code}</span>
                </div>
                <div className="journey-strip">
                  <div className="journey-node complete"><span>✓</span><strong>Foundation</strong><small>Skills proved</small></div>
                  <span className="journey-line active" />
                  <div className="journey-node active"><span>2</span><strong>Learning now</strong><small>{recommendation?.name ?? "Choose a skill"}</small></div>
                  <span className="journey-line" />
                  <div className="journey-node"><span>3</span><strong>Mastery</strong><small>Independent proof</small></div>
                </div>
                {launchpad.reviews_due.length > 0 && (
                  <div className="review-callout"><span aria-hidden="true">↻</span><div><strong>Keep it sharp</strong><p>{launchpad.reviews_due[0].skill_name} is ready for a quick review.</p></div></div>
                )}
              </section>

              <aside className="card curriculum-card">
                <p className="eyebrow">Learning plan</p>
                <h2>{learner.curriculum_code}</h2>
                <dl>
                  <div><dt>Version</dt><dd>{learner.curriculum_version}</dd></div>
                  <div><dt>Jurisdiction</dt><dd>{learner.jurisdiction ?? "Curriculum-defined"}</dd></div>
                  <div><dt>Practice-ready</dt><dd>{launchpad.ready_skill_count} skills</dd></div>
                </dl>
              </aside>
            </div>

            <details className="card skill-library">
              <summary><span><span className="eyebrow">Skill library</span><strong>Choose something else</strong></span><span aria-hidden="true">＋</span></summary>
              <form onSubmit={startSelected}>
                <label htmlFor="skill">Skill</label>
                <select id="skill" value={skillId} onChange={(event) => setSkillId(event.target.value)} required>
                  <option value="">Select skill</option>
                  {skills.map((skill) => <option key={skill.id} value={skill.id} disabled={!skill.content_ready}>{skill.code} · {skill.name}{skill.content_ready ? "" : " (content in progress)"}</option>)}
                </select>
                <div className="skill-grid" aria-label="Available skills">
                  {skills.map((skill) => (
                    <button key={skill.id} type="button" className={skill.id === skillId ? "skill-choice selected" : "skill-choice"} disabled={!skill.content_ready} aria-pressed={skill.id === skillId} onClick={() => setSkillId(skill.id)}>
                      <span className="skill-code">{skill.code}</span><strong>{skill.name}</strong><span>{skill.content_ready ? "Ready to practice" : "Content in progress"}</span>
                    </button>
                  ))}
                </div>
                <button className="secondary" disabled={!selectedSkill || starting}>{starting ? "Opening…" : "Practice selected skill"}</button>
              </form>
            </details>
          </>
        )}

        {!loading && !learners.length && (
          <section className="empty-launchpad card"><span aria-hidden="true">A</span><h1>Add your first learner</h1><p>Connect a curriculum to create a personalized learning path.</p></section>
        )}

        <details className="card add-learner-card" open={!learners.length}>
          <summary><span><span className="eyebrow">Family setup</span><strong>Add another learner</strong></span><span aria-hidden="true">＋</span></summary>
          <form onSubmit={addLearner}>
            <label htmlFor="firstName">Learner first name</label>
            <input id="firstName" value={firstName} onChange={(event) => setFirstName(event.target.value)} required />
            <label htmlFor="curriculum">Exact curriculum</label>
            <select id="curriculum" value={curriculumId} onChange={(event) => setCurriculumId(event.target.value)} required>
              <option value="">Select curriculum</option>
              {curricula.map((curriculum) => <option key={curriculum.id} value={curriculum.id}>{curriculum.code} ({curriculum.version})</option>)}
            </select>
            <button type="submit" className="secondary">Add learner</button>
          </form>
        </details>

        {notice && <p className="launchpad-notice success" role="status">{notice}</p>}
        {error && <div className="launchpad-error" role="alert"><strong>Something went wrong</strong><span>{error}</span><button type="button" onClick={() => window.location.reload()}>Try again</button></div>}
      </main>
    </>
  );
}
