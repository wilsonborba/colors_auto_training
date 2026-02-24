-- V001__create_keywords_videos_logs.sql

-- Optional: enable UUID generation helpers (Postgres)
-- If you already generate UUIDs in the app, you can remove this.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) keywords
CREATE TABLE IF NOT EXISTS keywords (
    id               UUID PRIMARY KEY,
    key_name         TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    videos_extracted BOOLEAN NOT NULL DEFAULT FALSE
);

-- Helpful uniqueness (optional): uncomment if you want no duplicate key_name
-- CREATE UNIQUE INDEX IF NOT EXISTS ux_keywords_key_name ON keywords (key_name);

CREATE INDEX IF NOT EXISTS ix_keywords_created_at ON keywords (created_at);


-- 2) videos
CREATE TABLE IF NOT EXISTS videos (
    id           UUID PRIMARY KEY,
    keyword_id   UUID NOT NULL,
    name         TEXT NOT NULL,
    img_tumbnail TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status       TEXT NOT NULL DEFAULT 'QUEUED',
    url_link     TEXT NOT NULL,

    CONSTRAINT fk_videos_keyword
        FOREIGN KEY (keyword_id)
        REFERENCES keywords (id)
        ON DELETE CASCADE,

    CONSTRAINT ck_videos_status
        CHECK (status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED'))
);

CREATE INDEX IF NOT EXISTS ix_videos_keyword_id ON videos (keyword_id);
CREATE INDEX IF NOT EXISTS ix_videos_status ON videos (status);
CREATE INDEX IF NOT EXISTS ix_videos_created_at ON videos (created_at);

-- Optional: avoid duplicate URLs (often useful)
-- CREATE UNIQUE INDEX IF NOT EXISTS ux_videos_url_link ON videos (url_link);


-- 3) video_logs
CREATE TABLE IF NOT EXISTS video_logs (
    id        UUID PRIMARY KEY,
    video_id  UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    message   TEXT NOT NULL,

    CONSTRAINT fk_video_logs_video
        FOREIGN KEY (video_id)
        REFERENCES videos (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_video_logs_video_id ON video_logs (video_id);
CREATE INDEX IF NOT EXISTS ix_video_logs_timestamp ON video_logs (timestamp);
