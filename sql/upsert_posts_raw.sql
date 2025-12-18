INSERT INTO posts_raw (
id,
user_id,
title,
body,
ingested_run_id,
ingested_at_epoch_ms)

VALUES (
:id,
:user_id,
:title,
:body,
:ingested_run_id,
:ingested_at_epoch_ms)
ON CONFLICT (id) DO NOTHING;