-- keywords_videos_002_add_query_search.sql
-- Add keywords.query_search (only if missing)

SET @col := (
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'keywords'
    AND column_name = 'query_search'
);

SET @sql := IF(
  @col = 0,
  'ALTER TABLE keywords ADD COLUMN query_search TEXT NOT NULL',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
