ALTER TABLE public.posts_enriched_stage
ADD CONSTRAINT uq_posts_enriched_stage_run_post
UNIQUE (load_run_id, post_id);