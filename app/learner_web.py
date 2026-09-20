import uuid

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["learner-web"])

_DESIGN_TOKENS = """
    :root {
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #172033;
      background: #f7f8fc;
      --goozam-blue: #2563eb;
      --goozam-indigo: #4f46e5;
      --goozam-purple: #7c3aed;
      --surface: #ffffff;
      --surface-soft: #f5f6ff;
      --border: #dfe3ef;
      --muted: #667085;
      --danger: #b42318;
      --success: #067647;
      --focus: #1d4ed8;
    }
"""


@router.get("/learn", response_class=HTMLResponse, include_in_schema=False)
def learner_entry_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Tutor</title>
  <style>
""" + _DESIGN_TOKENS + """
    * { box-sizing: border-box; }
    body { margin: 0; background: #f7f8fc; color: #172033; }
    nav.topbar {
      display: flex; align-items: center; gap: 1rem;
      background: var(--surface); border-bottom: 1px solid var(--border);
      padding: .7rem 1.25rem; position: sticky; top: 0; z-index: 10;
    }
    nav.topbar .brand {
      font-size: 1.15rem; font-weight: 800;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    nav.topbar a { color: var(--muted); text-decoration: none; font-weight: 600; font-size: .92rem; }
    nav.topbar a:hover { color: var(--goozam-indigo); }
    nav.topbar .spacer { flex: 1; }
    main { max-width: 680px; margin: auto; padding: 1.25rem; }
    header.hero {
      color: white;
      background:
        radial-gradient(circle at 85% 15%, rgba(255,255,255,.22), transparent 40%),
        linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      border-radius: 18px;
      padding: 1.6rem 1.4rem;
      margin-bottom: 1rem;
      box-shadow: 0 12px 30px rgba(79, 70, 229, .18);
    }
    header.hero h1 { margin: 0 0 .35rem; font-size: clamp(1.6rem, 4vw, 2.1rem); }
    header.hero p { margin: .25rem 0; color: rgba(255,255,255,.9); }
    header.hero nav { margin-top: .6rem; }
    header.hero a { color: rgba(255,255,255,.92); font-weight: 600; }
    .panel {
      background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
      padding: 1.25rem; margin-bottom: 1rem;
      box-shadow: 0 2px 10px rgba(23, 32, 51, .05);
    }
    label { display: block; margin-top: .8rem; font-weight: 650; }
    input, select, button { font: inherit; min-height: 44px; padding: .75rem; border-radius: 10px; border: 1px solid #c9cfdd; }
    input, select { width: 100%; box-sizing: border-box; }
    input:focus-visible, select:focus-visible, button:focus-visible { outline: 3px solid color-mix(in srgb, var(--focus) 36%, transparent); outline-offset: 2px; }
    button { margin-top: 1rem; min-height: 44px; cursor: pointer; font-weight: 650; }
    button.primary {
      color: #fff; border-color: transparent; width: 100%;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-indigo));
      box-shadow: 0 8px 18px rgba(37, 99, 235, .22);
    }
    button.secondary { background: var(--surface); color: var(--goozam-indigo); border-color: var(--border); width: 100%; }
    button.primary:disabled { opacity: .55; cursor: default; }
    .error { color: var(--danger); white-space: pre-wrap; }
    .muted { color: var(--muted); }
    details { margin-top: 1rem; }
    details summary { cursor: pointer; color: var(--goozam-indigo); font-weight: 650; min-height: 44px; display: flex; align-items: center; }
    details .panel-inner { padding-top: .5rem; }
    #newLearnerPanel[hidden] { display: none; }
  </style>
</head>
<body>
<nav class="topbar">
  <span class="brand">AI Tutor</span>
  <a href="/learn">Practice</a>
  <a href="/parent">Parent</a>
  <span class="spacer"></span>
  <a href="#" id="signOut">Sign out</a>
</nav>
<main>
  <header class="hero">
    <h1>Start learning</h1>
    <p>Adaptive math practice that meets you where you are.</p>
  </header>

  <section class="panel" aria-labelledby="startHeading">
    <h2 id="startHeading" style="margin-top:0">Start a learning session</h2>
    <p class="muted">Pick a learner and a skill. Curriculum scope and the first diagnostic problem are validated by the server.</p>
    <p id="error" class="error" role="alert" aria-live="assertive"></p>
    <form id="startForm">
      <label for="learnerSelect">Learner</label>
      <select id="learnerSelect" required></select>
      <label for="skillSelect">Skill</label>
      <select id="skillSelect" required></select>
      <button id="startBtn" class="primary" type="submit">Start learning</button>
    </form>

    <details id="newLearnerPanel">
      <summary>Add a new learner</summary>
      <form id="learnerForm">
        <label for="learnerName">First name</label>
        <input id="learnerName" autocomplete="off" required>
        <label for="curriculumSelect">Curriculum</label>
        <select id="curriculumSelect" required></select>
        <button id="learnerBtn" class="secondary" type="submit">Add learner</button>
      </form>
    </details>
  </section>
</main>
<script>
const api = '/api/v1';
const q = id => document.getElementById(id);

function setError(message = '') { q('error').textContent = message; }

async function request(path, options = {}) {
  const response = await fetch(api + path, {credentials: 'same-origin', ...options});
  if (response.status === 401) {
    window.location.assign('/login?next=/learn');
    throw new Error('Authentication required');
  }
  let body = null;
  try { body = await response.json(); } catch (_) {}
  if (!response.ok) throw new Error(body?.detail || `${response.status} ${response.statusText}`);
  return body;
}

async function loadSkills(learnerId) {
  const select = q('skillSelect');
  select.innerHTML = '';
  if (!learnerId) return;
  const skills = await request(`/onboarding/learners/${learnerId}/skills`);
  for (const skill of skills) {
    const option = document.createElement('option');
    option.value = skill.id;
    option.textContent = skill.name;
    select.appendChild(option);
  }
}

async function loadLearners(preferredId) {
  const learners = await request('/onboarding/learners');
  const select = q('learnerSelect');
  const current = preferredId || select.value;
  select.innerHTML = '';
  for (const learner of learners) {
    const option = document.createElement('option');
    option.value = learner.id;
    option.textContent = `${learner.first_name} · ${learner.curriculum_code}`;
    select.appendChild(option);
  }
  if (learners.some(l => l.id === current)) select.value = current;
  await loadSkills(select.value);
  q('startBtn').disabled = learners.length === 0;
}

async function loadCurricula() {
  const curricula = await request('/onboarding/curricula');
  const select = q('curriculumSelect');
  for (const curriculum of curricula) {
    const option = document.createElement('option');
    option.value = curriculum.id;
    option.textContent = `${curriculum.code} · ${curriculum.jurisdiction || curriculum.grade_level || ''}`;
    select.appendChild(option);
  }
}

q('learnerSelect').addEventListener('change', async e => {
  try { setError(); await loadSkills(e.target.value); }
  catch (err) { setError(err.message); }
});

q('learnerForm').addEventListener('submit', async e => {
  e.preventDefault();
  const button = q('learnerBtn');
  button.disabled = true;
  try {
    setError();
    const learner = await request('/onboarding/learners', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        first_name: q('learnerName').value.trim(),
        curriculum_id: q('curriculumSelect').value,
      }),
    });
    q('learnerName').value = '';
    await loadLearners(learner.id);
  } catch (err) { setError(err.message); }
  finally { button.disabled = false; }
});

