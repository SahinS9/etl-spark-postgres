from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def build_posts_enriched_stage(
        posts_df: DataFrame,
        users_df: DataFrame,
        comments_df: DataFrame,
        run_id: str,
        run_epoch_ms: int,
) -> DataFrame:
    
    comments_agg = (
        comments_df
        .groupBy(F.col("post_id"))
        .agg(F.count(F.lit(1)).cast("int").alias("comments_count"))
    )

    posts_users = (
        posts_df.alias("p")
        .join(users_df.alias("u"), F.col("p.user_id") == F.col("u.id"), "inner")
        .select(
            F.col("p.id").cast("int").alias("post_id"),
            F.col("p.user_id").cast("int").alias("user_id"),
            F.col("u.name").cast("string").alias("user_name"),
            F.col("u.email").cast("string").alias("user_email"),
            F.col("p.title").cast("string").alias("title"),
            F.col("p.body").cast("string").alias("body"),
        )
    )

    hash_input = F.concat_ws(
        "||",
        F.col("post_id").cast("string"),
        F.col("user_id").cast("string"),
        F.coalesce(F.col("user_name"), F.lit("")),
        F.coalesce(F.col("user_name"), F.lit("")),
        F.coalesce(F.col("title"), F.lit("")),
        F.coalesce(F.col("body"), F.lit("")),
        F.col("comment_count").cast("string"),
    )

    enriched = enriched.withColumn("row_hash", F.sha2(hash_input, 256))

    enriched = (
        enriched
        .withColumn("load_run_id", F.lit(run_id))
        .withColumn("load_at_epoch_ms", F.lit(int(run_epoch_ms)).cast("bigint"))
    )


    return enriched.select(
        "post_id",
        "user_id",
        "user_name",
        "user_email",
        "title",
        "body",
        "comment_count",
        "row_hash",
        "load_run_id",
        "load_at_epoch_ms"
    )

