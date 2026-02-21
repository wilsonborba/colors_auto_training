#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# init_repo_structure.sh
#
# Creates the initial project directory structure and adds an explanation.md
# file in each directory describing what belongs there.
#
# Run from repo root:
#   bash scripts/init_repo_structure.sh
# -----------------------------------------------------------------------------

# Helper: create directory and write explanation.md (only if it doesn't exist)
mkd() {
  local dir="$1"
  local text="$2"
  mkdir -p "$dir"
  if [[ ! -f "${dir}/explanation.md" ]]; then
    cat > "${dir}/explanation.md" <<EOF
# ${dir}

${text}
EOF
  fi
}

# -----------------------------------------------------------------------------
# CORE
# -----------------------------------------------------------------------------
mkd "core" \
"**Core operational foundation** for the app.

Put here:
- \`settings.py\`: a single Pydantic Settings class (env reading lives *only* here).
- global configuration contracts and shared constants (with discipline).
- cross-cutting utilities that are *not* infrastructure (e.g., domain-safe types, logging interface definitions).

Do **not** put:
- I/O code (network, filesystem, sqlite) → goes in \`dal/\`.
- business workflows → goes in \`domain/services/\` or \`domain/tasks/\`."

# -----------------------------------------------------------------------------
# DAL (Data Access Layer) = all adapters to the outside world
# -----------------------------------------------------------------------------
mkd "dal" \
"**Data Access Layer (DAL)**: adapters that talk to the outside world (remote/local).

Rules:
- DAL exposes *general-purpose adapter methods* (CRUD-ish, fetch/save, etc.).
- DAL contains no orchestration logic (no multi-step workflows).
- DAL code is consumed by **domain services**."

mkd "dal/remote" \
"Remote adapters: YouTube, HTTP APIs, scraping, external storage, etc.

Put here:
- API clients, request/response mapping, retry/backoff, rate-limiting, auth handling.
- 'Adapters' only — not domain workflows."

# Example file stub user requested
mkdir -p "dal/remote"
if [[ ! -f "dal/remote/youtube_adapter.py" ]]; then
  cat > "dal/remote/youtube_adapter.py" <<'EOF'
"""
YouTube adapter (DAL - remote)

Responsibilities:
- Search videos by keywords (if enabled)
- Fetch metadata (title, channel, duration, etc.)
- Download video / audio streams (implementation choice)
- Report progress callbacks to caller
- Raise typed adapter errors (no HTTP status codes here)

This file must not:
- Decide job priorities
- Update UI state directly
- Orchestrate pipeline stages
Those belong to domain services/tasks.
"""
EOF
fi

mkd "dal/local" \
"Local adapters: SQLite, filesystem, local caches.

Put here:
- \`sqlite_adapter.py\`: connection/session management, migrations strategy, queries.
- filesystem adapter(s): save/read assets, compute hashes, atomic writes.
- Any 'local I/O' adapter.

Note: your SQLite file can live under \`dal/local/\` (e.g., \`dal/local/app.sqlite\`) or under \`dal/local/state/\` if you later want to split it."

mkd "dal/local/assets" \
"Local assets root folder.

This is where the pipeline stores **physical artifacts** (videos, images, audit set, etc.).
Important rule:
- Treat this as *data*, not code.
- Keep it organized and append-only when possible (especially for audit and pseudo cycles)."

mkd "dal/local/assets/audit" \
"Frozen audit dataset (never used for training).

Put here:
- \`img/\` (or equivalent): the 1,000 audit images
- \`annotations/\` (or \`labels.csv\`): ground truth annotations
- optional: \`datasheet.md\` describing collection/coverage/limits

Rule:
- Do not write training outputs here.
- Do not add samples casually; changes must be deliberate and versioned."

mkd "dal/local/assets/videos" \
"Downloaded raw videos.

Put here:
- immutable or mostly-immutable raw video files
- hashed filenames or manifest-driven paths recommended

Rule:
- Video ingest/download worker writes here.
- Any derived outputs (frames/crops) should go elsewhere (e.g., under \`dal/local/assets/img/\`)."

mkd "dal/local/assets/img" \
"Derived image artifacts (frames, crops, ROIs, masks).

This is the working area for vision pipeline outputs.
Recommended subfolders:
- \`person/\`: person crops (bbox-based)
- \`clothes/\`: clothing ROIs + masks
- later: \`frames/\`, \`roi_upper/\`, \`roi_lower/\`, \`masks/\`, \`rejected/\`"

mkd "dal/local/assets/img/person" \
"Person-related image artifacts.

Put here:
- person crops from detection stage
- associated metadata files (bbox, confidence) if stored alongside images"

mkd "dal/local/assets/img/clothes" \
"Clothing-related image artifacts.

Put here:
- upper/lower clothing crops (ROI outputs)
- cloth masks (if stored together) or mask references
- rejected samples can go under a \`rejected/\` sibling folder later"

# -----------------------------------------------------------------------------
# DOMAIN
# -----------------------------------------------------------------------------
mkd "domain" \
"Domain layer = business logic and ML workflow logic (but **not** raw I/O).

Put here:
- entities/value objects (VideoJob, AuditSample, Run, ModelArtifact)
- service layer (use-cases) that call DAL adapters
- task definitions (repeatable jobs)
- run logic (ML training/eval artifacts) — per your preference"

mkd "domain/services" \
"Domain services = use-cases that orchestrate adapters.

Examples:
- \`video_queue_service.py\`: enqueue, reprioritize, retry policies
- \`download_service.py\`: call youtube_adapter + filesystem adapter + sqlite adapter
- \`dex_service.py\`: frame sampling → detection → ROI → mask, using adapters

Rules:
- services may call multiple adapters
- services must be testable (inject adapters)
- services do not contain HTTP / UI concerns"

mkd "domain/tasks" \
"Task runners / scheduled jobs.

Put here:
- periodic download worker
- pipeline stage workers (detect, crop, mask, label, train, evaluate)
- retry loops and job state transitions (but not UI)

Rules:
- tasks call domain services
- tasks are the bridge between 'daemon/worker world' and services"

mkd "domain/runs" \
"Runs = ML-related run artifacts and lifecycle.

Put here:
- evaluation run records (metrics.json, per-class reports)
- training run records (config, checkpoints, lineage)
- promotion decisions and model registry entries (if you keep registry here)

Rule:
- runs are append-only per run_id.
- do not mix runs with frozen audit data."

# -----------------------------------------------------------------------------
# PRESENTATION
# -----------------------------------------------------------------------------
mkd "presentation" \
"Presentation layer = API routes, handlers/controllers, and SSR/static frontend.

Put here:
- FastAPI app setup, routers
- handlers that call domain services
- response DTOs (your standard {status_code, message, data})
- SSR pages/templates and their JS/CSS separated by feature

Rules:
- routes should be thin: validate input → call handler → map to HTTP status
- handlers may call multiple services
- no DAL usage directly from routes (routes → handlers → services → adapters)."

# Optional: suggest subfolders for presentation, keeping your separation strict
mkd "presentation/api" \
"FastAPI app + routers.

Put here:
- \`main.py\` (app factory)
- \`routes/\` (only route wiring + status code mapping)
- dependencies/injection wiring"

mkd "presentation/handlers" \
"Handlers/controllers.

Put here:
- functions that coordinate one or more domain services
- mapping domain results to presentation DTOs

Rules:
- no direct HTTP logic besides preparing a response object
- no raw DAL calls (handlers call services)."

mkd "presentation/web" \
"SSR/static frontend.

Organize by feature/page:
- \`pages/video_downloads/\`
  - \`video_downloads.html\`
  - \`video_downloads.js\`
  - \`video_downloads.css\`

Rules:
- keep JS/HTML/CSS separated
- no big shared file dumping ground; shared components go in \`presentation/web/shared/\`."

mkd "presentation/web/pages" \
"Feature pages (each page in its own directory)."

mkd "presentation/web/shared" \
"Shared frontend assets.

Put here:
- shared CSS (base styles)
- shared JS utilities (small and disciplined)
- shared HTML partials (if you adopt them)"

echo "✅ Directory structure created and explanation.md files written."
