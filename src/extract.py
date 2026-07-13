"""
Extract step: fetch posts from external API and load into posts_raw 
Enforce idempotency using database constraints (UPSERT)
No transformations
"""

import time
import uuid

from sqlalchemy.orm import Session

from .config import fetch_json, validate_config, posts_url, users_url, comments_url
from .db import get_engine

from .repository import (
    log_run_failed,
    log_run_started,
    log_run_success,
    upsert_posts_raw,
    upsert_users_raw,
    upsert_comments_raw
)




def new_epoch_ms() -> int:
    return int(time.time()*1000)

def main() -> None:
    validate_config()
    engine = get_engine()

    run_id = uuid.uuid4().hex
    ingested_at_ms=new_epoch_ms()

    print(f"[extract.py] run_id={run_id}")


    datasets: dict[str, list[dict[str, Any]]] = {}
    
    for name, url_fn in [
        ("posts", posts_url),
        ("users", users_url),
        ("comments", comments_url),
    ]:
        url = url_fn()
        print(f"extract.py Get {url}")
        datasets[name] = fetch_json(url)
        print(f"[extract.py] fetched {len(datasets[name])} {name} records")
    

    posts = datasets["posts"]
    users = datasets["users"]
    comments = datasets["comments"]
    
    posts_rows = [
        {"id": int(p["id"]),
         "user_id": int(p["userId"]),
         "title": str(p["title"]),
         "body": str(p["body"]),
         "ingested_run_id": run_id,
         "ingested_at_epoch_ms": ingested_at_ms
         }
         for p in posts
    ]

    users_rows = [
        {
            "id": int(u["id"]),
            "name": str(u["name"]),
            "username": str(u["username"]),
            "email": str(u["email"]),
            "phone": str(u["phone"]),
            "website": str(u["website"]),
            "address_street": str(u["address"]["street"]),
            "address_suite": str(u["address"]["suite"]),
            "address_city": str(u["address"]["city"]),
            "address_zipcode": str(u["address"]["zipcode"]),
            "address_geo_lat": str(u["address"]["geo"]["lat"]),
            "address_geo_lng": str(u["address"]["geo"]["lng"]),
            "company_name": str(u["company"]["name"]),
            "company_catch_phrase": str(u["company"]["catchPhrase"]),
            "company_bs": str(u["company"]["bs"]),
            "ingested_run_id": run_id,
            "ingested_at_epoch_ms": ingested_at_ms
        }    
        for u in users
    ]

    comments_rows = [
        {
            "id": int(c["id"]),
            "post_id": int(c["postId"]),
            "name": str(c["name"]),
            "email": str(c["email"]),
            "body": str(c["body"]),
            "ingested_run_id": run_id,
            "ingested_at_epoch_ms": ingested_at_ms
        }

        for c in comments
    ]




    with Session(engine) as session:
        try:
            log_run_started(session, run_id)
            session.commit()

            with session.begin():
                inserted_posts  = upsert_posts_raw(session, posts_rows)
                affected_users = upsert_users_raw(session, users_rows)
                affected_comments = upsert_comments_raw(session, comments_rows)

                skipped_posts = len(posts_rows) - inserted_posts

                log_run_success(
                    session, 
                    run_id, 
                    (
                        f"posts_inserted={inserted_posts}, posts_skipped(existing)={skipped_posts},"
                        f"users_affected={affected_users}, comments_affected={affected_comments}"
                    ),
                )

            print(
                "[extract.py] "
                f"posts_inserted={inserted_posts}, posts_skipped={skipped_posts}, "
                f"users_affected={affected_users}, comments_affected={affected_comments}"
            )


        except Exception as exc:
            session.rollback()
            
            try:
                with Session(engine) as log_session:
                    log_run_failed(log_session, run_id, str(exc)[:500] or "Unknown failure")
                    log_session.commit()
            except Exception as log_exc:
                print("[extract.py] FAILED to log failure", log_exc)
            raise

if __name__ == "__main__":
    main()