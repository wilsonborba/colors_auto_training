PRAGMA foreign_keys = ON;

CREATE INDEX IF NOT EXISTS idx_videos_source ON videos(video_source_id);
CREATE INDEX IF NOT EXISTS idx_videos_status_enabled ON videos(status, is_enabled);
CREATE INDEX IF NOT EXISTS idx_jobs_claim ON jobs(status, run_after_at, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_locked_by ON jobs(locked_by, locked_at);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_search_plans_status ON search_plans(status, created_at);
CREATE INDEX IF NOT EXISTS idx_search_plan_keywords_plan ON search_plan_keywords(search_plan_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_search_plan_keyword ON search_plan_keywords(search_plan_id, keyword);
CREATE INDEX IF NOT EXISTS idx_search_results_plan ON search_results(search_plan_id, ranking);
