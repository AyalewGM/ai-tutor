import uuid

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["learner-web"])


@router.get("/learn/{session_id}", response_class=HTMLResponse, include_in_schema=False)
def learner_workspace_page(session_id: uuid.UUID) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Tutor Learning Session</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; color-scheme: light dark; }}
    body {{ margin: 0; background: Canvas; color: CanvasText; }}
    main {{ max-width: 860px; margin: auto; padding: 1rem; }}
    .panel {{ border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 14px; padding: 1rem; margin-bottom: 1rem; }}
    .meta {{ display: flex; gap: .6rem; flex-wrap: wrap; align-items: center; }}
    .chip {{ border: 1px solid color-mix(in srgb, CanvasText 22%, transparent); border-radius: 999px; padding: .3rem .65rem; font-size: .9rem; }}
    .problem {{ font-size: 1.25rem; line-height: 1.5; white-space: pre-wrap; }}
    .coach {{ border-left: 4px solid currentColor; padding-left: .8rem; line-height: 1.5; }}
    .actions {{ display: flex; gap: .65rem; flex-wrap: wrap; }}
    input, button {{ font: inherit; padding: .75rem; border-radius: 9px; border: 1px solid color-mix(in srgb, CanvasText 28%, transparent); }}
    input {{ width: min(100%, 34rem); box-sizing: border-box; }}
    button {{ cursor: pointer; min-height: 44px; }}
    button[hidden] {{ display: none; }}
    .muted {{ opacity: .72; }}
    .error {{ color: #b42318; white-space: pre-wrap; }}
    .success {{ color: #067647; }}
    .progress {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: .7rem; }}
    .metric {{ border: 1px solid color-mix(in srgb, CanvasText 15%, transparent); border-radius: 10px; padding: .75rem; }}
    :focus-visible {{ outline: 3px solid Highlight; outline-offset: 3px; }}
    @media (max-width: 600px) {{ main {{ padding: .65rem; }} .actions button {{ flex: 1 1 100%; }} }}
  </style>
</head>
<body>
<main>
  <header class="panel">
    <h1 id="title">Learning session</h1>
    <div class="meta">
      <span id="curriculum" class="chip"></span>
      <span id="state" class="chip"></span>
      <span id="skill" class="chip"></span>
    </div>
  </header>

  <p id="error" class="error" role="alert" aria-live="assertive"></p>
  <p id="status" role="status" aria-live="polite"></p>

  <section class="panel" aria-labelledby="problemHeading">
    <h2 id="problemHeading">Current problem</h2>
    <div id="problem" class="problem">Loading…</div>
    <form id="answerForm">
      <label for="answer"><strong>Your answer</strong></label><br>
      <input id="answer" name="answer" autocomplete="off" required>
      <div class="actions" style="margin-top:.75rem">
        <button id="submitBtn" type="submit">Submit answer</button>
        <button id="hintBtn" type="button" hidden>Hint</button>
        <button id="struggleBtn" type="button" hidden>I don't understand</button>
      </div>
    </form>
  </section>

  <section class="panel" aria-labelledby="coachHeading">
    <h2 id="coachHeading">Coach</h2>
    <p id="coach" class="coach muted">Loading coaching context…</p>
  </section>

  <section class="panel" aria-labelledby="progressHeading">
    <h2 id="progressHeading">Your progress</h2>
    <div class="progress">
      <div class="metric"><strong>Independent</strong><div id="independent">0 / 0</div></div>
      <div class="metric"><strong>Assisted successes</strong><div id="assisted">0</div></div>
      <div class="metric"><strong>Mastery</strong><div id="mastery">0%</div></div>
    </div>
    <p class="muted">Help can support learning, but assisted success is not counted as independent mastery evidence.</p>
  </section>
</main>
<script>
const sessionId = {session_id!r};
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
  let body = null;
  try {{ body = await response.json(); }} catch (_) {{}}
  if (!response.ok) throw new Error(body?.detail || `${{response.status}} ${{response.statusText}}`);
  return body;
}}
function hasAction(action) {{ return workspace?.allowed_actions?.includes(action); }}

function render(data) {{
  workspace = data;
  q('title').textContent = `${{data.learner.first_name}} · Grade ${{data.learner.grade_level}}`;
  q('curriculum').textContent = [data.curriculum.jurisdiction, data.curriculum.name].filter(Boolean).join(' · ');
  q('state').textContent = friendly(data.state);
  q('skill').textContent = data.focus.skill_name;
  q('problem').textContent = data.problem?.prompt || 'No problem is currently assigned.';
  q('coach').textContent = data.coaching_message || 'Work through the problem carefully.';
  q('independent').textContent = `${{data.evidence.independent_correct_count}} / ${{data.evidence.independent_attempt_count}}`;
  q('assisted').textContent = String(data.evidence.hinted_correct_count);
  q('mastery').textContent = `${{Math.round(data.evidence.mastery_score * 100)}}%`;
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

(async () => {{
  try {{ await loadWorkspace(); }}
  catch (error) {{ setError(`This learning session is unavailable: ${{error.message}}`); }}
}})();
</script>
</body>
</html>"""
