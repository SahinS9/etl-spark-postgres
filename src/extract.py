"""
Extract step: fetch posts from external API and load into posts_raw 
Enforce idempotency using database constraints (UPSERT)
No transformations
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from typing import Any

from .config import fetch_json, validate_config, posts_url, users_url, comments_url
from .db import get_engine
from .utils import current_epoch_ms

from .repository import (
    log_run_failed,
    log_run_started,
    log_run_success,
    upsert_posts_raw,
    upsert_users_raw,
    upsert_comments_raw
)






def require_keys(
        record: dict[str, Any]
        ,required_keys: set[str]
        ,dataset_name: str
        ,
) -> None:
    "if required fileds are missing - function tests it"

    missing_keys = required_keys - record.keys()

    if missing_keys:
        raise RuntimeError(
            f"{dataset_name} record is missing required fields {sorted(missing_keys)}"
        )

def fetch_datasets() -> dict[str, list[dict[str, Any]]]:
    "raw API datasets"
    endpoint_functions = {
        "posts": posts_url
        ,"users": users_url
        ,"comments": comments_url
        ,
    }

    datasets: dict[str, list[dict[str, Any]]] = {}

    for dataset_name, url_function in endpoint_functions.items():
        url = url_function()

        print(f"[extract.py] fetching {dataset_name} from {url}")

        records = fetch_json(url)
        datasets[dataset_name] = records

        print(
            f"[extract.py] fetched"
            f"{len(records)} {dataset_name} records"

        )

    return datasets


def map_posts(
        posts: list[dict[str, Any]]
        ,run_id: str
        ,ingested_at_epoch_ms: int
        , 
        ) -> list[dict[str, Any]]:

    rows: list[dict[str, Any]] = []

    required_keys = {"id", "userId", 'title', 'body'}

    for post in posts:
        require_keys(post, required_keys, "posts")

        rows.append(
            {
                "id": int(post["id"])
                ,"user_id": int(post["userId"])
                ,"title": str(post["title"])
                ,"body": str(post["body"])
                ,"ingested_run_id": run_id
                ,"ingested_at_epoch_ms": ingested_at_epoch_ms
            }
        )



    return rows


def map_users(
        users: list[dict[str, Any]]
        ,run_id: str
        ,ingested_at_epoch_ms: int
        )  -> list[dict[str, Any]]:
    
    rows: list[dict[str, Any]] = []

    required_keys = {
        "id"
        ,"name"
        ,"username"
        ,"email"
        ,"phone"
        ,"website"
        ,"address"
        ,"company"
    }

    for user in users:
        require_keys(user, required_keys, "users")

        address = user["address"]
        company = user["company"]

        if not isinstance(address, dict):
            raise RuntimeError(
                "users record contains an invalid company object"
            )
        
        if not isinstance(company, dict):
            raise RuntimeError(
                "users record contains an invalid company object"
            )
        
        require_keys(
            address
            ,{"street", "suite", "city", "zipcode", "geo"}
            ,"users.address"
        )

        require_keys(
            company
            ,{"name", "catchPhrase", "bs"}
            ,"users.company"
        )

        geo = address["geo"]

        if not isinstance(geo, dict):
            raise RuntimeError(
                "users record contains an invalid address.geo object"
            )
        
        require_keys(
            geo
            ,{"lat", "lng"}
            ,"users.address.geo"
        )

        rows.append(
            {
                "id": int(user["id"])
                ,"name": str(user["name"])
                ,"username": str(user["username"])
                ,"email": str(user["email"])
                ,"phone": str(user["phone"])
                ,"website": str(user["website"])
                ,"address_street": str(address["street"])
                ,"address_suite": str(address["suite"])
                ,"address_city": str(address["city"])
                ,"address_zipcode": str(address["zipcode"])
                ,"address_geo_lat": str(geo["lat"])
                ,"address_geo_lng": str(geo["lng"])
                ,"company_name": str(company["name"])
                ,"company_catch_phrase": str(company["catchPhrase"])
                ,"company_bs": str(company["bs"])
                ,"ingested_run_id": run_id
                ,"ingested_at_epoch_ms": ingested_at_epoch_ms
                ,
            }
        )



    return rows


def map_comments(
        comments: list[dict[str, Any]]
        ,run_id: str
        ,ingested_at_epoch_ms: int
        ,
) -> list[dict[str, Any]]:
    
    rows: list[dict[str, Any]] = []

    required_keys = {"id", "postId", "name", "email", "body"}

    for comment in comments:
        require_keys(comment, required_keys, "comments")

        rows.append(
            {
                "id": int(comment["id"])
                ,"post_id": int(comment["postId"])
                ,"name": str(comment["name"])
                ,"email": str(comment["email"])
                ,"body": str(comment["body"])
                ,"ingested_run_id": run_id
                ,"ingested_at_epoch_ms": ingested_at_epoch_ms
            }
        )



    return rows
    





def extract_and_load_raw(
        session: Session
        ,run_id: str
        ,ingested_at_epoch_ms: int | None=None
        ,
) -> dict[str,int]:
    
    "transaction and run-status management"

    timestamp_ms = (
        ingested_at_epoch_ms
        if ingested_at_epoch_ms is not None
        else current_epoch_ms()
    )

    datasets = fetch_datasets()

    posts_rows = map_posts(
        datasets["posts"]
        ,run_id
        ,timestamp_ms
    )

    users_rows = map_users(
        datasets["users"]
        ,run_id
        ,timestamp_ms
    )

    comments_rows = map_comments(
        datasets["comments"]
        ,run_id
        ,timestamp_ms
    )

    inserted_posts = upsert_posts_raw(
        session
        ,posts_rows
    )

    affected_users = upsert_users_raw(
        session
        ,users_rows
    )

    affected_comments = upsert_comments_raw(
        session
        ,comments_rows
    )

    return {
        "posts_received": len(posts_rows)
        ,"posts_inserted": inserted_posts
        ,"posts_skipped": len(posts_rows) - inserted_posts
        ,"users_received": len(users_rows)
        ,"users_affected": affected_users
        ,"comments_received": len(comments_rows)
        ,"comments_affected": affected_comments
    }


def format_result_message(result: dict[str, int]) -> str:
    return (
        f"posts_received= {result['posts_received']},"
        f"posts_inserted = {result['posts_inserted']},"
        f"posts_skipped = {result['posts_skipped']},"
        f"users_received = {result['users_received']},"
        f"users_affected = {result['users_affected']},"
        f"comments_received = {result['comments_received']},"
        f"comments_affected = {result['comments_affected']},"
    )

def main() -> None:
    validate_config()

    engine = get_engine()
    run_id = uuid.uuid4().hex

    print(f"[extract.py] run_id={run_id}")

    with Session(engine) as session:
        log_run_started(session, run_id)
        session.commit()

    try:
        with Session(engine) as session:
            with session.begin():
                result = extract_and_load_raw(
                    session=session
                    ,run_id=run_id
                )

                result_message = format_result_message(result)

                log_run_success(
                    session
                    ,run_id
                    ,result_message
                )
        print(f"[extract.py] SUCCESS: {result_message}")

    except Exception as exc:
        failure_message = str(exc)#.strip()[:1500]

        if not failure_message:
            failure_message = type(exc).__name__

        try:
            with Session(engine) as failure_session:
                log_run_failed(
                    failure_session,
                    run_id,
                    failure_message,
                )
                failure_session.commit()

        except Exception as log_exc:
            print(
                "[extract.py] failed to record run failure: "
                f"{type(log_exc).__name__}: {log_exc}"
            )

        print(
            f"[extract.py] FAILED: "
            f"{type(exc).__name__}: {failure_message}"
        )

        raise

if __name__ == "__main__":
    main()