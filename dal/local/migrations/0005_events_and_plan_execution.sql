PRAGMA foreign_keys = ON;

ALTER TABLE events ADD COLUMN ts TEXT;
ALTER TABLE events ADD COLUMN entity_type TEXT;
ALTER TABLE events ADD COLUMN entity_id TEXT;

UPDATE events
SET ts = COALESCE(ts, created_at),
    entity_type = COALESCE(entity_type, aggregate_type),
    entity_id = COALESCE(entity_id, aggregate_id)
WHERE ts IS NULL OR entity_type IS NULL OR entity_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_type, entity_id, ts DESC);

ALTER TABLE search_plans ADD COLUMN total_keywords INTEGER NOT NULL DEFAULT 0;
ALTER TABLE search_plans ADD COLUMN current_keyword_index INTEGER NOT NULL DEFAULT 0;
ALTER TABLE search_plans ADD COLUMN current_keyword_text TEXT;
ALTER TABLE search_plans ADD COLUMN started_at TEXT;
ALTER TABLE search_plans ADD COLUMN deleted_at TEXT;

CREATE INDEX IF NOT EXISTS idx_search_plans_active ON search_plans(status, deleted_at, created_at DESC);
