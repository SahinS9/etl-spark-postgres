CREATE TABLE IF NOT EXISTS users_raw (
    id integer PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    username VARCHAR(256) NOT NULL,
    email VARCHAR(256) NOT NULL,

    phone VARCHAR(256) NOT NULL,
    website VARCHAR(256) NOT NULL,

    address_street VARCHAR(256) NOT NULL,
    address_suite VARCHAR(256) NOT NULL,
    address_city VARCHAR(256) NOT NULL,
    address_zipcode VARCHAR(256) NOT NULL,
    address_geo_lat VARCHAR(256) NOT NULL,
    address_geo_lng VARCHAR(256) NOT NULL,

    company_name VARCHAR(256) NOT NULL,
    company_catch_phrase VARCHAR(256) NOT NULL,
    company_bs VARCHAR(256) NOT NULL,

    ingested_run_id VARCHAR(256) NOT NULL,
    ingested_at_epoch_ms BIGINT NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_users_raw_ingested_run_id
    ON users_raw (ingested_run_id);
    