q('startForm').addEventListener('submit', async e => {
  e.preventDefault();
  const button = q('startBtn');
  button.disabled = true;
  try {
    setError();
    const body = await request('/adaptive-tutor/sessions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        student_id: q('learnerSelect').value,
        skill_id: q('skillSelect').value,
      }),
    });
    window.location.assign(`/learn/${body.session_id}`);
  } catch (failure) {
    setError(`Unable to start this learning session: ${failure.message}`);
    button.disabled = false;
  }
});

q('signOut').addEventListener('click', async e => {
  e.preventDefault();
  try { await request('/auth/logout', {method: 'POST'}); } catch (_) {}
  window.location.assign('/login');
});

(async () => {
  try { await loadCurricula(); await loadLearners(); }
  catch (err) { setError(err.message); }
})();
</script>
</body>
</html>"""


@router.get("/learn/{session_id}", response_class=HTMLResponse, include_in_schema=False)
def learner_workspace_page(session_id: uuid.UUID) -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Tutor Learning Session</title>
  <style>
""" + _DESIGN_TOKENS + rf"""
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f7f8fc; color: #172033; }}
    nav.topbar {{
      display: flex; align-items: center; gap: 1rem;
      background: var(--surface); border-bottom: 1px solid var(--border);
      padding: .7rem 1.25rem; position: sticky; top: 0; z-index: 10;
    }}
    nav.topbar .brand {{
      font-size: 1.15rem; font-weight: 800;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      -webkit-background-clip: text; background-clip: text; color: transparent;
    }}
    nav.topbar a {{ color: var(--muted); text-decoration: none; font-weight: 600; font-size: .92rem; }}
    nav.topbar a:hover {{ color: var(--goozam-indigo); }}
    nav.topbar .spacer {{ flex: 1; }}
    main {{ max-width: 1080px; margin: auto; padding: 1.25rem; }}
    header.hero {{
      color: white;
      background:
        radial-gradient(circle at 85% 15%, rgba(255,255,255,.22), transparent 40%),
        linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      border-radius: 18px;
      padding: 1.5rem 1.4rem;
      margin-bottom: 1rem;
      box-shadow: 0 12px 30px rgba(79, 70, 229, .18);
    }}
    header.hero h1 {{ margin: 0 0 .5rem; font-size: clamp(1.5rem, 4vw, 2rem); }}
    .meta {{ display: flex; gap: .6rem; flex-wrap: wrap; align-items: center; }}
    .chip {{
      border: 1px solid rgba(255,255,255,.45);
      background: rgba(255,255,255,.14);
      color: #fff;
      border-radius: 999px;
      padding: .3rem .75rem;
      font-size: .9rem;
      font-weight: 600;
      backdrop-filter: blur(4px);
    }}
    .stepper {{ display: flex; gap: .4rem; margin-top: 1rem; flex-wrap: wrap; }}
    .step {{
      display: flex; align-items: center; gap: .4rem;
      font-size: .8rem; font-weight: 650; color: rgba(255,255,255,.75);
    }}
    .step .dot {{
      width: 22px; height: 22px; border-radius: 999px;
      border: 2px solid rgba(255,255,255,.5);
      display: inline-flex; align-items: center; justify-content: center;
      font-size: .7rem;
    }}
    .step.active {{ color: #fff; }}
    .step.active .dot {{ background: #fff; color: var(--goozam-indigo); border-color: #fff; }}
    .step.done .dot {{ background: rgba(255,255,255,.3); border-color: transparent; color: #fff; }}
    .layout {{ display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 1rem; align-items: start; }}
    .panel {{
      background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
      padding: 1.25rem; margin-bottom: 1rem;
      box-shadow: 0 2px 10px rgba(23, 32, 51, .05);
    }}
    .panel h2 {{ margin-top: 0; font-size: 1.05rem; }}
    .problem {{
      font-family: "SF Mono", ui-monospace, Menlo, Consolas, monospace;
      font-size: 1.45rem; line-height: 1.5; white-space: pre-wrap;
      background: linear-gradient(180deg, #fafbff, var(--surface-soft));
      border: 1px solid #e2e4f6; border-radius: 14px; padding: 1.4rem 1.2rem;
      text-align: center; letter-spacing: .01em;
      transition: border-color .2s ease, box-shadow .2s ease;
    }}
    .problem.correct {{ border-color: var(--success); box-shadow: 0 0 0 3px color-mix(in srgb, var(--success) 18%, transparent); }}
    .problem.wrong {{ border-color: var(--danger); box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger) 15%, transparent); animation: shake .3s ease; }}
    @keyframes shake {{ 25% {{ transform: translateX(-4px); }} 75% {{ transform: translateX(4px); }} }}
    .coach-row {{ display: flex; gap: .7rem; align-items: flex-start; }}
    .avatar {{
      width: 36px; height: 36px; border-radius: 999px; flex-shrink: 0;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      color: #fff; font-weight: 800; display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 10px rgba(79, 70, 229, .3);
    }}
    .coach {{
      background: var(--surface-soft); border: 1px solid #e2e4f6;
      padding: .75rem .95rem; border-radius: 4px 14px 14px 14px; line-height: 1.55;
      flex: 1;
    }}
    .actions {{ display: flex; gap: .65rem; flex-wrap: wrap; }}
    input, button {{ font: inherit; min-height: 44px; padding: .75rem .9rem; border-radius: 10px; border: 1px solid #c9cfdd; }}
    input {{ width: 100%; box-sizing: border-box; font-size: 1.1rem; }}
    input:focus-visible, button:focus-visible {{ outline: 3px solid color-mix(in srgb, var(--focus) 36%, transparent); outline-offset: 2px; }}
    button {{ cursor: pointer; min-height: 44px; font-weight: 650; background: var(--surface); color: #172033; transition: transform .12s ease, box-shadow .2s ease; }}
    button:hover:not(:disabled) {{ transform: translateY(-1px); }}
    button.primary {{ color: #fff; border-color: transparent; background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-indigo)); box-shadow: 0 8px 18px rgba(37, 99, 235, .22); }}
    button.primary:hover:not(:disabled) {{ box-shadow: 0 10px 22px rgba(37, 99, 235, .3); }}
    button[hidden], section[hidden] {{ display: none; }}
    .muted {{ color: var(--muted); }}
    .error {{ color: var(--danger); white-space: pre-wrap; }}
    .success {{ color: var(--success); font-weight: 600; }}
    .review-banner {{
      border: 1px solid #e2e4f6;
      border-left: 4px solid var(--goozam-purple);
      background: linear-gradient(90deg, color-mix(in srgb, var(--goozam-purple) 7%, var(--surface)), var(--surface-soft));
      border-radius: 10px;
      padding: .8rem 1rem;
      margin-bottom: 1rem;
    }}
    .ring-wrap {{ display: flex; align-items: center; gap: 1rem; }}
    .ring {{ transform: rotate(-90deg); }}
    .ring .track {{ stroke: #e2e4f6; }}
    .ring .fill {{ stroke: url(#ringGrad); stroke-linecap: round; transition: stroke-dashoffset .4s ease; }}
    .progress {{ display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; margin-top: 1rem; }}
    .metric {{ background: var(--surface-soft); border: 1px solid #e2e4f6; border-radius: 12px; padding: .8rem; }}
    .metric strong {{ display: block; color: var(--muted); font-size: .85rem; font-weight: 650; }}
    .metric div {{ font-size: 1.35rem; font-weight: 700; color: var(--goozam-indigo); margin-top: .2rem; }}
    .mastery-bar {{ height: 10px; border-radius: 999px; background: #e2e4f6; overflow: hidden; margin-top: .75rem; }}
    .mastery-bar > div {{ height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--goozam-blue), var(--goozam-purple)); transition: width .3s ease; }}
    .completion-hero {{ text-align: center; padding: 1rem 0; }}
    .completion-hero .badge {{
      width: 64px; height: 64px; margin: 0 auto .75rem; border-radius: 999px;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      color: #fff; font-size: 1.8rem; display: flex; align-items: center; justify-content: center;
      box-shadow: 0 10px 24px rgba(79, 70, 229, .35);
    }}
    @media (max-width: 600px) {{
      main {{ padding: .65rem; }}
      .layout {{ grid-template-columns: 1fr; }}
      .actions button {{ flex: 1 1 100%; }}
    }}
  </style>
</head>
<body>
<nav class="topbar">
  <span class="brand">AI Tutor</span>
  <a href="/learn">Practice</a>
  <a href="/parent">Parent</a>
  <span class="spacer"></span>
  <a href="#" id="signOut">Sign out</a>
</nav>
<main>
  <header class="hero">
    <h1 id="title">Learning session</h1>
    <div class="meta">
      <span id="curriculum" class="chip"></span>
      <span id="state" class="chip"></span>
      <span id="skill" class="chip"></span>
    </div>
    <div class="stepper" id="stepper" aria-label="Learning progress">
      <span class="step" data-state="DIAGNOSE"><span class="dot">1</span>Diagnose</span>
      <span class="step" data-state="GUIDED_PRACTICE"><span class="dot">2</span>Guided practice</span>
      <span class="step" data-state="INDEPENDENT_PRACTICE"><span class="dot">3</span>Independent</span>
      <span class="step" data-state="MASTERY_CHECK"><span class="dot">4</span>Mastery check</span>
      <span class="step" data-state="COMPLETE"><span class="dot">5</span>Complete</span>
    </div>
  </header>

  <p id="error" class="error" role="alert" aria-live="assertive"></p>
  <p id="status" role="status" aria-live="polite"></p>

  <section id="reviewBanner" class="review-banner" hidden>
    <strong>Review due:</strong> <span id="reviewList"></span>
    <div class="muted" style="font-size:.9rem">Quick refresh keeps mastered skills strong.</div>
  </section>

  <section id="completionPanel" class="panel" aria-labelledby="completionHeading" hidden>
    <div class="completion-hero">
      <div class="badge" aria-hidden="true">&#10003;</div>
      <h2 id="completionHeading">Skill complete</h2>
      <p id="completionMessage">You demonstrated this skill independently in the mastery check.</p>
      <p id="nextSkill" class="muted"></p>
      <p class="muted">Mastery is based on the tutor application's recorded independent evidence. Help and hints do not count as mastery evidence.</p>
      <a href="/learn"><button type="button" class="primary" style="padding:.75rem 2rem">Continue learning</button></a>
    </div>
  </section>

  <div class="layout">
    <div>
      <section id="problemPanel" class="panel" aria-labelledby="problemHeading">
        <h2 id="problemHeading">Current problem</h2>
        <div id="problem" class="problem">Loading…</div>
        <form id="answerForm">
          <label for="answer"><strong>Your answer</strong></label><br>
          <input id="answer" name="answer" autocomplete="off" required placeholder="Type your answer…">
          <div class="actions" style="margin-top:.75rem">
            <button id="submitBtn" class="primary" type="submit">Submit answer</button>
            <button id="hintBtn" type="button" hidden>Hint</button>
            <button id="struggleBtn" type="button" hidden>I don't understand</button>
          </div>
        </form>
      </section>

      <section class="panel" aria-labelledby="coachHeading">
        <h2 id="coachHeading">Coach</h2>
        <div class="coach-row">
          <div class="avatar" aria-hidden="true">T</div>
          <p id="coach" class="coach muted" style="margin:0">Loading coaching context…</p>
        </div>
      </section>
    </div>

    <section class="panel" aria-labelledby="progressHeading">
      <h2 id="progressHeading">Your progress</h2>
      <div class="ring-wrap">
        <svg class="ring" width="86" height="86" viewBox="0 0 86 86" aria-hidden="true">
          <defs>
            <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#2563eb"/>
              <stop offset="100%" stop-color="#7c3aed"/>
            </linearGradient>
          </defs>
          <circle class="track" cx="43" cy="43" r="36" fill="none" stroke-width="9"/>
          <circle class="fill" id="masteryRing" cx="43" cy="43" r="36" fill="none" stroke-width="9"
                  stroke-dasharray="226.2" stroke-dashoffset="226.2"/>
        </svg>
        <div>
          <div class="metric" style="border:none;background:none;padding:0">
            <strong>Mastery</strong><div id="mastery">0%</div>
          </div>
        </div>
      </div>
      <div class="mastery-bar" aria-hidden="true"><div id="masteryBar" style="width:0%"></div></div>
      <div class="progress">
        <div class="metric"><strong>Independent</strong><div id="independent">0 / 0</div></div>
        <div class="metric"><strong>Assisted successes</strong><div id="assisted">0</div></div>
      </div>
      <p class="muted" style="font-size:.85rem">Help can support learning, but assisted success is not counted as independent mastery evidence.</p>
    </section>
  </div>
</main>
<script>
const sessionId = "{session_id}";
const workspaceUrl = `/api/v1/learner-workspace/sessions/${{sessionId}}`;
const adaptiveUrl = `/api/v1/adaptive-tutor/sessions/${{sessionId}}`;
const q = id => document.getElementById(id);
let workspace = null;

function friendly(value) {{
  return String(value || '').replaceAll('_', ' ').toLowerCase().replace(/(^|\s)\S/g, c => c.toUpperCase());
}}
function setError(message = '') {{ q('error').textContent = message; }}
function setStatus(message = '', success = false) {{
  q('status').textContent = message;
  q('status').className = success ? 'success' : '';
}}
async function jsonRequest(url, options = {{}}) {{
  const response = await fetch(url, {{credentials: 'same-origin', ...options}});
  if (response.status === 401) {{
    window.location.assign(`/login?next=/learn/${{sessionId}}`);
    throw new Error('Authentication required');
  }}
  let body = null;
  try {{ body = await response.json(); }} catch (_) {{}}
  if (!response.ok) throw new Error(body?.detail || `${{response.status}} ${{response.statusText}}`);
  return body;
}}
function hasAction(action) {{ return workspace?.allowed_actions?.includes(action); }}

const STEP_ORDER = ['DIAGNOSE', 'GUIDED_PRACTICE', 'INDEPENDENT_PRACTICE', 'MASTERY_CHECK', 'COMPLETE'];
const STEP_ALIAS = {{ REMEDIATION: 'GUIDED_PRACTICE', REVIEW: 'DIAGNOSE' }};

function renderStepper(state) {{
  const effective = STEP_ALIAS[state] || state;
  const activeIndex = STEP_ORDER.indexOf(effective);
  for (const step of document.querySelectorAll('#stepper .step')) {{
    const index = STEP_ORDER.indexOf(step.dataset.state);
    step.classList.toggle('active', index === activeIndex);
    step.classList.toggle('done', index < activeIndex);
  }}
}}

function render(data) {{
  workspace = data;
  const complete = data.state === 'COMPLETE';
  q('title').textContent = `${{data.learner.first_name}} · Grade ${{data.learner.grade_level}}`;
  q('curriculum').textContent = [data.curriculum.jurisdiction, data.curriculum.name].filter(Boolean).join(' · ');
  q('state').textContent = friendly(data.state);
  q('skill').textContent = data.focus.skill_name;
  renderStepper(data.state);
  q('completionPanel').hidden = !complete;
  q('problemPanel').hidden = complete;
  q('problem').textContent = data.problem?.prompt || 'No problem is currently assigned.';
  q('coach').textContent = complete
    ? 'Nice work. Your independent mastery check is complete.'
    : (data.coaching_message || 'Work through the problem carefully.');
  q('independent').textContent = `${{data.evidence.independent_correct_count}} / ${{data.evidence.independent_attempt_count}}`;
  q('assisted').textContent = String(data.evidence.hinted_correct_count);
  const masteryPct = Math.round(data.evidence.mastery_score * 100);
  q('mastery').textContent = `${{masteryPct}}%`;
  q('masteryBar').style.width = `${{masteryPct}}%`;
  q('masteryRing').style.strokeDashoffset = String(226.2 * (1 - masteryPct / 100));

  const reviews = data.reviews_due || [];
  q('reviewBanner').hidden = reviews.length === 0;
  q('reviewList').textContent = reviews.map(r => r.skill_name).join(', ');
  q('nextSkill').textContent = data.recommended_next
    ? `Up next: ${{data.recommended_next.skill_name}}`
    : '';
  q('submitBtn').hidden = !hasAction('SUBMIT_ANSWER') || !data.problem;
  q('hintBtn').hidden = !hasAction('REQUEST_HINT') || !data.problem;
  q('struggleBtn').hidden = !hasAction('I_DONT_UNDERSTAND') || !data.problem;
  q('answer').disabled = !hasAction('SUBMIT_ANSWER') || !data.problem;
}}

async function loadWorkspace() {{
  render(await jsonRequest(workspaceUrl));
}}

async function requestHelp(reason) {{
  if (!workspace?.problem) return;
  setError(); setStatus('');
  const result = await jsonRequest(`${{adaptiveUrl}}/hint`, {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{problem_id: workspace.problem.id, reason}}),
  }});
  setStatus(result.message || 'Support is not available in this learning state.', result.allowed);
  await loadWorkspace();
}}

q('answerForm').addEventListener('submit', async event => {{
  event.preventDefault();
  if (!workspace?.problem) return;
  try {{
    setError(); setStatus('Checking your work…');
    const result = await jsonRequest(`${{adaptiveUrl}}/respond`, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        problem_id: workspace.problem.id,
        answer: q('answer').value,
        assistance_level: 0,
      }}),
    }});
    q('answer').value = '';
    q('problem').classList.remove('correct', 'wrong');
    void q('problem').offsetWidth;
    q('problem').classList.add(result.evaluation.correct ? 'correct' : 'wrong');
    setStatus(result.evaluation.correct ? 'Correct. Keep going.' : 'Not yet. Use the feedback and try the next step.', result.evaluation.correct);
    await loadWorkspace();
  }} catch (error) {{ setError(error.message); setStatus(''); }}
}});
q('hintBtn').addEventListener('click', async () => {{
  try {{ await requestHelp('HINT'); }} catch (error) {{ setError(error.message); }}
}});
q('struggleBtn').addEventListener('click', async () => {{
  try {{ await requestHelp('I_DONT_UNDERSTAND'); }} catch (error) {{ setError(error.message); }}
}});
q('signOut').addEventListener('click', async event => {{
  event.preventDefault();
  try {{ await jsonRequest('/api/v1/auth/logout', {{method: 'POST'}}); }} catch (_) {{}}
  window.location.assign('/login');
}});

(async () => {{
  try {{ await loadWorkspace(); }}
  catch (error) {{ setError(`This learning session is unavailable: ${{error.message}}`); }}
}})();
</script>
</body>
</html>"""
