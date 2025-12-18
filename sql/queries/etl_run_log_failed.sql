UPDATE etl_run_log
SET status = 'FAILED',
    finished_at = now(),
    message = :message
WHERE run_id = :run_id;