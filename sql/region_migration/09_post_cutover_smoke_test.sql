\echo '=== POST-CUTOVER TARGET WRITE TEST ==='

BEGIN;

INSERT INTO public.etl_run_log (
    run_id,
    status,
    message
)
VALUES (
    'post-cutover-target-smoke-test',
    'STARTED',
    'Controlled PostgreSQL 18 target write test'
)
RETURNING
    id,
    run_id,
    status;

DELETE FROM public.etl_run_log
WHERE run_id = 'post-cutover-target-smoke-test';

COMMIT;

\echo '=== VERIFY TEST ROW CLEANUP ==='

SELECT COUNT(*) AS remaining_test_rows
FROM public.etl_run_log
WHERE run_id = 'post-cutover-target-smoke-test';

\echo '=== VERIFY TARGET SEQUENCE ==='

SELECT
    last_value,
    is_called
FROM public.etl_run_log_id_seq;