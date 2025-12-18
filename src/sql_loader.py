from pathlib import Path
_SQL_DIR= Path(__file__).resolve().parent.parent / "sql"


def load_sql(filename: str) -> str:
    path = _SQL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")



