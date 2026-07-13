\echo '=== CREATE REGION MIGRATION PUBLICATION ==='

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_publication
        WHERE pubname = 'etl_region_migration_pub'
    ) THEN
        CREATE PUBLICATION etl_region_migration_pub
        FOR TABLE
            public.comments_raw,
            public.etl_run_log,
            public.posts_enriched_history,
            public.posts_enriched_snapshot,
            public.posts_raw,
            public.users_raw;
    END IF;
END
$$;

\echo '=== PUBLICATION DETAILS ==='

SELECT
    pubname,
    pubinsert,
    pubupdate,
    pubdelete,
    pubtruncate
FROM pg_publication
WHERE pubname = 'etl_region_migration_pub';

\echo '=== PUBLISHED TABLES ==='

SELECT
    pubname,
    schemaname,
    tablename
FROM pg_publication_tables
WHERE pubname = 'etl_region_migration_pub'
ORDER BY schemaname, tablename;