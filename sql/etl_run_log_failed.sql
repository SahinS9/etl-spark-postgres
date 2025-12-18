UPDATE etl_run_log
SET status = "Failed",
    finished_at = now(),
    message = :message
WHERE run_id = :run_id;