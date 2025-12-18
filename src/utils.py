from pathlib import Path
from typing import Any

from sqlalchemy import text

from .config import validate_config, PROJECT_ROOT
from .db import get_engine

SQL_DIR_ADMIN = PROJECT_ROOT / "sql" / "admin"

def run_sql_file(relative_path: str, params: dict[str, Any] | None = None) -> int:
    validate_config()
    engine = get_engine()

    sql_path = SQL_DIR_ADMIN / relative_path
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    
    sql = sql_path.read_text(encoding="utf-8")

    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {})
        return result.rowcount or 0
