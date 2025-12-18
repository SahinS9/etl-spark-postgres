from sqlalchemy import text
from sqlalchemy.orm import Session

from .sql_loader import load_sql

_SQL_RUN_START = load_sql("etl_run_log_start.sql")
_SQL_RUN_SUCCESS = load_sql("etl_run_log_success.sql")
_SQL_RUN_FAILED = load_sql("etl_run_Log_failed.sql")
_SQL_RUN_POSTS_RAW = load_sql("upsert_posts_raw.sql")

def log_run_started(session: Session, run_id: str) -> None:
    session.execute(text(_SQL_RUN_START), {"run_id":run_id})

def log_run_success(session: Session, run_id: str) -> None:
    session.execute(text(_SQL_RUN_SUCCESS), {"run_id": run_id})

def log_run_failed(session: Session, run_id: str) -> None:
    session.execute(text(_SQL_RUN_FAILED), {"run_id": run_id})

def upsert_posts_raw(session: Session, rows: list[dict]) -> int:
    result = session.execute(text(_SQL_RUN_POSTS_RAW), rows)
    return result.rowcount or 0 #rowcount is reported by the database driver after the SQL statement is executed
    