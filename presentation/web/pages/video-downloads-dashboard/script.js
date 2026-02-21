const downloads = [
  { id: "v-104", title: "How to Build Healthy Habits", priority: 2, status: "Queued", progress: 0 },
  { id: "v-211", title: "Street Food Stories: Seoul", priority: 1, status: "Downloading", progress: 43 },
  { id: "v-315", title: "Ocean Documentary Episode 4", priority: 3, status: "Failed", progress: 65 }
];

const tbody = document.getElementById("downloads-tbody");

function statusClass(status) {
  if (status === "Downloading") return "state-info";
  if (status === "Completed") return "state-success";
  if (status === "Failed") return "state-danger";
  return "state-warning";
}

function render() {
  tbody.innerHTML = downloads
    .sort((a, b) => a.priority - b.priority)
    .map(
      (item) => `
        <tr>
          <td>${item.title}</td>
          <td>
            <div class="priority-controls">
              <button class="button" onclick="changePriority('${item.id}', -1)">↑</button>
              <span>${item.priority}</span>
              <button class="button" onclick="changePriority('${item.id}', 1)">↓</button>
            </div>
          </td>
          <td><span class="chip ${statusClass(item.status)}">${item.status}</span></td>
          <td>
            <div class="progress-wrap">
              <progress max="100" value="${item.progress}"></progress>
              <small>${item.progress}%</small>
            </div>
          </td>
          <td>
            <div class="row-actions">
              <button class="button" onclick="retry('${item.id}')">Retry</button>
              <button class="button" onclick="toggleEnabled('${item.id}')">${item.disabled ? "Enable" : "Disable"}</button>
            </div>
          </td>
        </tr>
      `
    )
    .join("");
}

function changePriority(id, delta) {
  const item = downloads.find((d) => d.id === id);
  if (!item) return;
  item.priority = Math.max(1, item.priority + delta);
  render();
}

function retry(id) {
  const item = downloads.find((d) => d.id === id);
  if (!item) return;
  item.status = "Downloading";
  item.progress = 10;
  render();
}

function toggleEnabled(id) {
  const item = downloads.find((d) => d.id === id);
  if (!item) return;
  item.disabled = !item.disabled;
  item.status = item.disabled ? "Queued" : "Downloading";
  render();
}

render();
