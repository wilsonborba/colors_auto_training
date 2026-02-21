PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS video_downloads (
    id TEXT PRIMARY KEY,
    video_source_id TEXT NOT NULL,
    source_video_id TEXT,
    source_url TEXT,
    local_path TEXT,
    file_size_bytes INTEGER,
    sha256 TEXT,
    status TEXT NOT NULL,
    claimed_by TEXT,
    claimed_at TEXT,
    downloaded_video_id TEXT,
    downloaded_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (video_source_id) REFERENCES video_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (downloaded_video_id) REFERENCES videos(id) ON DELETE SET NULL,
    CHECK (status IN ('queued', 'downloading', 'downloaded', 'failed')),
    CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_video_downloads_source_video_id
    ON video_downloads(video_source_id, source_video_id)
    WHERE source_video_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_video_downloads_sha256
    ON video_downloads(sha256)
    WHERE sha256 IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_video_downloads_path_size
    ON video_downloads(local_path, file_size_bytes)
    WHERE local_path IS NOT NULL AND file_size_bytes IS NOT NULL;
