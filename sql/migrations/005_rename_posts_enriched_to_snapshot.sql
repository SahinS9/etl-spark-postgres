DO $$
BEGIN
    IF EXISTS(
    SELECT 1 
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'posts_enriched'
    )

    AND NOT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'posts_enriched_snapshot'
    ) THEN 
    ALTER TABLE  posts_enriched RENAME TO posts_enriched_snapshot;
    END IF;
END $$;

DO $$
BEGIN 
    IF EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'posts_enriched_snapshot'
    )
    AND NOT EXISTS (
    SELECT 1 
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'posts_enriched_snapshot'
    AND column_name = 'row_hash'
    )
    THEN
    ALTER TABLE posts_enriched_snapshot
    ADD COLUMN row_hash VARCHAR(64);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_pes_row_hash
ON posts_enriched_snapshot (row_hash);