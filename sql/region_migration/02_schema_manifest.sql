\echo '=== TABLE COLUMNS ==='

SELECT
    columns.table_schema,
    columns.table_name,
    columns.ordinal_position,
    columns.column_name,
    columns.data_type,
    columns.udt_name,
    columns.character_maximum_length,
    columns.numeric_precision,
    columns.numeric_scale,
    columns.is_nullable,
    columns.column_default,
    columns.is_identity,
    columns.identity_generation
FROM information_schema.columns AS columns
WHERE columns.table_schema = 'public'
  AND columns.table_name <> 'schema_migrations'
ORDER BY
    columns.table_schema,
    columns.table_name,
    columns.ordinal_position;

\echo '=== PRIMARY AND UNIQUE CONSTRAINTS ==='

SELECT
    namespace.nspname AS schema_name,
    table_record.relname AS table_name,
    constraint_record.contype AS constraint_type,
    constraint_record.conname AS constraint_name,
    pg_get_constraintdef(constraint_record.oid) AS definition
FROM pg_constraint AS constraint_record
JOIN pg_class AS table_record
    ON table_record.oid = constraint_record.conrelid
JOIN pg_namespace AS namespace
    ON namespace.oid = table_record.relnamespace
WHERE namespace.nspname = 'public'
  AND constraint_record.contype IN ('p', 'u')
  AND table_record.relname <> 'schema_migrations'
ORDER BY
    namespace.nspname,
    table_record.relname,
    constraint_record.contype,
    constraint_record.conname;

\echo '=== INDEXES ==='

SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename <> 'schema_migrations'
ORDER BY schemaname, tablename, indexname;

\echo '=== REPLICA IDENTITY ==='

SELECT
    namespace.nspname AS schema_name,
    table_record.relname AS table_name,
    CASE table_record.relreplident
        WHEN 'd' THEN 'DEFAULT'
        WHEN 'n' THEN 'NOTHING'
        WHEN 'f' THEN 'FULL'
        WHEN 'i' THEN 'INDEX'
        ELSE table_record.relreplident::text
    END AS replica_identity
FROM pg_class AS table_record
JOIN pg_namespace AS namespace
    ON namespace.oid = table_record.relnamespace
WHERE namespace.nspname = 'public'
  AND table_record.relkind = 'r'
  AND table_record.relname <> 'schema_migrations'
ORDER BY namespace.nspname, table_record.relname;