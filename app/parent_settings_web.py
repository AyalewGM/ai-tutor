from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["parent-web"])


@router.get("/parent/settings", response_class=HTMLResponse, include_in_schema=False)
def parent_settings_page() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Parent Settings</title>
<style>
body{font-family:system-ui,sans-serif;color:#172033;background:#f7f8fc}main{max-width:720px;margin:auto;padding:1rem}.panel{background:white;border:1px solid #dfe3ef;border-radius:12px;padding:1rem;margin:1rem 0}button,input{font:inherit;min-height:44px;padding:.6rem;border-radius:8px;border:1px solid #c9cfdd}.danger{color:#b42318}.muted{color:#667085}.error{color:#b42318}
</style></head>
<body><main><h1>Parent Settings</h1><p><a href="/parent">Back to dashboard</a></p>
<section class="panel"><h2>Profile</h2><form id="profileForm"><label>Display name <input id="displayName" required minlength="1" maxlength="120"></label> <button type="submit">Save</button></form><p id="email"></p></section>
<section class="panel" aria-labelledby="privacyHeading"><h2 id="privacyHeading">Privacy & family data</h2>
<p id="notice" class="muted">Loading privacy notice…</p><button id="ackBtn" type="button" hidden>Acknowledge current notice</button>
<p id="dataSummary" class="muted"></p>
<h3>Delete a learner's data</h3><p>This permanently deletes the selected learner and their tutoring/progress evidence. This is different from removing a child from your dashboard. Shared curriculum content is not deleted.</p>
<label>Learner <select id="learnerSelect"><option value="">Select a learner</option></select></label>
<p><label>Type DELETE to confirm <input id="deleteConfirm" autocomplete="off"></label> <button id="deleteBtn" class="danger" type="button">Permanently delete learner data</button></p>
</section>
<p id="status" role="status"></p><p id="error" class="error" role="alert"></p>
<script>
async function jsonRequest(url, options={}){const r=await fetch(url,{credentials:'same-origin',...options});if(!r.ok){let d=r.status+' '+r.statusText;try{const b=await r.json();d=b.detail||d}catch(_){}throw new Error(d)}if(r.status===204)return null;return r.json()}
async function profileRequest(options={}){return jsonRequest('/api/v1/parents/profile',options)}
async function loadPrivacy(){
 const n=await jsonRequest('/api/v1/privacy/notice'); document.getElementById('notice').textContent=n.title+': '+n.summary; document.getElementById('ackBtn').hidden=n.acknowledged;
 const s=await jsonRequest('/api/v1/privacy/data-summary'); document.getElementById('dataSummary').textContent='Active learners: '+s.active_learner_count+'. Stored categories: '+s.stored_categories.join(', ')+'.';
 const children=await jsonRequest('/api/v1/parents/children'); const sel=document.getElementById('learnerSelect'); sel.innerHTML='<option value="">Select a learner</option>'; for(const child of children){const o=document.createElement('option');o.value=child.id;o.textContent=child.first_name+' · Grade '+child.grade_level;sel.appendChild(o)}
}
(async()=>{try{const p=await profileRequest();document.getElementById('displayName').value=p.display_name||'';document.getElementById('email').textContent='Email: '+p.email;await loadPrivacy()}catch(e){document.getElementById('error').textContent=e.message}})();
document.getElementById('profileForm').addEventListener('submit',async e=>{e.preventDefault();try{const p=await profileRequest({method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:document.getElementById('displayName').value})});document.getElementById('status').textContent='Saved as '+p.display_name}catch(err){document.getElementById('error').textContent=err.message}});
document.getElementById('ackBtn').addEventListener('click',async()=>{try{const n=await jsonRequest('/api/v1/privacy/notice');await jsonRequest('/api/v1/privacy/notice/acknowledge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({notice_version:n.version})});document.getElementById('status').textContent='Privacy notice acknowledged.';await loadPrivacy()}catch(e){document.getElementById('error').textContent=e.message}});
document.getElementById('deleteBtn').addEventListener('click',async()=>{const id=document.getElementById('learnerSelect').value;const confirmation=document.getElementById('deleteConfirm').value;if(!id){document.getElementById('error').textContent='Select a learner.';return}if(confirmation!=='DELETE'){document.getElementById('error').textContent='Type DELETE exactly to confirm.';return}if(!confirm('Permanently delete this learner and their learning evidence? This cannot be undone.'))return;try{await jsonRequest('/api/v1/privacy/learners/'+id,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmation:'DELETE'})});document.getElementById('deleteConfirm').value='';document.getElementById('status').textContent='Learner data deleted.';document.getElementById('error').textContent='';await loadPrivacy()}catch(e){document.getElementById('error').textContent=e.message}});
</script></main></body></html>"""
