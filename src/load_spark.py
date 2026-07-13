from __future__ import annotations

import time
import uuid

from dataclasses import dataclass
from urllib.parse import urlparse

from pyspark.sql import DataFrame, SparkSession

from .config import DATABASE_URL, validate_config
from .spark_session import get_spark


@dataclass (frozen=True)
class JdbcConfig:
    url: str
    props: dict[str, str]

def parse_database_rul_to_jdbc(database_url: str) -> JdbcConfig:
    #Convert SQLAlchemy-style DATABASE_URL into Spark JDBC url + properties. 

    parsed = urlparse(database_url)

    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError(f"Unsopperted DB scheme: {parsed.scheme}")
    
    if not parsed.hostname or not parsed.path:
        raise ValueError(f"DATABASE_URL must include hostname and database name")
    
    port = parsed.port or 5432
    jdbc_url = f"jdbc:postgresql://{parsed.hostname}:{port}{parsed.path}"

    props: dict[str, str] = {
        "user": parsed.username or "",
        "password": parsed.password or "",
        "drive": "org.postgresql.Drive",
    }

    return JdbcConfig(url=jdbc_url, props=props)


def read_table(spark: SparkSession, jdbc: JdbcConfig, table: str) -> DataFrame:
    return (
        spark.read.format("jdbc")
        .option("url", jdbc.url)
        .option("dbtable", table)
        .option("user", jdbc.props["user"])
        .option("password", jdbc.props["password"])
        .option("driver", "org.postgresql.Driver")
        .load()
    )

def write_table_append(df: DataFrame, jdbc: JdbcConfig, table: str) -> None:
    (
        df.write.format("jdbc")
        .mode("append")
        .option("url", jdbc.url)
        .option("dbtable", table)
        .option("user", jdbc.props["user"])
        .option("password", jdbc.props["password"])
        .option("driver", "org.postgresql.Driver")
        .save()
    )

def run(run_id: str | None = None) -> str:
    # Spark job entrypoiint

    validate_config()
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    
    run_id = run_id or uuid.uuid4().hex
    run_epoch_ms = int(time.time()*1000)

    spark = get_spark("posts-enriched-etl")

    try:
        jdbc = parse_database_rul_to_jdbc(DATABASE_URL)

        posts_df = read_table(spark, jdbc, "posts_raw")
        users_df = read_table(spark, jdbc, "users_raw")
        comments_df = read_table(spark, jdbc, "comments_raw")

        from .transform import build_posts_enriched_stage

        stage_df = build_posts_enriched_stage(
            posts_df=posts_df,
            users_df=users_df,
            comments_df=comments_df,
            run_id=run_id,
            run_epoch_ms=run_epoch_ms,
        )

        write_table_append(stage_df, jdbc, "posts_enriched_stage")

        return run_id
    
    finally:
        spark.stop()