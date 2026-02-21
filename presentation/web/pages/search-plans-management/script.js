const planForm = document.getElementById("plan-form");
const queryInput = document.getElementById("plan-query");
const sourceInput = document.getElementById("plan-source");
const keywordsInput = document.getElementById("plan-keywords");
const negativeInput = document.getElementById("plan-negative");
const autoStartBtn = document.getElementById("auto-start-btn");
const plansList = document.getElementById("plans-list");
const resultsList = document.getElementById("results-list");

let selectedPlanId = null;
const planProgress = new Map();

function splitCsv(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function stateClass(status) {
  if (status === "approved") return "state-success";
  if (status === "rejected") return "state-danger";
  if (status === "review_pending") return "state-info";
  if (status === "running") return "state-warning";
  return "state-warning";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.message || "request failed");
  }
  return payload.data;
}

async function loadPlans() {
  const plans = await api("/search-plans");
  renderPlans(plans);
  if (selectedPlanId) {
    await loadResults(selectedPlanId);
  }
}

function renderProgress(planId) {
  const progress = planProgress.get(planId);
  if (!progress) return "<div>progress: waiting</div>";
  const pct = progress.progress_percent ?? 0;
  const keyword = progress.keyword ? ` | keyword: ${progress.keyword}` : "";
  return `<div>progress: ${pct}% | found: ${progress.total_found ?? 0} | enqueued: ${progress.total_enqueued ?? 0}${keyword}</div>`;
}

function renderPlans(plans) {
  plansList.innerHTML = plans
    .map(
      (plan) => `
      <li class="plan-item">
        <div><strong>${plan.query}</strong></div>
        <div>source: ${plan.source_type} | keywords: ${(plan.keywords || []).map((k) => k.keyword).join(", ")}</div>
        <div><span class="chip ${stateClass(plan.status)}">${plan.status}</span></div>
        ${renderProgress(plan.id)}
        <div class="plan-actions">
          <button class="button" onclick="runPlan('${plan.id}')">Run</button>
          <button class="button" onclick="showResults('${plan.id}')">Review Results</button>
          <button class="button" onclick="approvePlan('${plan.id}')">Approve Plan</button>
          <button class="button" onclick="rejectPlan('${plan.id}')">Reject Plan</button>
        </div>
      </li>
    `,
    )
    .join("");
}

async function showResults(planId) {
  selectedPlanId = planId;
  await loadResults(planId);
}

async function loadResults(planId) {
  const results = await api(`/search-plans/${planId}/results`);
  resultsList.innerHTML = results
    .map(
      (result) => `
      <li class="plan-item">
        <div><strong>${result.title || "No title"}</strong></div>
        <div>${result.source_url || "-"}</div>
        <div>keyword: ${result.query_keyword || "-"}</div>
        <div><span class="chip ${stateClass(result.status)}">${result.status}</span></div>
        <div class="plan-actions">
          <button class="button" onclick="approveResult('${result.id}')">Approve Result</button>
          <button class="button" onclick="rejectResult('${result.id}')">Reject Result</button>
        </div>
      </li>
    `,
    )
    .join("");
}

async function syncProgress() {
  const events = await api("/events/tail?limit=50");
  for (const event of events) {
    if (!event.event_type.startsWith("search_plan.run.")) continue;
    const payload = event.payload || {};
    const planId = payload.search_plan_id || event.aggregate_id;
    if (!planId) continue;
    planProgress.set(planId, payload);
  }
  await loadPlans();
}

planForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await api("/search-plans", {
    method: "POST",
    body: JSON.stringify({
      query: queryInput.value,
      source_type: sourceInput.value,
      keywords: splitCsv(keywordsInput.value),
      negative_keywords: splitCsv(negativeInput.value),
    }),
  });
  keywordsInput.value = "";
  negativeInput.value = "";
  await loadPlans();
});

autoStartBtn.addEventListener("click", async () => {
  await api("/search-plans/auto-start", {
    method: "POST",
    body: JSON.stringify({
      query: queryInput.value,
      seed_keywords: splitCsv(keywordsInput.value),
    }),
  });
  keywordsInput.value = "";
  negativeInput.value = "";
  await loadPlans();
});

async function runPlan(id) {
  await api(`/search-plans/${id}/run`, { method: "POST" });
  await loadPlans();
}

async function approvePlan(id) {
  await api(`/search-plans/${id}/approve`, { method: "POST", body: JSON.stringify({ reason: null }) });
  await loadPlans();
}

async function rejectPlan(id) {
  await api(`/search-plans/${id}/reject`, { method: "POST", body: JSON.stringify({ reason: "rejected" }) });
  await loadPlans();
}

async function approveResult(id) {
  const reason = window.prompt("Reason (optional):") || null;
  await api(`/search-results/${id}/approve`, { method: "POST", body: JSON.stringify({ reason }) });
  if (selectedPlanId) await loadResults(selectedPlanId);
}

async function rejectResult(id) {
  const reason = window.prompt("Reason for reject:") || "rejected by reviewer";
  await api(`/search-results/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) });
  if (selectedPlanId) await loadResults(selectedPlanId);
}

window.runPlan = runPlan;
window.showResults = showResults;
window.approvePlan = approvePlan;
window.rejectPlan = rejectPlan;
window.approveResult = approveResult;
window.rejectResult = rejectResult;

loadPlans().catch((err) => {
  plansList.innerHTML = `<li class="plan-item">Erro ao carregar: ${err.message}</li>`;
});
setInterval(() => {
  syncProgress().catch(() => {});
}, 2500);
