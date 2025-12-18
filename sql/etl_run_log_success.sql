UPDATE etl_run_log
SET status = 'SUCCESS',
finished_at = now(),
message = :message
where run_id = :run_id;