DO $$
BEGIN
    -- Rename only if old column exists and new one doesn't
    IF EXISTS (
        SELECT 1 --Return a constant value (1) — without caring about table data
        FROM information_schema.columns
        WHERE table_name = 'etl_run_log'
          AND column_name = 'runid'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'etl_run_log'
          AND column_name = 'run_id'
    ) THEN
        ALTER TABLE etl_run_log RENAME COLUMN runid TO run_id;
    END IF;
END $$;
