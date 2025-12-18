CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    checksum TEXT NOT NULL, --checksum is a fingerprint of a file, short string - If the contents change → the checksum changes
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);