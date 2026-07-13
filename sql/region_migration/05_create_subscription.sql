\echo '=== CREATE TARGET SUBSCRIPTION ==='

\getenv source_conninfo REPLICATION_SOURCE_URL

CREATE SUBSCRIPTION etl_region_migration_sub
CONNECTION :'source_conninfo'
PUBLICATION etl_region_migration_pub
WITH (
    copy_data = true,
    create_slot = true,
    enabled = true,
    slot_name = 'etl_region_migration_slot'
);

\echo '=== SUBSCRIPTION CREATED ==='

SELECT
    subname,
    subenabled,
    subslotname,
    subpublications
FROM pg_subscription
WHERE subname = 'etl_region_migration_sub';