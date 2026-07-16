WITH current_rows_to_close AS (
    UPDATE public.posts_enriched_history AS history
    SET is_current = False
    FROM public.posts_enriched_stage AS stage
    WHERE stage.load_run_id = :run_id
        AND history.post_id = stage.post_id
        AND history.is_current = TRUE
        AND history.row_hash IS DISTINCT FROM stage.row_hash
    RETURNING history.post_id
    )
INSERT INTO public.posts_enriched_history (
    post_id
    ,user_id
    ,user_name
    ,user_email
    ,title
    ,body
    ,comment_count
    ,row_hash
    ,valid_from_run_id
    ,valid_from_epoch_ms
    ,is_current
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
    ,TRUE
FROM public.posts_enriched_stage as stage
WHERE stage.load_run_id = :run_id
    AND NOT EXISTS (
        SELECT 1 
        FROM public.posts_enriched_history as history
        WHERE history.post_id = stage.post_id
            AND history.is_current = TRUE
            AND history.row_hash = stage.row_hash
);