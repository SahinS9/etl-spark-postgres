-- "$TARGET_DATABASE_URL"   -X   -v ON_ERROR_STOP=1   -f sql/region_migration/01_source_inventory.sql   | tee docs/evidence/region_migration/02_target_inventory_before_schema.txt --

/* psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/01_source_inventory.sql \
  | tee docs/evidence/region_migration/01_source_inventory.txt
*/



\echo '=== SOURCE DATABASE IDENTITY ==='

SELECT 
    current_database() as database_name,
    current_user as connected_user,
    version() as postgres_version,
    current_setting('server_version') as server_version,
    current_setting('wal_level') as wal_level;


\echo '=== DATABASE SIZE  ==='

SELECT 
    current_database() as database_name,
    pg_size_pretty(pg_database_size(current_database())) as database_size;


\echo '=== INSTALLED EXTENSIONS ==='

SELECT
    extname as extension_name,
    extversion as externsion_version
FROM pg_extension
ORDER BY extname;


\echo '=== APPLICATION TABLES ==='

SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;

\echo '=== TABLE SIZE AND ESTIMATED ROWS ==='

SELECT
    schemaname,
    relname as table_name,
    n_live_tup as estimated_rows, /* An estimated number of active rows,  not  an exact count. It is useful for planning, but later reconciliation should use SELECT COUNT(*) */
    pg_size_pretty(
        pg_total_relation_size(
            quote_ident(schemaname) || '.' || quote_ident(relname)
            )
            ) as total_size
FROM pg_stat_user_tables
ORDER BY schemaname, relname;


\echo '=== PRIMARY KEYS ==='

SELECT
    namespace.nspname as schema_name,
    table_class.relname as table_name,
    constraint_record.conname as primary_key_name,
    pg_get_constraintdef(constraint_record.oid) as definition
FROM pg_constraint as constraint_record
JOIN pg_class as table_class
    ON table_class.oid = constraint_record.conrelid
JOIN pg_namespace as namespace
    ON namespace.oid = table_class.relnamespace
WHERE constraint_record.contype = 'p'
    AND namespace.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY namespace.nspname, table_class.relname;


\echo '=== TABLES WITHOUT PRIMARY KEYS ==='

SELECT 
    namespace.nspname as schema_name,
    table_class.relname as table_name
FROM pg_class as table_class
JOIN pg_namespace as namespace
    ON namespace.oid = table_class.relnamespace
WHERE table_class.relkind = 'r'
    AND namespace.nspname NOT IN ('pg_catalog', 'information_schema')
    AND NOT EXISTS (
        SELECT 1
        FROM pg_constraint as constraint_record
        where constraint_record.conrelid = table_class.oid
            AND constraint_record.contype = 'p'
        )
ORDER BY namespace.nspname, table_class.relname;

/* is important because tables without primary keys may be more difficult to replicate safely.

For insert-only tables, replication may still work. But updates and deletes need a reliable row identity.

Possible solutions later include:
adding a primary key
adding a unique key
configuring REPLICA IDENTITY FULL

However, that decision should be reviewed carefully because REPLICA IDENTITY FULL can increase replication overhead.
*/



\echo '=== SEQUENCES ==='

/* the target might contain rows up to ID 100, while its sequence could still think the next ID is 1.
That could later cause duplicate-key errors. */

SELECT 
    sequence_schema,
    sequence_name,
    data_type,
    start_value,
    increment
FROM information_schema.sequences
WHERE sequence_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY sequence_schema, sequence_name;




