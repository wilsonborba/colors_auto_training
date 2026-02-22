const planId = new URLSearchParams(window.location.search).get("id");
const el = (id) => document.getElementById(id);
async function api(path, options = {}) { const r = await fetch(path, { headers: {"Content-Type":"application/json"}, ...options }); const p = await r.json(); if(!r.ok) throw new Error(p.message||"request failed"); return p.data; }
function pct(plan){const total=plan.total_keywords||0; const idx=plan.current_keyword_index||0; return total?Math.min(100,Math.round((idx/total)*100)):0;}
async function load(){
  const plan = await api(`/search-plans/${planId}`);
  el("header").innerHTML = `<h2>${plan.query}</h2><div>Status: <span class="chip">${plan.status}</span></div><div>source: ${plan.source_type} | created: ${plan.created_at} | keywords: ${plan.total_keywords||plan.keywords.length}</div>`;
  el("keywords").innerHTML = plan.keywords.map((k,i)=>`<div class="kw">#${i+1} ${k.keyword} ${k.is_negative?"(negative)":""}</div>`).join("");
  const progress = pct(plan);
  el("execution").innerHTML = `<div class="progress"><div class="bar" style="width:${progress}%"></div></div><div>${plan.current_keyword_index||0}/${plan.total_keywords||plan.keywords.length}</div><div>Searching keyword ${plan.current_keyword_index||0}/${plan.total_keywords||plan.keywords.length}: ${plan.current_keyword_text||"-"}</div><div>Started: ${plan.started_at||"-"} | Updated: ${plan.updated_at}</div>`;
  const results = await api(`/search-plans/${planId}/results`);
  el("results").innerHTML = results.map((r)=>`<div class="kw"><label><input class="result-check" type="checkbox" value="${r.id}"/> <b>${r.title||"No title"}</b></label><br>${r.source_url||"-"}<br>keyword:${r.query_keyword||"-"} | ${r.status}<br><button class="button" onclick="approveResult('${r.id}')">Approve</button> <button class="button" onclick="rejectResult('${r.id}')">Reject</button></div>`).join("");
  const events = await api(`/search-plans/${planId}/events/tail?limit=100`);
  el("events").innerHTML = events.map((ev)=>`<li>${ev.ts||ev.created_at} | ${ev.event_type} | ${JSON.stringify(ev.payload||{})}</li>`).join("");
}
async function approveResult(id){await api(`/search-results/${id}/approve`,{method:"POST",body:JSON.stringify({reason:null})}); await load();}
async function rejectResult(id){await api(`/search-results/${id}/reject`,{method:"POST",body:JSON.stringify({reason:"rejected by user"})}); await load();}
window.approveResult=approveResult; window.rejectResult=rejectResult;
load(); setInterval(()=>load().catch(()=>{}), 3000);

async function bulkReview(approved){ const ids=[...document.querySelectorAll(".result-check:checked")].map((e)=>e.value); if(!ids.length) return; if(!window.confirm(`Apply to ${ids.length} result(s)?`)) return; await api(`/search-plans/${planId}/results/bulk`, {method:"POST", body: JSON.stringify({result_ids: ids, approved, reason: approved?null:"bulk reject"})}); await load(); }
window.bulkReview=bulkReview;
