\echo '=== SUBSCRIPTION STATUS ==='

SELECT
    subname,
    pid,
    relid::regclass AS relation,
    received_lsn,
    latest_end_lsn,
    latest_end_time
FROM pg_stat_subscription
WHERE subname = 'etl_region_migration_sub';

\echo '=== TABLE SYNCHRONIZATION STATUS ==='

SELECT
    subscription.subname,
    relation.srrelid::regclass AS table_name,
    relation.srsubstate AS state_code,
    CASE relation.srsubstate
        WHEN 'i' THEN 'INITIALIZE'
        WHEN 'd' THEN 'DATA COPY'
        WHEN 'f' THEN 'FINISHED TABLE COPY'
        WHEN 's' THEN 'SYNCHRONIZED'
        WHEN 'r' THEN 'READY'
        ELSE relation.srsubstate::text
    END AS state_description,
    relation.srsublsn
FROM pg_subscription_rel AS relation
JOIN pg_subscription AS subscription
    ON subscription.oid = relation.srsubid
WHERE subscription.subname = 'etl_region_migration_sub'
ORDER BY table_name;

\echo '=== TARGET ROW COUNTS ==='

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
SELECT 'posts_raw', COUNT(*)
FROM public.posts_raw
UNION ALL
SELECT 'users_raw', COUNT(*)
FROM public.users_raw
ORDER BY table_name;