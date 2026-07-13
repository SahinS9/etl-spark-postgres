\echo '=== GRANT REPLICATION ROLE ACCESS ==='

GRANT CONNECT ON DATABASE neondb
TO etl_region_replication;

GRANT USAGE ON SCHEMA public
TO etl_region_replication;

GRANT SELECT ON TABLE
    public.comments_raw,
    public.etl_run_log,
    public.posts_enriched_history,
    public.posts_enriched_snapshot,
    public.posts_raw,
    public.users_raw
TO etl_region_replication;

\echo '=== VERIFY TABLE PRIVILEGES ==='

SELECT
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'etl_region_replication'
ORDER BY table_schema, table_name, privilege_type;