PRAGMA foreign_keys = ON;

ALTER TABLE search_plans ADD COLUMN source_type TEXT NOT NULL DEFAULT 'manual';
ALTER TABLE search_plans ADD COLUMN review_reason TEXT;

ALTER TABLE search_plan_keywords ADD COLUMN is_negative INTEGER NOT NULL DEFAULT 0;

ALTER TABLE search_results ADD COLUMN query_keyword TEXT;
ALTER TABLE search_results ADD COLUMN review_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_search_plan_keywords_plan_negative
    ON search_plan_keywords(search_plan_id, is_negative, created_at);

CREATE INDEX IF NOT EXISTS idx_search_results_plan_status
    ON search_results(search_plan_id, status, ranking);
