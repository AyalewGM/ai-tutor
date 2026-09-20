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
      --focus: #1d4ed8;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: #f7f8fc; color: #172033; }
    main { max-width: 1120px; margin: auto; padding: 1.25rem; }
    header.hero {
      color: white;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      border-radius: 18px;
      padding: 1.4rem;
      margin-bottom: 1rem;
      box-shadow: 0 12px 30px rgba(79, 70, 229, .18);
    }
    header.hero h1 { margin: 0 0 .35rem; font-size: clamp(1.7rem, 4vw, 2.3rem); }
    header.hero p { margin: .25rem 0; color: rgba(255,255,255,.9); }
    .panel { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem; margin-bottom: 1rem; }
    .toolbar { display: flex; gap: .75rem; flex-wrap: wrap; align-items: end; }
    label { display: grid; gap: .35rem; font-weight: 650; }
    input, select, button { font: inherit; min-height: 44px; padding: .65rem .8rem; border-radius: 10px; border: 1px solid #c9cfdd; }
    input:focus-visible, select:focus-visible, button:focus-visible, summary:focus-visible { outline: 3px solid color-mix(in srgb, var(--focus) 36%, transparent); outline-offset: 2px; }
    button { cursor: pointer; background: var(--surface); color: #172033; font-weight: 650; }
    button.primary { color: #fff; border-color: transparent; background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-indigo)); }
    button.danger { color: var(--danger); }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: .75rem; }
    .summary-card { background: var(--surface-soft); border: 1px solid #e2e4f6; border-radius: 12px; padding: .9rem; }
    .summary-card strong { display: block; font-size: 1.55rem; color: var(--goozam-indigo); margin-top: .2rem; }
    .summary-card span { color: var(--muted); font-size: .9rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(225px, 1fr)); gap: .75rem; }
    .card { border: 1px solid var(--border); border-radius: 12px; padding: .9rem; background: #fff; }
    .card .state { font-weight: 700; color: var(--goozam-indigo); }
    .card small { color: var(--muted); }
    .next-step { margin: .7rem 0 0; padding: .65rem .75rem; background: var(--surface-soft); border-radius: 8px; }
    details { margin-top: .65rem; }
    details summary { cursor: pointer; color: var(--goozam-indigo); font-weight: 650; min-height: 44px; display: flex; align-items: center; }
    .muted { color: var(--muted); }
    .error { color: var(--danger); white-space: pre-wrap; }
    .evidence-note { border-left: 4px solid var(--goozam-indigo); background: var(--surface-soft); padding: .7rem .8rem; border-radius: 8px; }
    ul { padding-left: 1.25rem; }
    @media (max-width: 600px) {
      main { padding: .7rem; }
      .toolbar > * { width: 100%; }
      header.hero { border-radius: 14px; }
    }
  </style>
</head>
<body>
<main>
  <header class="hero">
    <h1>Parent Dashboard</h1>
    <p>Clear, evidence-backed learning progress for each linked child.</p>\n    <p><a href="/parent/settings" style="color:white">Settings & privacy</a></p>
    <div id="profile">Loading parent profile…</div>
  </header>

  <section class="panel" aria-label="Child selection">
    <div class="toolbar">
      <label>Child<select id="childSelect"><option value="">Select a child</option></select></label>
      <button id="refreshBtn" class="primary" type="button">Refresh progress</button>
      <button id="unlinkBtn" class="danger" type="button">Remove selected child</button>
    </div>
  </section>

  <section class="panel">
    <h2>Add a child</h2>
    <p class="muted">Enter the one-time link code provided by the application. A child cannot be linked by UUID.</p>
    <form id="linkForm" class="toolbar">
      <label>One-time link code<input id="claimToken" minlength="16" required autocomplete="off"></label>
      <button class="primary" type="submit">Link child</button>
    </form>
  </section>

  <p id="error" class="error" role="alert" aria-live="assertive"></p>
  <section id="dashboard" hidden>
    <div class="panel">
      <h2 id="childTitle"></h2>
      <div id="context" class="muted"></div>
      <p><strong>Current focus:</strong> <span id="activeSkill">None</span></p>
      <p><strong>Recommended next:</strong> <span id="recommendedNext">None</span></p>
      <p class="evidence-note">Progress below distinguishes assisted work from independent evidence. Limited observations are shown as insufficient evidence rather than as a weakness.</p>
    </div>

    <section class="panel" id="reviewsPanel" aria-labelledby="reviewsHeading" hidden>
      <h2 id="reviewsHeading">Reviews due</h2>
      <p class="muted">Previously mastered skills due for a quick retention check. Projected mastery reflects time since the last independent evidence.</p>
      <ul id="reviews"></ul>
    </section>

    <section class="panel" aria-labelledby="summaryHeading">
      <h2 id="summaryHeading">Learning summary</h2>
      <div id="summary" class="summary"></div>
    </section>

    <section class="panel" aria-labelledby="skillsHeading">
      <h2 id="skillsHeading">Skill progress and next steps</h2>
      <div id="skills" class="grid"></div>
    </section>

    <section class="panel" aria-labelledby="activityHeading">
      <h2 id="activityHeading">Recent activity</h2>
      <ul id="activity"></ul>
    </section>

    <section class="panel" aria-labelledby="supportHeading">
      <h2 id="supportHeading">Current support areas</h2>
      <ul id="support"></ul>
    </section>
  </section>
</main>
<script>
const api = '/api/v1/parents';
const q = id => document.getElementById(id);

async function request(path, options = {}) {
  const response = await fetch(api + path, {credentials: 'same-origin', ...options});
  if (response.status === 401) {
    window.location.assign('/login?next=/parent');
    throw new Error('Authentication required');
  }
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

function summaryCounts(skills) {
  return {
    mastered: skills.filter(s => s.learning_state === 'INDEPENDENT_MASTERY').length,
    independent: skills.filter(s => s.learning_state === 'INDEPENDENT_PROGRESS').length,
    assisted: skills.filter(s => s.learning_state === 'ASSISTED_SUCCESS').length,
    insufficient: skills.filter(s => s.evidence_status === 'INSUFFICIENT_EVIDENCE').length,
  };
}

function renderSummary(skills) {
  const counts = summaryCounts(skills);
  const items = [
    ['Independent mastery', counts.mastered],
    ['Independent progress', counts.independent],
    ['Assisted success', counts.assisted],
    ['Insufficient evidence', counts.insufficient],
  ];
  q('summary').innerHTML = items.map(([label, value]) => `<article class="summary-card"><span>${escapeHtml(label)}</span><strong>${value}</strong></article>`).join('');
}

function actionText(code) {
  const actions = {
    COLLECT_MORE_EVIDENCE: 'Continue normal practice so the tutor can collect enough evidence.',
    CONTINUE_CURRENT_LEARNING: 'Continue the current learning plan without drawing a negative conclusion.',
    ENCOURAGE_INDEPENDENT_ATTEMPT: 'Encourage a fresh independent attempt when the tutor presents one.',
    RECOGNIZE_INDEPENDENT_PROGRESS: 'Recognize the independent progress and continue the tutor plan.',
    RECOGNIZE_MASTERY: 'Celebrate the independently demonstrated mastery.',
    FOLLOW_EXISTING_REVIEW_PLAN: 'Follow the review already scheduled by the tutoring engine.',
  };
  return actions[code] || 'Continue the tutor plan.';
}

function skillCard(skill) {
  return `<article class="card">
    <strong>${escapeHtml(skill.skill_name)}</strong>
    <p class="state">${escapeHtml(friendlyStatus(skill.learning_state))}</p>
    <p class="next-step"><strong>Suggested next step:</strong> ${escapeHtml(actionText(skill.action_code))}</p>
    <details><summary>View supporting evidence</summary>
      <small>Independent: ${skill.independent_correct_count}/${skill.independent_attempt_count} · Assisted successes: ${skill.hinted_correct_count} · Evidence: ${escapeHtml(friendlyStatus(skill.evidence_status))} · Reason: ${escapeHtml(friendlyStatus(skill.reason_code))}</small>
    </details>
  </article>`;
}

async function loadDashboard(studentId) {
  if (!studentId) { q('dashboard').hidden = true; return; }
  const d = await request(`/children/${studentId}/dashboard`);
  q('dashboard').hidden = false;
  q('childTitle').textContent = `${d.child.first_name} · Grade ${d.child.grade_level}`;
  q('context').textContent = [d.child.jurisdiction, d.child.curriculum_name, d.child.school_system].filter(Boolean).join(' · ');
  q('activeSkill').textContent = d.active_skill_name || 'None';
  q('recommendedNext').textContent = d.recommended_next
    ? `${d.recommended_next.skill_name} (${friendlyStatus(d.recommended_next.reason)})`
    : 'None';
  const reviews = d.reviews_due || [];
  q('reviewsPanel').hidden = reviews.length === 0;
  q('reviews').innerHTML = reviews.map(r => `<li><strong>${escapeHtml(r.skill_name)}</strong> — ${escapeHtml(r.status)} · mastery ${Math.round(r.mastery_score * 100)}% → projected ${Math.round(r.projected_mastery_score * 100)}%</li>`).join('');
  renderSummary(d.skills);
  q('skills').innerHTML = d.skills.length ? d.skills.map(skillCard).join('') : '<p class="muted">No skill progress recorded yet.</p>';
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
