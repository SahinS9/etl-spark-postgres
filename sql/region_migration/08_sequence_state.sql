\echo '=== ACTUAL SEQUENCE STATE ==='

SELECT
    schemaname,
    sequencename,
    last_value,
    start_value,
    increment_by
FROM pg_sequences
WHERE schemaname = 'public'
  AND sequencename IN (
      'etl_run_log_id_seq',
      'posts_enriched_history_id_seq'
  )
ORDER BY sequencename;