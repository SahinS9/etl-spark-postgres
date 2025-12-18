"""
Extract step: fetch posts from external API and load into posts_raw 
Enforce idempotency using database constraints (UPSERT)
No transformations
"""

import time
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import POSTS_URL, fetch_json, validate_config
from .db import get_engine

from .repository import (
    log_run_failed,
    log_run_started,
    log_run_success,
    upsert_posts_raw
)



def new_epoch_ms() -> int:
    return int(time.time()*100)

def main() -> None:
    validate_config()
    engine = get_engine()

    run_id = uuid.uuid4().hex
    ingested_at_ms=new_epoch_ms()

    print(f"[extract] run_id={run_id}")
    print(f"[extract] Get {POSTS_URL}")

    posts = fetch_json(POSTS_URL)
    print(f"[extract] fetched {len(posts)} records")

    rows = [
        {"id": int(p["id"]),
         "user_id": int(p["userId"]),
         "title": str(p["title"]),
         "body": str(p["body"]),
         "ingested_run_id": run_id,
         "ingested_at_epoch_ms": ingested_at_ms
         }
         for p in posts
    ]

    with Session(engine) as session:
        try:
            log_run_started(session, run_id)
            session.commit()

            inserted = upsert_posts_raw(session, rows)
            session.commit()

            skipped = len(rows) - inserted
            log_run_success(session, run_id, f"inserted={inserted}, skipped(existing)={skipped}")
            session.commit()

        except Exception as exc:
            session.rollback()
            try:
                log_run_failed(session, run_id, str(exc)[:500])
                session.commit()
            except Exception:
                session.rollback()
            raise

if __name__ == "__main__":
    main()