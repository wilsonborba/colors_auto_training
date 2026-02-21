const eventsList = document.getElementById("events-list");
const tailToggle = document.getElementById("tail-toggle");
const clearButton = document.getElementById("clear-button");

const streamSeed = [
  { level: "info", msg: "Job #920 started for batch alpha" },
  { level: "warn", msg: "Retrying thumbnail extraction for video v-315" },
  { level: "success", msg: "Job #918 completed successfully" },
  { level: "info", msg: "Queue depth changed to 12" }
];

function classFor(level) {
  if (level === "success") return "state-success";
  if (level === "warn") return "state-warning";
  if (level === "danger") return "state-danger";
  return "state-info";
}

function addEvent(event) {
  const li = document.createElement("li");
  li.className = "event-item";
  li.innerHTML = `
    <div><span class="chip ${classFor(event.level)}">${event.level}</span> ${event.msg}</div>
    <div class="event-meta">
      <span>${new Date().toLocaleTimeString()}</span>
      <span>worker-node-2</span>
    </div>
  `;
  eventsList.appendChild(li);

  if (tailToggle.checked) {
    li.scrollIntoView({ behavior: "smooth", block: "end" });
  }
}

clearButton.addEventListener("click", () => {
  eventsList.innerHTML = "";
});

streamSeed.forEach(addEvent);

setInterval(() => {
  const sample = streamSeed[Math.floor(Math.random() * streamSeed.length)];
  addEvent(sample);
}, 4000);
