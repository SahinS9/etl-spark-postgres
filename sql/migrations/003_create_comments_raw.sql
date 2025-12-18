CREATE TABLE IF NOT EXISTS comments_raw (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,

    name VARCHAR(512) NOT NULL,
    email VARCHAR(256) NOT NULL,
    body TEXT NOT NULL,

    ingested_run_id VARCHAR(64) NOT NULL,
    ingested_at_epoch_ms BIGINT NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_comments_raw_post_id
    ON comments_raw (post_id);

CREATE INDEX IF NOT EXISTS idx_comments_raw_ingested_run_id
    ON comments_raw (ingested_run_id);