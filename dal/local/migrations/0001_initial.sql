PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS video_sources (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    external_ref TEXT,
    display_name TEXT,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (is_enabled IN (0, 1))
);

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    video_source_id TEXT NOT NULL,
    source_video_id TEXT,
    title TEXT,
    source_url TEXT,
    local_path TEXT,
    file_size_bytes INTEGER,
    sha256 TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    is_enabled INTEGER NOT NULL DEFAULT 1,
    retries INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (video_source_id) REFERENCES video_sources(id) ON DELETE CASCADE,
    CHECK (is_enabled IN (0, 1)),
    CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    CHECK (retries >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_videos_sha256 ON videos(sha256) WHERE sha256 IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_videos_path_size ON videos(local_path, file_size_bytes)
    WHERE local_path IS NOT NULL AND file_size_bytes IS NOT NULL;

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT,
    priority INTEGER NOT NULL DEFAULT 0,
    run_after_at TEXT,
    locked_by TEXT,
    locked_at TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (attempts >= 0),
    CHECK (max_attempts >= 1)
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    aggregate_type TEXT,
    aggregate_id TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_plans (
    id TEXT PRIMARY KEY,
    video_source_id TEXT,
    query TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    generated_by_job_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (video_source_id) REFERENCES video_sources(id) ON DELETE SET NULL,
    FOREIGN KEY (generated_by_job_id) REFERENCES jobs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS search_plan_keywords (
    id TEXT PRIMARY KEY,
    search_plan_id TEXT NOT NULL,
    keyword TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (search_plan_id) REFERENCES search_plans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_results (
    id TEXT PRIMARY KEY,
    search_plan_id TEXT NOT NULL,
    source_video_id TEXT,
    title TEXT,
    source_url TEXT,
    channel_name TEXT,
    relevance_score REAL,
    ranking INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    ingested_video_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (search_plan_id) REFERENCES search_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (ingested_video_id) REFERENCES videos(id) ON DELETE SET NULL
);
