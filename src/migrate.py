from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import text
from .config import validate_config, PROJECT_ROOT
from .db import get_engine

SQL_DIR_MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def sha_256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def list_migration_files() -> list[Path]:
    if not SQL_DIR_MIGRATIONS.exists():
        raise FileNotFoundError(f"SQL Migrations dir not found: {SQL_DIR_MIGRATIONS}")
    
    return sorted(SQL_DIR_MIGRATIONS.glob('*.sql'))


def ensure_schema_migrations(conn) -> None:
    conn.execute(
        text(
            """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                checksum TEXT NOT NULL, 
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
            """
        )
    )


def main() -> None:
    validate_config()
    engine = get_engine()

    files = list_migration_files()
    if not files:
        print("[migrate.py] no migration files found.")
        return
    
    with engine.begin() as conn:
        ensure_schema_migrations(conn)

        applied = {
            row["version"]: row["checksum"]
            for row in conn.execute(text("Select version, checksum FROM schema_migrations")).mappings().all()
        }

        pending: list[tuple[str, str, str]] = [] #version, checksum, sql

        for path in files:
            version = path.name
            sql = path.read_text(encoding="utf-8")
            checksum = sha_256_text(sql)

            if version in applied:
                if applied[version] != checksum:
                    raise RuntimeError(f"Migration checksum mismatch: {version}\n"
                        f"DB checksum:   {applied[version]}\n"
                        f"File checksum: {checksum}\n"
                        "Do NOT edit already-applied migrations. Create a new migration instead."
                    )

                continue
        
            pending.append((version, checksum, sql))



        if not pending:
            print("[migrate.py] up to date (no pending migrations)")
            return 
        
        for version, checksum, sql in pending:
            print(f"[migrate.py] applying {version}")

            conn.execute(text(sql))
            conn.execute(
                text("INSERT INTO schema_migrations (version, checksum) VALUES (:v, :c)"), {"v": version, "c": checksum},
            )

            print(f"[migrate.py] applied {version}")

        print(f"[migrate.py] done. Applied {len(pending)} migration(s).")


if __name__ == "__main__":
    main()
