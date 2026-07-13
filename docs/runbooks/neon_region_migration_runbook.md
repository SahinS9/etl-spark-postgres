# Neon Region Migration Runbook
## PostgreSQL 17 → PostgreSQL 18 with Logical Replication

This runbook records the file creation order and the terminal commands used to migrate the ETL database from the old Neon region to the new Neon project.

> Never commit real database URLs, usernames, or passwords. Store them only in `.env`.

---

## 0. Required environment variables

Add these values to `.env`:

```env
# Active application database
DATABASE_URL='postgresql://...'

# Old PostgreSQL 17 source database
SOURCE_DATABASE_URL='postgresql://...'

# New PostgreSQL 18 target, pooled application URL
TARGET_DATABASE_URL='postgresql://...-pooler...'

# New PostgreSQL 18 target, direct URL
TARGET_DIRECT_DATABASE_URL='postgresql://...'

# Direct source URL using the dedicated replication role
REPLICATION_SOURCE_URL='postgresql://etl_region_replication:...'
```

Load the variables:

```bash
set -a
source .env
set +a
```

Check that they are loaded without printing secrets:

```bash
test -n "$SOURCE_DATABASE_URL" && echo "SOURCE_DATABASE_URL loaded"
test -n "$TARGET_DATABASE_URL" && echo "TARGET_DATABASE_URL loaded"
test -n "$TARGET_DIRECT_DATABASE_URL" && echo "TARGET_DIRECT_DATABASE_URL loaded"
test -n "$REPLICATION_SOURCE_URL" && echo "REPLICATION_SOURCE_URL loaded"
```

---

# Phase 1 — Create migration folders

```bash
mkdir -p sql/region_migration
mkdir -p scripts/region_migration
mkdir -p docs/runbooks
mkdir -p docs/adr
mkdir -p docs/evidence/region_migration
```

Expected structure:

```text
project-root/
├── src/
├── sql/
│   ├── migrations/
│   ├── queries/
│   ├── admin/
│   └── region_migration/
├── scripts/
│   └── region_migration/
└── docs/
    ├── adr/
    ├── runbooks/
    └── evidence/
        └── region_migration/
```

---

# Phase 2 — Source and target inventory

## File 1

Create:

```text
sql/region_migration/01_source_inventory.sql
```

Purpose:

- database identity
- PostgreSQL version
- `wal_level`
- database size
- extensions
- application tables
- approximate row counts
- primary keys
- tables without primary keys
- sequences

Run against the target before schema deployment:

```bash
psql "$TARGET_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/01_source_inventory.sql \
  | tee docs/evidence/region_migration/02_target_inventory_before_schema.txt
```

Run against the source:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/01_source_inventory.sql \
  | tee docs/evidence/region_migration/01_source_inventory.txt
```

Check extensions separately:

```bash
psql "$SOURCE_DATABASE_URL" -X -v ON_ERROR_STOP=1 \
  -c "SELECT extname, extversion FROM pg_extension ORDER BY extname;"
```

```bash
psql "$TARGET_DATABASE_URL" -X -v ON_ERROR_STOP=1 \
  -c "SELECT extname, extversion FROM pg_extension ORDER BY extname;"
```

---

# Phase 3 — Build the target schema

Apply migrations to the PostgreSQL 18 target:

```bash
DATABASE_URL="$TARGET_DATABASE_URL" python -m src.migrate
```

Corrective migrations added during this process:

```text
sql/migrations/004a_create_posts_enriched_snapshot_if_missing.sql
sql/migrations/008_create_missing_core_tables.sql
```

Validate the target schema:

```bash
psql "$TARGET_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/01_source_inventory.sql \
  | tee docs/evidence/region_migration/03_target_inventory_after_schema.txt
```

Check migration history:

```bash
psql "$TARGET_DATABASE_URL" -X -v ON_ERROR_STOP=1 \
  -c "SELECT version, applied_at FROM schema_migrations ORDER BY version;"
```

---

# Phase 4 — Compare source and target schemas

## File 2

Create:

```text
sql/region_migration/02_schema_manifest.sql
```

Purpose:

- detailed columns
- data types
- nullability
- defaults
- identity settings
- primary and unique constraints
- indexes
- replica identity

Generate source manifest:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/02_schema_manifest.sql \
  > docs/evidence/region_migration/04_source_schema_manifest.txt
```

