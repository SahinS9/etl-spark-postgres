INSERT INTO posts_enriched (
post_id,
user_id,
user_name,
user_email,
title,
body,
comment_count,
loaded_run_id,
loaded_at_epoch_ms)

VALUES (
:post_id,
:user_id,
:user_name,
:user_email,
:title,
:body,
:comment_count,
:loaded_run_id,
:loaded_at_epoch_ms)

ON CONFLICT (post_id) DO UPDATE
SET
    user_id = EXCLUDED.user_id,
    user_name = EXCLUDED.user_name,
    user_email = EXCLUDED.user_email,
    title = EXCLUDED.title,
    body = EXCLUDED.body,
    comment_count = EXCLUDED.comment_count,
    loaded_run_id = EXCLUDED.loaded_run_id,
    loaded_at_epoch_ms = EXCLUDED.loaded_at_epoch_ms;