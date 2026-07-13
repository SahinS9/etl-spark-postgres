CREATE TABLE if NOT EXISTS posts_enriched_history (
    id BIGSERIAL PRIMARY KEY,

    post_id INTEGER NOT NULL,

    user_id INTEGER NOT NULL,
    user_name VARCHAR(256) NOT NULL,
    user_email VARCHAR(256) NOT NULL,

    title VARCHAR(256) NOT NULL,
    body TEXT NOT NULL,

    comment_count INTEGER NOT NULL,

    row_hash VARCHAR(64) NOT NULL,

    valid_from_run_id VARCHAR(64) NOT NULL,
    valid_from_epoch_ms BIGINT NOT NULL,

    is_current BOOLEAN NOT NULL DEFAULT TRUE
    );

CREATE INDEX IF NOT EXISTS idx_peh_post_id_current
    ON posts_enriched_history (post_id)
    WHERE is_current = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_peh_post_id_current
    ON posts_enriched_history (post_id)
    WHERE is_current = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_peh_post_id_hash
    ON posts_enriched_history (post_id, row_hash);

