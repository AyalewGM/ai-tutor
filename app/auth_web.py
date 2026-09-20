from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.learner_web import _DESIGN_TOKENS

router = APIRouter(tags=["auth-web"])


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Tutor — Sign in</title>
  <style>
""" + _DESIGN_TOKENS + """
    * { box-sizing: border-box; }
    body { margin: 0; background: #f7f8fc; color: #172033; }
    main { max-width: 520px; margin: auto; padding: 1.25rem; }
    header.hero {
      color: white;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-purple));
      border-radius: 18px;
      padding: 1.4rem;
      margin-bottom: 1rem;
      box-shadow: 0 12px 30px rgba(79, 70, 229, .18);
      text-align: center;
    }
    header.hero h1 { margin: 0 0 .35rem; font-size: clamp(1.6rem, 4vw, 2.1rem); }
    header.hero p { margin: .25rem 0; color: rgba(255,255,255,.9); }
    .panel { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.1rem; }
    .tabs { display: flex; gap: .5rem; margin-bottom: 1rem; }
    .tabs button {
      flex: 1; min-height: 44px; border-radius: 10px; border: 1px solid var(--border);
      background: var(--surface-soft); color: var(--muted); font-weight: 650; cursor: pointer;
    }
    .tabs button.active {
      color: #fff; border-color: transparent;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-indigo));
    }
    label { display: block; margin-top: .8rem; font-weight: 650; }
    input, button { font: inherit; }
    input { width: 100%; box-sizing: border-box; min-height: 44px; padding: .75rem; border-radius: 10px; border: 1px solid #c9cfdd; }
    input:focus-visible, button:focus-visible { outline: 3px solid color-mix(in srgb, var(--focus) 36%, transparent); outline-offset: 2px; }
    button.primary {
      margin-top: 1.1rem; width: 100%; min-height: 44px; cursor: pointer; font-weight: 650;
      color: #fff; border: none; border-radius: 10px;
      background: linear-gradient(120deg, var(--goozam-blue), var(--goozam-indigo));
      box-shadow: 0 8px 18px rgba(37, 99, 235, .22);
    }
    button.primary:disabled { opacity: .55; cursor: default; }
    .error { color: var(--danger); white-space: pre-wrap; }
    .muted { color: var(--muted); font-size: .9rem; }
    form[hidden] { display: none; }
  </style>
</head>
<body>
<main>
  <header class="hero">
    <h1>AI Tutor</h1>
    <p>Adaptive math practice for your family.</p>
  </header>

  <section class="panel">
    <div class="tabs" role="tablist">
      <button id="loginTab" class="active" type="button" role="tab" aria-selected="true">Sign in</button>
      <button id="registerTab" type="button" role="tab" aria-selected="false">Create account</button>
    </div>

    <p id="error" class="error" role="alert" aria-live="assertive"></p>

    <form id="loginForm">
      <label for="loginEmail">Email</label>
      <input id="loginEmail" type="email" autocomplete="email" required>
      <label for="loginPassword">Password</label>
      <input id="loginPassword" type="password" autocomplete="current-password" required>
      <button class="primary" type="submit">Sign in</button>
    </form>

    <form id="registerForm" hidden>
      <label for="registerName">Display name</label>
      <input id="registerName" autocomplete="name">
      <label for="registerEmail">Email</label>
      <input id="registerEmail" type="email" autocomplete="email" required>
      <label for="registerPassword">Password</label>
      <input id="registerPassword" type="password" autocomplete="new-password" minlength="12" required>
      <p class="muted">Use at least 12 characters.</p>
      <button class="primary" type="submit">Create account</button>
    </form>
  </section>
</main>
<script>
const api = '/api/v1/auth';
const q = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const next = params.get('next') || '/learn';

function setError(message = '') { q('error').textContent = message; }

function selectTab(login) {
  q('loginForm').hidden = !login;
  q('registerForm').hidden = login;
  q('loginTab').classList.toggle('active', login);
  q('registerTab').classList.toggle('active', !login);
  q('loginTab').setAttribute('aria-selected', String(login));
  q('registerTab').setAttribute('aria-selected', String(!login));
  setError();
}
q('loginTab').addEventListener('click', () => selectTab(true));
q('registerTab').addEventListener('click', () => selectTab(false));

async function submit(path, body, button) {
  setError();
  button.disabled = true;
  try {
    const response = await fetch(api + path, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    let data = null;
    try { data = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(data?.detail || `${response.status} ${response.statusText}`);
    window.location.assign(next);
  } catch (failure) {
    setError(failure.message);
    button.disabled = false;
  }
}

q('loginForm').addEventListener('submit', e => {
  e.preventDefault();
  submit('/login', {
    email: q('loginEmail').value.trim(),
    password: q('loginPassword').value,
  }, e.submitter);
});
q('registerForm').addEventListener('submit', e => {
  e.preventDefault();
  submit('/register-parent', {
    email: q('registerEmail').value.trim(),
    password: q('registerPassword').value,
    display_name: q('registerName').value.trim() || null,
  }, e.submitter);
});
</script>
</body>
</html>"""
