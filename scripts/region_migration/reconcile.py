from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

TABLES = {
    "comments_raw": "id"
    ,"etl_run_log": "id"
    ,"posts_enriched_history": "id"
    ,"posts_enriched_snapshot": "post_id"
    ,"posts_raw": "id"
    ,"users_raw": "id"
    ,
}


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    
    return value

def get_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)

def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    
    if hasattr(value, "isoformat"):
        return value.isoformat()
    
def calculate_table_hash(
        engine: Engine
        ,table_name: str
        ,key_column: str
        ,
) -> tuple[int, str]:
    query = text (
        f"""
        SELECT * 
        FROM public.{table_name}
        ORDER BY {key_column}
        """
    )
    
    digest = hashlib.sha256()
    row_count=0

    with engine.connect() as connection:
        rows = connection.execute(query).mappings()

        for row in rows:
            normalized = {
                key: normalize_value(value)
                for key, value in row.items()
            }

            serialized = json.dumps(
                normalized
                ,sort_keys=True
                ,separators=(",", ":")
                ,ensure_ascii=False
                ,
            )

            digest.update(serialized.encode("utf-8"))
            digest.update(b"\n")
            row_count += 1
    
    return row_count, digest.hexdigest()


def main() -> None:
    load_dotenv()

    source_url = get_required_env("SOURCE_DATABASE_URL")
    target_url = get_required_env("TARGET_DIRECT_DATABASE_URL")

    source_engine = get_engine(source_url)
    target_engine = get_engine(target_url)

    failed = False

    print(
        f"{'table':30}"
        f"{'source':>8}"
        f"{'target':>8}"
        f"{'count':>8}"
        f"{'hash':>8}"
    )

    print("-" * 72)

    try:
        for table_name, key_column in TABLES.items():
            source_count, source_hash = calculate_table_hash(
                source_engine
                ,table_name
                ,key_column
                ,
            )

            target_count, target_hash = calculate_table_hash(
                target_engine
                ,table_name
                ,key_column
                ,
            )

            count_status = "PASS" if source_count == target_count else "FAIL"
            hash_status = "PASS" if source_hash == target_hash else "FAIL"

            if count_status == "FAIL" or hash_status == "FAIL":
                failed=True

            print(
                f"{table_name:30}"
                f"{source_count:8d}"
                f"{target_count:8d}"
                f"{count_status:>8}"
                f"{hash_status:>8}"
            )

        print("-" * 72)

        if failed:
            print("RECONCILIATION RESULT: FAIL")
            sys.exit(1)

        print("RECONCILIATION RESULT: PASS")

    finally:
        source_engine.dispose()
        target_engine.dispose()

if __name__=="__main__":
    main()