from __future__ import annotations

import os
from typing import Any, Mapping, Optional

from pyspark.sql import SparkSession


def _env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}
 
def _env_int(key: str, default: int) -> int:
    v = os.getenv(key)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def get_spark(app_name: str, configs: Optional[Mapping[str,Any]] = None) -> SparkSession:

    master = os.getenv("SPARK_MASTER", "local[*]")
    shuffle_partitions = os.getenv("SPARK_SHUFFLE_PARITIONS", 8)
    adaptive_enabled = os.getenv("SPARK_ADAPTIVE_ENABLE", True)
    timezone = os.getenv("SPARK_TIMEZONE","UTC")

    raw_level = os.getenv("SPARK_LOG_LEVEL", "WARN")
    level_map = {"WARNING":"WARN", "WARN":"WARN", "ERROR":"ERROR", "INFO":"INFO", "DEBUG":"DEBUG"}
    log_level = level_map.get(raw_level, "WARN")

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3")
        .config("spark.sql.adaptive.enabled", adaptive_enabled)
        .config("spark.sql.shuffle.paritions", shuffle_partitions)
        .config("spark.sql.session.timeZone", timezone)
    )

    if configs:
        for k, v in configs.items():
            builder = builder.config(k, str(v))

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel(log_level)
    return spark
