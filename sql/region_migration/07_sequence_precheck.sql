\echo '=== GENERATED ID SEQUENCES ==='

SELECT
    'etl_run_log' AS table_name,
    'id' AS column_name,
    pg_get_serial_sequence('public.etl_run_log', 'id') AS sequence_name,
    COALESCE(MAX(id), 0) AS maximum_table_id
FROM public.etl_run_log

UNION ALL

SELECT
    'posts_enriched_history',
    'id',
    pg_get_serial_sequence('public.posts_enriched_history', 'id'),
    COALESCE(MAX(id), 0)
FROM public.posts_enriched_history;