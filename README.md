This project builds an end-to-end ETL pipeline using Python, PostgreSQL, SQLAlchemy, Apache Spark, and Neon.

The pipeline extracts posts, users, and comments from the JSONPlaceholder API, loads the raw data into PostgreSQL,
 transforms the datasets with Spark, and maintains both a current snapshot and a historical record of changes.

.
├── sql
│   ├── migrations
│   └── queries
├── src
│   ├── config.py
│   ├── db.py
│   ├── extract.py
│   ├── load_spark.py
│   ├── migrate.py
│   ├── models.py
│   ├── pipeline.py
│   ├── repository.py
│   ├── spark_session.py
│   ├── sql_loader.py
│   ├── transform.py
│   └── utils.py
├── .env.example
├── requirements.txt
└── README.md




JSONPlaceholder API
        ↓
posts_raw
users_raw
comments_raw
        ↓
Spark join + transform + row_hash
        ↓
posts_enriched_stage
        ↓
        ├── posts_enriched_snapshot
        │      one latest row per post
        │
        └── posts_enriched_history
               every changed version


The main pipeline performs these steps:

1. Creates one run ID for the complete ETL execution.
2. Records the run as STARTED.
3. Removes staging rows from previously successful runs.
4. Fetches posts, users, and comments from the API.
5. Upserts the latest source records into the raw tables.
6. Reads the raw tables with Spark.
7. Joins posts with users and aggregated comment counts.
8. Generates a SHA-256 hash for change detection.
9. Writes the transformed batch into the staging table.
10. Updates the latest snapshot.
11. Adds changed versions to the history table.
12. Records the pipeline as SUCCESS or FAILED.




Pipeline run order
1. Generate new run_id
2. Confirm previous run completed successfully
3. Delete stage rows belonging to completed older runs
4. Spark writes the new run
5. Merge into snapshot/history
6. Keep this stage batch until the next successful run begins



MAIN TABLES
Raw tables
- posts_raw
- users_raw
- comments_raw

These tables contain the latest records received from the API.


Staging table
- posts_enriched_stage

This table contains the transformed output for the latest pipeline run.


Rows are unique by: load_run_id + post_id

Completed staging rows are removed when the next pipeline run starts.


Snapshot table
- posts_enriched_snapshot

This table contains one current enriched row for each post.

A row is updated only when its calculated hash changes.

History table
- posts_enriched_history

This table stores previous versions of enriched posts.



When a post changes:
- the previous version is marked as not current
- a new version is inserted 
- unchanged records do not create additional history rows


Run log
- etl_run_log

This table records the status of each full pipeline execution.

Possible statuses include:
- STARTED
- SUCCESS
- FAILED


REQUIREMENTS:
Python 3.11
Java compatible with PySpark
PostgreSQL
Apache Spark through PySpark
PostgreSQL JDBC driver
A Neon PostgreSQL database or another compatible PostgreSQL instance


Environment variables
- Create a .env file in the project root.


DATABASE_URL=postgresql://USER:PASSWORD@POOLED_HOST/DATABASE?sslmode=require

SPARK_DATABASE_URL=postgresql://USER:PASSWORD@DIRECT_HOST/DATABASE?sslmode=require

API_BASE_URL=https://jsonplaceholder.typicode.com

SPARK_MASTER=local[*]
SPARK_SHUFFLE_PARTITIONS=8
SPARK_ADAPTIVE_ENABLED=true
SPARK_LOG_LEVEL=WARN




INSTALLATION
python -m venv .venv
source .venv/bin/activate


Database migrations

- Migrations create and update the database schema in a reproducible way.
- Database changes should be added as new migration files instead of being applied manually.


Idempotency

The project is designed to be safely rerun.
Raw source records are upserted using their source IDs.
The staging table prevents duplicate posts within the same run using: UNIQUE (load_run_id, post_id)

*The snapshot and history merges compare the incoming row_hash with the currently stored hash.


When the API data has not changed:
raw records are refreshed
a new staging batch is created
snapshot rows are not updated
history rows are not duplicated
Change detection

The enriched row hash is generated from:
- post_id
- user_id
- user_name
- user_email
- title
- body
- comment_count


Notes

Spark introduces noticeable startup time for this small dataset because it starts a JVM, loads the JDBC driver, and creates database connections.

The dataset is intentionally small, but Spark is used to demonstrate a pipeline structure that can be extended to larger workloads.




Validation queries

Check the current table totals:

SELECT
    (SELECT COUNT(*) FROM public.posts_enriched_snapshot)
        AS snapshot_rows,
    (SELECT COUNT(*) FROM public.posts_enriched_history)
        AS history_rows,
    (SELECT COUNT(*)
     FROM public.posts_enriched_history
     WHERE is_current)
        AS current_history_rows,
    (SELECT COUNT(*) FROM public.posts_enriched_stage)
        AS stage_rows;



Check recent pipeline runs:

SELECT
    run_id,
    status,
    message
FROM public.etl_run_log
ORDER BY started_at_epoch_ms DESC
LIMIT 10;



Check that only one history row is current for each post:

SELECT
    post_id,
    COUNT(*) AS current_versions
FROM public.posts_enriched_history
WHERE is_current = TRUE
GROUP BY post_id
HAVING COUNT(*) <> 1;


*A correct result returns no rows.
