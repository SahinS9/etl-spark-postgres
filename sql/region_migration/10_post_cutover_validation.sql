\echo '=== TARGET DATABASE IDENTITY ==='

SELECT
    current_database() AS database_name,
    current_user AS connected_user,
    current_setting('server_version') AS server_version;

\echo '=== APPLICATION TABLES ==='

SELECT
    tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

\echo '=== BUSINESS TABLE COUNTS ==='

SELECT 'comments_raw' AS table_name, COUNT(*) AS row_count
FROM public.comments_raw
UNION ALL
SELECT 'etl_run_log', COUNT(*)
FROM public.etl_run_log
UNION ALL
SELECT 'posts_enriched_history', COUNT(*)
FROM public.posts_enriched_history
UNION ALL
SELECT 'posts_enriched_snapshot', COUNT(*)
FROM public.posts_enriched_snapshot
UNION ALL
SELECT 'posts_enriched_stage', COUNT(*)
FROM public.posts_enriched_stage
UNION ALL
SELECT 'posts_raw', COUNT(*)
FROM public.posts_raw
UNION ALL
SELECT 'schema_migrations', COUNT(*)
FROM public.schema_migrations
UNION ALL
SELECT 'users_raw', COUNT(*)
FROM public.users_raw
ORDER BY table_name;

\echo '=== FAILED OR INCOMPLETE ETL RUNS ==='

SELECT
    run_id,
    status,
    started_at,
    finished_at,
    message
FROM public.etl_run_log
WHERE status NOT IN ('SUCCESS', 'FAILED')
ORDER BY started_at DESC;

\echo '=== TARGET SEQUENCE STATE ==='

SELECT
    'etl_run_log_id_seq' AS sequence_name,
    last_value,
    is_called
FROM public.etl_run_log_id_seq

UNION ALL

SELECT
    'posts_enriched_history_id_seq',
    last_value,
    is_called
FROM public.posts_enriched_history_id_seq;