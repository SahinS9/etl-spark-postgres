import os
from typing import Any, Mapping

from pyspark.sql import SparkSession


def _env_bool(key:str, default: bool) -> bool:
    value = os.getenv(key)

    if value is None:
        return default
    
    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    
    raise ValueError(
        f"{key} must be a boolean, got: {value!r}"
    )


def _env_int(key:str, default: int) -> int:
    value = os.getenv(key)

    if value is None:
        return default
    
    try: 
        parsed_value = int(value)
    except ValueError as exc:
        raise ValueError(
            f"{key} must be an integer, got: {value!r}"
        ) from exc
    
    if parsed_value <= 0:
        raise ValueError(
            f"{key} must be greater than zero"
        )

    return parsed_value


def get_spark(
        app_name: str
        ,configs: Mapping[str, Any] | None=None
    ) -> SparkSession:
    "create or reuse confg spark session"

    """
    Environment variables:
    SPARK_MASTER
    SPARK_SHUFFLE
    SPARK_ADAPTIVE_ENABLED
    SPARK_TIMEZONE
    SPARK_LOG_LEVEL
    POSTGRES_JDBC_PACKAGE
    """

    master = os.getenv(
        "SPARK_MASTER"
        ,"local[*]"
    )    

    shuffle_partitions = _env_int(
        "SPARK_SHUFFLE_PARTITIONS"
        ,8
    )

    adaptive_enabled = _env_bool(
        "SPARK_ADAPTIVE_ENABLED"
        ,True
    )

    timezone = os.getenv(
        "SPARK_TIMEZONE"
        ,"UTC"
    )

    postgres_jdbc_package = os.getenv(
        "POSTGRES_JDBC_PACKAGE"
        ,"org.postgresql:postgresql:42.7.3"
    )

    raw_log_level = os.getenv(
        "SPARK_LOG_LEVEL"
        ,"WARN"
    ).strip().upper()

    allowed_log_levels = {
        "ALL"
        ,"DEBUG"
        ,"ERROR"
        ,"FATAL"
        ,"INFO"
        ,"OFF"
        ,"TRACE"
        ,"WARN"
    }

    if raw_log_level == "WARNING":
        log_level = "WARN"
    elif raw_log_level in allowed_log_levels:
        log_level = raw_log_level
    else:
        raise ValueError(
            "SPARK_LOG_LEVEL must be one of: "
            +",".join(sorted(allowed_log_levels))
        )
    
    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config(
            "spark.jars.packages"
            ,postgres_jdbc_package
        )
        .config("spark.sql.adaptive.enabled"
                ,str(adaptive_enabled).lower()
                )
        .config("spark.sql.shuffle.partitions"
                ,str(shuffle_partitions)
                )
        .config("spark.sql.session.timeZone"
                ,timezone
        )
    )
    
    if configs:
        for key, value in config.items():
            builder = builder.config(
                key
                ,str(value)
            )

    spark = builder.getOrCreate()

    spark.sparkContext.setLogLevel(log_level)

    return spark







'''
python - <<'PY'
from src.spark_session import get_spark

spark = get_spark("spark-session-test")

print(
    "Spark version:",
    spark.version,
)

print(
    "Master:",
    spark.sparkContext.master,
)

print(
    "Shuffle partitions:",
    spark.conf.get(
        "spark.sql.shuffle.partitions"
    ),
)

print(
    "Adaptive enabled:",
    spark.conf.get(
        "spark.sql.adaptive.enabled"
    ),
)

print(
    "Timezone:",
    spark.conf.get(
        "spark.sql.session.timeZone"
    ),
)

spark.stop()
PY'''