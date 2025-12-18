"""
Simple database connectivity health check.
Used to validate DATABASE_URL and network access before running ETL pipelines.
"""

from sqlalchemy import text

from .config import validate_config
from .db import get_engine

def main() -> None:
    validate_config()
    engine = get_engine()

    print("db_healthcheck testing connection...")

    with engine.connect() as conn:
        row = conn.execute(text("select 1 as ok")).mappings().one()
        print(f"db_healthcheck Connected {row}")


if __name__ == "__main__":
    main()