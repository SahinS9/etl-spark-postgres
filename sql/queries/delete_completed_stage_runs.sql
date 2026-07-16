DELETE FROM public.posts_enriched_stage AS stage
USING public.etl_run_log AS run_log
WHERE stage.load_run_id = run_log.run_id
  AND run_log.status = 'SUCCESS'
  AND stage.load_run_id <> :current_run_id;