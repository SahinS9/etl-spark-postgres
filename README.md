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




Pipeline run order
1. Generate new run_id
2. Confirm previous run completed successfully
3. Delete stage rows belonging to completed older runs
4. Spark writes the new run
5. Merge into snapshot/history
6. Keep this stage batch until the next successful run begins