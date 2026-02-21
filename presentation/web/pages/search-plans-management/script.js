const planForm = document.getElementById("plan-form");
const queryInput = document.getElementById("plan-query");
const sourceInput = document.getElementById("plan-source");
const keywordsInput = document.getElementById("plan-keywords");
const negativeInput = document.getElementById("plan-negative");
const plansList = document.getElementById("plans-list");
const resultsList = document.getElementById("results-list");

let selectedPlanId = null;

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

function renderPlans(plans) {
  plansList.innerHTML = plans
    .map(
      (plan) => `
      <li class="plan-item">
        <div><strong>${plan.query}</strong></div>
        <div>source: ${plan.source_type} | keywords: ${(plan.keywords || []).map((k) => k.keyword).join(", ")}</div>
        <div><span class="chip ${stateClass(plan.status)}">${plan.status}</span></div>
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
  queryInput.value = "";
  keywordsInput.value = "";
  negativeInput.value = "";
  await loadPlans();
});

async function runPlan(id) {
  await api(`/search-plans/${id}/run`, { method: "POST" });
  await loadPlans();
}

async function approvePlan(id) {
  const reason = window.prompt("Reason (optional):") || null;
  await api(`/search-plans/${id}/approve`, { method: "POST", body: JSON.stringify({ reason }) });
  await loadPlans();
}

async function rejectPlan(id) {
  const reason = window.prompt("Reason for reject:") || "rejected by reviewer";
  await api(`/search-plans/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) });
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
