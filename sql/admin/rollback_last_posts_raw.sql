WITH latest AS (
SELECT ingested_run_id
FROM posts_raw
ORDER BY ingested_run_id DESC
OFFSET 1
LIMIT 1;
)
DELETE FROM posts_raw
WHERE ingested_run_id = (SELECT ingested_run_id FROM latest);
