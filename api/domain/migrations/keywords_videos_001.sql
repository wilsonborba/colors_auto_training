-- keywords_videos_001.sql (MySQL / Aiven MySQL)

-- 1) keywords
CREATE TABLE IF NOT EXISTS keywords (
  id               CHAR(36) NOT NULL PRIMARY KEY,
  key_name         VARCHAR(255) NOT NULL,
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  videos_extracted BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB;

-- Index: keywords(created_at)
SET @idx := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'keywords'
    AND index_name = 'ix_keywords_created_at'
);
SET @sql := IF(@idx = 0,
  'CREATE INDEX ix_keywords_created_at ON keywords (created_at)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


-- 2) videos
CREATE TABLE IF NOT EXISTS videos (
  id           CHAR(36) NOT NULL PRIMARY KEY,
  keyword_id   CHAR(36) NOT NULL,
  name         VARCHAR(255) NOT NULL,
  img_tumbnail TEXT NOT NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status       VARCHAR(16) NOT NULL DEFAULT 'QUEUED',
  url_link     TEXT NOT NULL,

  CONSTRAINT fk_videos_keyword
    FOREIGN KEY (keyword_id)
    REFERENCES keywords(id)
    ON DELETE CASCADE,

  CONSTRAINT ck_videos_status
    CHECK (status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED'))
) ENGINE=InnoDB;

-- Index: videos(keyword_id)
SET @idx := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'videos'
    AND index_name = 'ix_videos_keyword_id'
);
SET @sql := IF(@idx = 0,
  'CREATE INDEX ix_videos_keyword_id ON videos (keyword_id)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Index: videos(status)
SET @idx := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'videos'
    AND index_name = 'ix_videos_status'
);
SET @sql := IF(@idx = 0,
  'CREATE INDEX ix_videos_status ON videos (status)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Index: videos(created_at)
SET @idx := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'videos'
    AND index_name = 'ix_videos_created_at'
);
SET @sql := IF(@idx = 0,
  'CREATE INDEX ix_videos_created_at ON videos (created_at)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


-- 3) video_logs
CREATE TABLE IF NOT EXISTS video_logs (
  id        CHAR(36) NOT NULL PRIMARY KEY,
  video_id  CHAR(36) NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  message   TEXT NOT NULL,

  CONSTRAINT fk_video_logs_video
    FOREIGN KEY (video_id)
    REFERENCES videos(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- Index: video_logs(video_id)
SET @idx := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'video_logs'
    AND index_name = 'ix_video_logs_video_id'
);
SET @sql := IF(@idx = 0,
  'CREATE INDEX ix_video_logs_video_id ON video_logs (video_id)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Index: video_logs(timestamp)
SET @idx := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'video_logs'
    AND index_name = 'ix_video_logs_timestamp'
);
SET @sql := IF(@idx = 0,
  'CREATE INDEX ix_video_logs_timestamp ON video_logs (timestamp)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
