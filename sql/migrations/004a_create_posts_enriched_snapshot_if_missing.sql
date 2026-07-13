CREATE TABLE IF NOT EXISTS posts_enriched_snapshot (
    post_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(256) NOT NULL,
    user_email VARCHAR(256) NOT NULL,
    title VARCHAR(512) NOT NULL,
    body TEXT NOT NULL,
    comment_count INTEGER NOT NULL,
    loaded_run_id VARCHAR(64) NOT NULL,
    loaded_at_epoch_ms BIGINT NOT NULL
);