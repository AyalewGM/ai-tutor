from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["parent-web"])


@router.get("/parent", response_class=HTMLResponse, include_in_schema=False)
def parent_dashboard_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Tutor Parent Dashboard</title>
  <style>
    :root { font-family: system-ui, sans-serif; color-scheme: light dark; }
    body { margin: 0; background: Canvas; color: CanvasText; }
    main { max-width: 1040px; margin: auto; padding: 1rem; }
    header, .panel { border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }
    .toolbar { display: flex; gap: .75rem; flex-wrap: wrap; align-items: end; }
    label { display: grid; gap: .35rem; font-weight: 600; }
    input, select, button { font: inherit; padding: .65rem; border-radius: 8px; border: 1px solid color-mix(in srgb, CanvasText 28%, transparent); }
    button { cursor: pointer; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: .75rem; }
    .card { border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 10px; padding: .8rem; }
    .muted { opacity: .72; }
    .error { color: #b42318; white-space: pre-wrap; }
    ul { padding-left: 1.25rem; }
    @media (max-width: 600px) { main { padding: .65rem; } .toolbar > * { width: 100%; } }
  </style>
</head>
<body>
<main>
  <header>
    <h1>Parent Dashboard</h1>
    <p class="muted">View each linked child's progress. Curriculum and learning decisions are read-only here.</p>
    <div id="profile" class="muted">Loading parent profile…</div>
  </header>

  <section class="panel">
    <div class="toolbar">
      <label>Child<select id="childSelect"><option value="">Select a child</option></select></label>
      <button id="refreshBtn" type="button">Refresh progress</button>
      <button id="unlinkBtn" type="button">Remove selected child</button>
    </div>
  </section>

  <section class="panel">
    <h2>Add a child</h2>
    <p class="muted">Enter the one-time link code provided by the application. A child cannot be linked by UUID.</p>
    <form id="linkForm" class="toolbar">
      <label>One-time link code<input id="claimToken" minlength="16" required autocomplete="off"></label>
      <button type="submit">Link child</button>
    </form>
  </section>

  <p id="error" class="error" role="alert"></p>
  <section id="dashboard" hidden>
    <div class="panel"><h2 id="childTitle"></h2><div id="context" class="muted"></div><p><strong>Active skill:</strong> <span id="activeSkill">None</span></p></div>
    <div class="panel"><h2>Skill progress</h2><div id="skills" class="grid"></div></div>
    <div class="panel"><h2>Recent activity</h2><ul id="activity"></ul></div>
    <div class="panel"><h2>Areas needing support</h2><ul id="support"></ul></div>
  </section>
</main>
<script>
const api = '/api/v1/parents';
const q = id => document.getElementById(id);

async function request(path, options = {}) {
  const response = await fetch(api + path, {credentials: 'same-origin', ...options});
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try { const body = await response.json(); detail = body.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

function showError(error) { q('error').textContent = error ? error.message : ''; }

async function loadProfile() {
  const p = await request('/profile');
  q('profile').textContent = `${p.display_name || p.email} · ${p.email}`;
}

async function loadChildren(preferredId) {
  const children = await request('/children');
  const select = q('childSelect');
  const current = preferredId || select.value;
  select.innerHTML = '<option value="">Select a child</option>';
  for (const child of children) {
    const option = document.createElement('option');
    option.value = child.id;
    option.textContent = `${child.first_name} · Grade ${child.grade_level}`;
    select.appendChild(option);
  }
  if (children.some(c => c.id === current)) select.value = current;
  else if (children.length) select.value = children[0].id;
  if (select.value) await loadDashboard(select.value); else q('dashboard').hidden = true;
}

async function loadDashboard(studentId) {
  if (!studentId) { q('dashboard').hidden = true; return; }
  const d = await request(`/children/${studentId}/dashboard`);
  q('dashboard').hidden = false;
  q('childTitle').textContent = `${d.child.first_name} · Grade ${d.child.grade_level}`;
  q('context').textContent = [d.child.jurisdiction, d.child.curriculum_name, d.child.school_system].filter(Boolean).join(' · ');
  q('activeSkill').textContent = d.active_skill_name || 'None';
  q('skills').innerHTML = d.skills.length ? d.skills.map(s => `<article class="card"><strong>${escapeHtml(s.skill_name)}</strong><p>${escapeHtml(friendlyStatus(s.status))}</p><small>Independent: ${s.independent_correct_count}/${s.independent_attempt_count} · Assisted successes: ${s.hinted_correct_count}</small></article>`).join('') : '<p class="muted">No skill progress recorded yet.</p>';
  q('activity').innerHTML = d.recent_activity.length ? d.recent_activity.map(a => `<li>${escapeHtml(a.skill_name)} — ${escapeHtml(friendlyStatus(a.state))}</li>`).join('') : '<li class="muted">No recent activity.</li>';
  q('support').innerHTML = d.support_areas.length ? d.support_areas.map(a => `<li>${escapeHtml(a.name)}</li>`).join('') : '<li class="muted">No current support areas recorded.</li>';
}

function friendlyStatus(value) {
  return String(value || '').replaceAll('_', ' ').split(' ').filter(Boolean).map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
}
function escapeHtml(value) {
  const div = document.createElement('div'); div.textContent = value ?? ''; return div.innerHTML;
}

q('childSelect').addEventListener('change', async e => { try { showError(); await loadDashboard(e.target.value); } catch (err) { showError(err); } });
q('refreshBtn').addEventListener('click', async () => { try { showError(); await loadChildren(q('childSelect').value); } catch (err) { showError(err); } });
q('unlinkBtn').addEventListener('click', async () => {
  const id = q('childSelect').value; if (!id || !confirm('Remove this child from your dashboard? Learning history will be preserved.')) return;
  try { showError(); await request(`/children/${id}`, {method: 'DELETE'}); await loadChildren(); } catch (err) { showError(err); }
});
q('linkForm').addEventListener('submit', async e => {
  e.preventDefault();
  try {
    showError();
    const linked = await request('/children/link', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({claim_token: q('claimToken').value})});
    q('claimToken').value = '';
    await loadChildren(linked.child.id);
  } catch (err) { showError(err); }
});

(async () => {
  try { await loadProfile(); await loadChildren(); }
  catch (err) { showError(new Error(`Parent access is not available: ${err.message}`)); }
})();
</script>
</body>
</html>"""
