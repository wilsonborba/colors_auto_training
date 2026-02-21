const tbody = document.getElementById("downloads-tbody");

function statusClass(status) {
  if (status === "downloaded") return "state-success";
  if (status === "failed") return "state-danger";
  if (status === "downloading") return "state-info";
  return "state-warning";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || "request failed");
  return payload.data;
}

function render(videos) {
  tbody.innerHTML = videos
    .map(
      (item) => `
        <tr>
          <td>${item.title || item.source_video_id || item.id}</td>
          <td>
            <div class="priority-controls">
              <button class="button" onclick="changePriority('${item.id}', -1)">↑</button>
              <span>${item.priority ?? 0}</span>
              <button class="button" onclick="changePriority('${item.id}', 1)">↓</button>
            </div>
          </td>
          <td><span class="chip ${statusClass(item.status)}">${item.status}</span></td>
          <td>${item.source_url || "-"}</td>
          <td>
            <div class="row-actions">
              <button class="button" onclick="retry('${item.id}')">Retry</button>
              <button class="button" onclick="toggleEnabled('${item.id}', ${item.is_enabled ? 1 : 0})">${item.is_enabled ? "Disable" : "Enable"}</button>
            </div>
          </td>
        </tr>
      `,
    )
    .join("");
}

async function loadVideos() {
  const videos = await api("/videos");
  render(videos);
}

async function changePriority(id, delta) {
  const videos = await api("/videos");
  const item = videos.find((video) => video.id === id);
  if (!item) return;
  const nextPriority = Math.max(0, Number(item.priority || 0) + delta);
  await api(`/videos/${id}/priority`, {
    method: "POST",
    body: JSON.stringify({ priority: nextPriority }),
  });
  await loadVideos();
}

async function retry(id) {
  await api(`/videos/${id}/retry`, { method: "POST" });
  await loadVideos();
}

async function toggleEnabled(id, enabled) {
  const path = enabled ? `/videos/${id}/disable` : `/videos/${id}/enable`;
  await api(path, { method: "POST" });
  await loadVideos();
}

window.changePriority = changePriority;
window.retry = retry;
window.toggleEnabled = toggleEnabled;

loadVideos().catch((err) => {
  tbody.innerHTML = `<tr><td colspan="5">Erro ao carregar: ${err.message}</td></tr>`;
});
