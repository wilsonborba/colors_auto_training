const plans = [
  {
    id: 1,
    name: "Weekly creator trends",
    query: "creator analytics week over week",
    status: "Draft"
  }
];

const planForm = document.getElementById("plan-form");
const nameInput = document.getElementById("plan-name");
const queryInput = document.getElementById("plan-query");
const plansList = document.getElementById("plans-list");

function stateClass(status) {
  if (status === "Approved") return "state-success";
  if (status === "Rejected") return "state-danger";
  if (status === "In Review") return "state-info";
  return "state-warning";
}

function renderPlans() {
  plansList.innerHTML = plans
    .map(
      (plan) => `
      <li class="plan-item">
        <div><strong>${plan.name}</strong></div>
        <div>${plan.query}</div>
        <div><span class="chip ${stateClass(plan.status)}">${plan.status}</span></div>
        <div class="plan-actions">
          <button class="button" onclick="runPlan(${plan.id})">Run</button>
          <button class="button" onclick="reviewResult(${plan.id})">Review Results</button>
          <button class="button" onclick="approvePlan(${plan.id})">Approve</button>
          <button class="button" onclick="rejectPlan(${plan.id})">Reject</button>
          <button class="button" onclick="bulkSelect(${plan.id})">Bulk Select</button>
        </div>
      </li>
    `
    )
    .join("");
}

planForm.addEventListener("submit", (event) => {
  event.preventDefault();
  plans.push({
    id: Date.now(),
    name: nameInput.value,
    query: queryInput.value,
    status: "Draft"
  });
  nameInput.value = "";
  queryInput.value = "";
  renderPlans();
});

function runPlan(id) {
  const plan = plans.find((p) => p.id === id);
  if (!plan) return;
  plan.status = "In Review";
  renderPlans();
}

function reviewResult(id) {
  const plan = plans.find((p) => p.id === id);
  if (!plan) return;
  plan.status = "In Review";
  renderPlans();
}

function approvePlan(id) {
  const plan = plans.find((p) => p.id === id);
  if (!plan) return;
  plan.status = "Approved";
  renderPlans();
}

function rejectPlan(id) {
  const plan = plans.find((p) => p.id === id);
  if (!plan) return;
  plan.status = "Rejected";
  renderPlans();
}

function bulkSelect() {
  alert("Added to bulk action queue");
}

renderPlans();
