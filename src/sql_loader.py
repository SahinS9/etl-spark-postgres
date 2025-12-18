from .config import PROJECT_ROOT

SQL_DIR_QUERIES = PROJECT_ROOT / "sql" / "queries"

def load_sql(filename: str) -> str:
    path = SQL_DIR_QUERIES / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")



