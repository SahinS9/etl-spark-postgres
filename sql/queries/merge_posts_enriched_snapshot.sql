INSERT INTO public.posts_enriched_snapshot(
    post_id
    ,user_id
    ,user_name
    ,user_email
    ,title
    ,body
    ,comment_count
    ,row_hash
    ,loaded_run_id
    ,loaded_at_epoch_ms
    )
SELECT
    stage.post_id
    ,stage.user_id
    ,stage.user_name
    ,stage.user_email
    ,stage.title
    ,stage.body
    ,stage.comment_count
    ,stage.row_hash
    ,stage.load_run_id
    ,stage.load_at_epoch_ms
FROM public.posts_enriched_stage as stage
WHERE stage.load_run_id = :run_id
ON CONFLICT (post_id)
DO UPDATE SET
    user_id = EXCLUDED.user_id
    ,user_name = EXCLUDED.user_name
    ,user_email = EXCLUDED.user_email
    ,title = EXCLUDED.title
    ,body = EXCLUDED.body
    ,comment_count = EXCLUDED.comment_count
    ,row_hash = EXCLUDED.row_hash
    ,loaded_run_id = EXCLUDED.loaded_run_id
    ,loaded_at_epoch_ms = EXCLUDED.loaded_at_epoch_ms
WHERE public.posts_enriched_snapshot.row_hash
    IS DISTINCT FROM EXCLUDED.row_hash;