Generate target manifest:

```bash
psql "$TARGET_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/02_schema_manifest.sql \
  > docs/evidence/region_migration/05_target_schema_manifest.txt
```

Compare:

```bash
diff -u \
  docs/evidence/region_migration/04_source_schema_manifest.txt \
  docs/evidence/region_migration/05_target_schema_manifest.txt \
  | tee docs/evidence/region_migration/06_schema_manifest_diff.txt
```

Create assessment:

```text
docs/evidence/region_migration/07_schema_compatibility_assessment.md
```

Document:

- compatible columns and types
- approved differences
- tables included in replication
- tables excluded from replication

Replication scope:

```text
Included:
- comments_raw
- etl_run_log
- posts_enriched_history
- posts_enriched_snapshot
- posts_raw
- users_raw

Excluded:
- schema_migrations
- posts_enriched_stage
```

---

# Phase 5 — Enable logical replication on the source

Enable logical replication in the old Neon source project.

Verify:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "SELECT current_setting('wal_level') AS wal_level;"
```

Expected:

```text
logical
```

Save evidence:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "
SELECT
    current_database() AS database_name,
    current_setting('server_version') AS server_version,
    current_setting('wal_level') AS wal_level;
" \
  | tee docs/evidence/region_migration/08_source_logical_replication_enabled.txt
```

---

# Phase 6 — Create the publication

## File 3

Create:

```text
sql/region_migration/03_create_publication.sql
```

Run against the source:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/03_create_publication.sql \
  | tee docs/evidence/region_migration/09_source_publication_created.txt
```

Verify that no publication exists on the target:

```bash
psql "$TARGET_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "SELECT pubname FROM pg_publication ORDER BY pubname;"
```

---

# Phase 7 — Create and grant the replication role

Create the role on the existing source production branch:

```text
etl_region_replication
```

Verify:

```bash
psql "$SOURCE_DATABASE_URL" -X -v ON_ERROR_STOP=1 \
  -c "
SELECT rolname, rolreplication
FROM pg_roles
WHERE rolname = 'etl_region_replication';
"
```

Expected:

```text
rolreplication = true
```

## File 4

Create:

```text
sql/region_migration/04_grant_replication_access.sql
```

Run:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/04_grant_replication_access.sql \
  | tee docs/evidence/region_migration/10_replication_role_access.txt
```

Test the dedicated direct URL:

```bash
psql "$REPLICATION_SOURCE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "
SELECT
    current_user,
    current_database(),
    current_setting('wal_level') AS wal_level;
"
```

Confirm table access:

```bash
psql "$REPLICATION_SOURCE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "SELECT COUNT(*) AS posts_raw_count FROM public.posts_raw;"
```

---

# Phase 8 — Create the target subscription

Confirm the direct target connection:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "
SELECT current_user, current_database(), current_setting('server_version');
"
```

Confirm the replicated target tables are empty:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" -X -v ON_ERROR_STOP=1 \
  -c "
SELECT 'posts_raw' AS table_name, COUNT(*) AS row_count FROM posts_raw
UNION ALL
SELECT 'users_raw', COUNT(*) FROM users_raw
UNION ALL
SELECT 'comments_raw', COUNT(*) FROM comments_raw
UNION ALL
SELECT 'etl_run_log', COUNT(*) FROM etl_run_log
UNION ALL
SELECT 'posts_enriched_snapshot', COUNT(*) FROM posts_enriched_snapshot
UNION ALL
SELECT 'posts_enriched_history', COUNT(*) FROM posts_enriched_history
ORDER BY table_name;
"
```

## File 5

Create:

```text
sql/region_migration/05_create_subscription.sql
```

Run against the direct target URL:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/05_create_subscription.sql \
  | tee docs/evidence/region_migration/11_target_subscription_created.txt
```

---

# Phase 9 — Validate initial replication

## File 6

Create:

```text
sql/region_migration/06_validate_replication.sql
```

Run:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/06_validate_replication.sql \
  | tee docs/evidence/region_migration/12_initial_replication_status.txt
```

Expected:

