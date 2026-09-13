from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["parent-web"])


@router.get("/parent/settings", response_class=HTMLResponse, include_in_schema=False)
def parent_settings_page() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Parent Settings</title></head>
<body><main style="max-width:640px;margin:auto;padding:1rem;font-family:system-ui,sans-serif">
<h1>Parent Settings</h1><p><a href="/parent">Back to dashboard</a></p>
<form id="profileForm"><label>Display name <input id="displayName" required minlength="1" maxlength="120"></label> <button type="submit">Save</button></form>
<p id="email"></p><p id="status" role="status"></p>
<script>
async function request(options = {}) {
  const response = await fetch('/api/v1/parents/profile', {credentials:'same-origin', ...options});
  if (!response.ok) { let detail = `${response.status} ${response.statusText}`; try { const b = await response.json(); detail = b.detail || detail; } catch (_) {} throw new Error(detail); }
  return response.json();
}
(async () => { try { const p = await request(); document.getElementById('displayName').value = p.display_name || ''; document.getElementById('email').textContent = `Email: ${p.email}`; } catch (e) { document.getElementById('status').textContent = e.message; } })();
document.getElementById('profileForm').addEventListener('submit', async e => { e.preventDefault(); const status = document.getElementById('status'); try { const p = await request({method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({display_name:document.getElementById('displayName').value})}); status.textContent = `Saved as ${p.display_name}`; } catch (err) { status.textContent = err.message; } });
</script></main></body></html>"""
