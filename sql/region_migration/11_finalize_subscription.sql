\echo '=== DISABLE SUBSCRIPTION ==='

ALTER SUBSCRIPTION etl_region_migration_sub DISABLE;

SELECT
    subname,
    subenabled,
    subslotname
FROM pg_subscription
WHERE subname = 'etl_region_migration_sub';

\echo '=== DROP SUBSCRIPTION ==='

DROP SUBSCRIPTION etl_region_migration_sub;

\echo '=== VERIFY SUBSCRIPTION REMOVED ==='

SELECT
    subname,
    subenabled,
    subslotname
FROM pg_subscription
WHERE subname = 'etl_region_migration_sub';