```text
state_code = r
state_description = READY
```

---

# Phase 10 — Reconcile source and target data

## Python file 1

Create:

```text
scripts/region_migration/reconcile.py
```

The script compares:

- row counts
- full-table SHA-256 hashes

Run:

```bash
python scripts/region_migration/reconcile.py \
  | tee docs/evidence/region_migration/13_data_reconciliation.txt
```

Expected:

```text
RECONCILIATION RESULT: PASS
```

---

# Phase 11 — Continuous replication canary test

Create a unique canary ID:

```bash
CANARY_RUN_ID="region-migration-canary-$(date -u +%Y%m%dT%H%M%SZ)"
echo "$CANARY_RUN_ID"
```

Insert on source:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -v run_id="$CANARY_RUN_ID" <<'SQL'
INSERT INTO public.etl_run_log (
    run_id,
    status,
    message
)
VALUES (
    :'run_id',
    'STARTED',
    'Controlled logical-replication canary'
);
SQL
```

Verify source:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -v run_id="$CANARY_RUN_ID" <<'SQL'
SELECT id, run_id, status, message
FROM public.etl_run_log
WHERE run_id = :'run_id';
SQL
```

Verify target:

```bash
sleep 3
```

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -v run_id="$CANARY_RUN_ID" <<'SQL'
SELECT id, run_id, status, message
FROM public.etl_run_log
WHERE run_id = :'run_id';
SQL
```

Delete from source:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -v run_id="$CANARY_RUN_ID" <<'SQL'
DELETE FROM public.etl_run_log
WHERE run_id = :'run_id';
SQL
```

Verify deletion on target:

```bash
sleep 3
```

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -v run_id="$CANARY_RUN_ID" <<'SQL'
SELECT COUNT(*) AS remaining_canary_rows
FROM public.etl_run_log
WHERE run_id = :'run_id';
SQL
```

Run reconciliation again:

```bash
python scripts/region_migration/reconcile.py \
  | tee docs/evidence/region_migration/14_post_canary_reconciliation.txt
```

---

# Phase 12 — Sequence audit

## File 7

Create:

```text
sql/region_migration/07_sequence_precheck.sql
```

Run source:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/07_sequence_precheck.sql \
  | tee docs/evidence/region_migration/15_source_sequence_precheck.txt
```

Run target:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/07_sequence_precheck.sql \
  | tee docs/evidence/region_migration/16_target_sequence_precheck.txt
```

## File 8

Create:

```text
sql/region_migration/08_sequence_state.sql
```

Run source:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/08_sequence_state.sql \
  | tee docs/evidence/region_migration/17_source_sequence_state.txt
```

Run target:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/08_sequence_state.sql \
  | tee docs/evidence/region_migration/18_target_sequence_state.txt
```

---

# Phase 13 — Pre-cutover freeze and validation

Pause all source writes:

- extraction jobs
- Spark jobs
- pipeline execution
- manual inserts or updates
- scheduled jobs

Run replication validation:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/06_validate_replication.sql \
  | tee docs/evidence/region_migration/19_pre_cutover_replication_status.txt
```

Run final reconciliation:

```bash
python scripts/region_migration/reconcile.py \
  | tee docs/evidence/region_migration/20_pre_cutover_reconciliation.txt
```

---

# Phase 14 — Synchronize target sequences

## Python file 2

Create:

```text
scripts/region_migration/sync_sequences.py
```

Run:

```bash
python scripts/region_migration/sync_sequences.py \
  | tee docs/evidence/region_migration/21_sequence_synchronization.txt
```

Verify:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/08_sequence_state.sql \
  | tee docs/evidence/region_migration/22_target_sequence_state_after_sync.txt
```

Verify `is_called`:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "
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
"
```

Expected:

```text
etl_run_log_id_seq            | 10 | true
posts_enriched_history_id_seq |  1 | false
```

---

# Phase 15 — Final pre-cutover checks

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/06_validate_replication.sql \
  | tee docs/evidence/region_migration/23_final_replication_status.txt
```

```bash
python scripts/region_migration/reconcile.py \
  | tee docs/evidence/region_migration/24_final_reconciliation.txt
