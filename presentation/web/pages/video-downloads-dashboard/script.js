const tbody = document.getElementById("downloads-tbody");
const progressByVideo = new Map();

function statusClass(status) {
  if (status === "done") return "state-success";
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

function progressHtml(item) {
  const p = progressByVideo.get(item.id) || {};
  const percent = Number(p.percent || p.progress_percent || 0);
  const speed = p.speed || p.speed_mbps || "-";
  const eta = p.eta || p.eta_seconds || "-";
  return `<div class="progress-wrap"><progress max="100" value="${percent}"></progress><small>${percent}% | speed: ${speed} | ETA: ${eta}</small></div>`;
}

function render(videos) {
  tbody.innerHTML = videos
    .map(
      (item) => `
        <tr>
          <td>${item.title || item.source_video_id || item.id}<br/>${progressHtml(item)}</td>
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
  await Promise.all(videos.slice(0, 20).map(async (video) => {
    const events = await api(`/videos/${video.id}/events/tail?limit=10`);
    const progressEvent = events.find((event) => event.event_type === "download_progress");
    if (progressEvent) progressByVideo.set(video.id, progressEvent.payload || {});
  }));
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
setInterval(() => loadVideos().catch(() => {}), 3000);
