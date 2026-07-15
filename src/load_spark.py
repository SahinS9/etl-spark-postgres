import os
import uuid
from dataclasses import dataclass
from urllib.parse import parse_qsl, unquote, urlencode, urlparse

from pyspark.sql import DataFrame, SparkSession

from .config import DATABASE_URL, validate_config
from .spark_session import get_spark
from .transform import build_posts_enriched_stage
from .utils import current_epoch_ms

@dataclass(frozen=True)
class JdbcConfig:

    url: str
    properties: dict[str, str]


def parse_database_url_to_jdbc(database_url: str) -> JdbcConfig:
    """modify postgresql connection url into spark jdbc config"""

    parsed = urlparse(database_url)

    #to accept SQLAlchemy schemes as postgresql+pyscopg
    database_scheme = parsed.scheme.split("+", maxsplit=1) [0]

    if database_scheme not in {"postgresql", "postgres"}:
        raise ValueError(
            f"unsupported database scheme: {parsed.scheme!r}"
        )
    
    database_name = parsed.path.lstrip("/")

    if not database_name:
        raise ValueError(
            "Database url must include a database name"
        )
    
    if not parsed.username:
        raise ValueError(
            "Database url must include a username"
        )
    
    if not parsed.hostname:
        raise ValueError(
            "Database URL must include a hostname"
        )    

    if parsed.password is None:
        raise ValueError(
            "Database url must include a password"
        )

    port = parsed.port or 5432

    query_parameters = dict(
        parse_qsl(
            parsed.query
            ,keep_blank_values=True
        )
    )

    jdbc_url = (
        f"jdbc:postgresql://"
        f"{parsed.hostname}:{port}/"
        f"{database_name}"
    )

    if query_parameters:
        jdbc_url = (
            f"{jdbc_url}?"
            f"{urlencode(query_parameters)}"
        )

    properties = {
        "user": unquote(parsed.username)
        ,"password": unquote(parsed.password)
        ,"driver": "org.postgresql.Driver"
    }

    return JdbcConfig(
        url=jdbc_url
        ,properties=properties
    )


def read_table(
        spark: SparkSession
        ,jdbc: JdbcConfig
        ,table_name: str
) ->DataFrame:
    "read pstgsql table through spark jdbc"
    return (
        spark.read
        .format("jdbc")
        .option("url", jdbc.url)
        .option("dbtable", table_name)
        .options(**jdbc.properties)
        .load()
    )

def write_table_append(
        dataframe: DataFrame
        ,jdbc: JdbcConfig
        ,table_name: str
) -> None:
    "append spark df to pstgsql table"

    (dataframe.write
     .format("jdbc")
     .mode("append")
     .option("url", jdbc.url)
     .option("dbtable", table_name)
     .options(**jdbc.properties)
     .save()
     )
    

def run(run_id: str | None=None) -> str:
    validate_config()

    spark_database_url = os.getenv(
        "SPARK_DATABASE_URL",
        DATABASE_URL or ""
    )

    if not spark_database_url:
        raise RuntimeError(
            "SPARK_DATABASE_URL or DATABASE_URL must be configured"
        )
    
    effective_run_id = run_id or uuid.uuid4().hex
    run_epoch_ms = current_epoch_ms()

    spark = get_spark(
        "etl-project"
    )

    try:
        jdbc = parse_database_url_to_jdbc(
            spark_database_url
        )

        posts_df = read_table(
            spark
            ,jdbc
            ,"public.posts_raw"
        )

        users_df = read_table(
            spark
            ,jdbc
            ,"public.users_raw"
        )

        comments_df = read_table(
            spark
            ,jdbc
            ,"public.comments_raw"

        )

        stage_df = build_posts_enriched_stage(
            posts_df = posts_df
            ,users_df = users_df
            ,comments_df = comments_df
            ,run_id = effective_run_id
            ,run_epoch_ms = run_epoch_ms
        )

        write_table_append(
            stage_df
            ,jdbc
            ,"public.posts_enriched_stage"
        )

        return effective_run_id
    
    finally:
        spark.stop()


if __name__ == "__main__":
    completed_run_id = run()

    print(
        "[load_spark.py] stage load complete: "
        f"run_id={completed_run_id}"
    )