```

---

# Phase 16 — Cut over the application

Update `.env`:

```env
DATABASE_URL='TARGET_POSTGRESQL_18_APPLICATION_URL'
```

Reload:

```bash
unset DATABASE_URL
set -a
source .env
set +a
```

Run the application health check:

```bash
python -m src.db_healthcheck
```

Verify PostgreSQL version:

```bash
psql "$DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "
SELECT
    current_database() AS database_name,
    current_user AS connected_user,
    current_setting('server_version') AS server_version;
"
```

Expected:

```text
PostgreSQL 18.4
```

---

# Phase 17 — Post-cutover write test

## File 9

Create:

```text
sql/region_migration/09_post_cutover_smoke_test.sql
```

Run:

```bash
psql "$DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/09_post_cutover_smoke_test.sql \
  | tee docs/evidence/region_migration/25_post_cutover_write_test.txt
```

Expected:

- insert succeeds
- generated ID is safe
- cleanup succeeds
- no fake row remains

---

# Phase 18 — Post-cutover validation

## File 10

Create:

```text
sql/region_migration/10_post_cutover_validation.sql
```

Run:

```bash
psql "$DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/10_post_cutover_validation.sql \
  | tee docs/evidence/region_migration/26_post_cutover_validation.txt
```

Record operational observations, including historical incomplete `STARTED` ETL runs.

---

# Phase 19 — Finalize logical replication

## File 11

Create:

```text
sql/region_migration/11_finalize_subscription.sql
```

Run against the direct target connection:

```bash
psql "$TARGET_DIRECT_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -f sql/region_migration/11_finalize_subscription.sql \
  | tee docs/evidence/region_migration/27_subscription_finalized.txt
```

Verify the source replication slot was removed:

```bash
psql "$SOURCE_DATABASE_URL" \
  -X \
  -v ON_ERROR_STOP=1 \
  -c "
SELECT
    slot_name,
    active
FROM pg_replication_slots
WHERE slot_name = 'etl_region_migration_slot';
"
```

Expected:

```text
0 rows
```

---

# Final file order

```text
sql/region_migration/
├── 01_source_inventory.sql
├── 02_schema_manifest.sql
├── 03_create_publication.sql
├── 04_grant_replication_access.sql
├── 05_create_subscription.sql
├── 06_validate_replication.sql
├── 07_sequence_precheck.sql
├── 08_sequence_state.sql
├── 09_post_cutover_smoke_test.sql
├── 10_post_cutover_validation.sql
└── 11_finalize_subscription.sql
```

```text
scripts/region_migration/
├── reconcile.py
└── sync_sequences.py
```

```text
docs/evidence/region_migration/
├── 01_source_inventory.txt
├── 02_target_inventory_before_schema.txt
├── 03_target_inventory_after_schema.txt
├── 04_source_schema_manifest.txt
├── 05_target_schema_manifest.txt
├── 06_schema_manifest_diff.txt
├── 07_schema_compatibility_assessment.md
├── 08_source_logical_replication_enabled.txt
├── 09_source_publication_created.txt
├── 10_replication_role_access.txt
├── 11_target_subscription_created.txt
├── 12_initial_replication_status.txt
├── 13_data_reconciliation.txt
├── 14_post_canary_reconciliation.txt
├── 15_source_sequence_precheck.txt
├── 16_target_sequence_precheck.txt
├── 17_source_sequence_state.txt
├── 18_target_sequence_state.txt
├── 19_pre_cutover_replication_status.txt
├── 20_pre_cutover_reconciliation.txt
├── 21_sequence_synchronization.txt
├── 22_target_sequence_state_after_sync.txt
├── 23_final_replication_status.txt
├── 24_final_reconciliation.txt
├── 25_post_cutover_write_test.txt
├── 26_post_cutover_validation.txt
└── 27_subscription_finalized.txt
```

---

# Migration result

```text
Source:
- Neon old region
- PostgreSQL 17.10
- x86_64

Target:
- Neon new supported region
- PostgreSQL 18.4
- aarch64

Method:
- PostgreSQL logical replication

Result:
- schema migration PASS
- initial data copy PASS
- continuous replication PASS
- full reconciliation PASS
- sequence synchronization PASS
- application cutover PASS
- target write test PASS
- subscription cleanup PASS
```
