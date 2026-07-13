CREATE TABLE IF NOT EXISTS posts_enriched_stage (
    post_id INTEGER NOT NULL,

    user_id INTEGER NOT NULL,
    user_name VARCHAR(256) NOT NULL,
    user_mail VARCHAR(256) NOT NULL,

    title VARCHAR(256) NOT NULL,
    body TEXT NOT NULL,

    comment_count INTEGER NOT NULL,

    row_hash VARCHAR(64) NOT NULL,

    load_run_id VARCHAR(64) NOT NULL,
    load_at_epoch_ms BIGINT NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_pesg_post_id
ON posts_enriched_stage (post_id);

CREATE INDEX IF NOT EXISTS idx_pesg_load_run_id
ON posts_enriched_stage (load_run_id);

CREATE INDEX IF NOT EXISTS idx_pesg_row_hash
ON posts_enriched_stage (row_hash);


