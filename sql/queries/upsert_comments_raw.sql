INSERT INTO comments_raw (
    id,
    post_id,
    name,
    email,
    body,
    ingested_run_id,
    ingested_at_epoch_ms)
VALUES (
    :id,
    :post_id,
    :name,
    :email,
    :body,
    :ingested_run_id,
    :ingested_at_epoch_ms
    )
ON CONFLICT (id) DO UPDATE
SET
    post_id = EXCLUDED.post_id,
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    body = EXCLUDED.body,
    ingested_run_id = EXCLUDED.ingested_run_id,
    ingested_at_epoch_ms = EXCLUDED.ingested_at_epoch_ms;
