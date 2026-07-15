import uuid

from sqlalchemy.orm import Session

from .config import validate_config
from .db import get_engine
from .extract import extract_and_load_raw, format_result_message
from .load_spark import run as run_spark_stage
from .repository import (
    delete_completed_stage_runs
    ,log_run_failed
    ,log_run_started
    ,log_run_success
    ,merge_posts_enriched_history
    ,merge_posts_enriched_snapshot
)

def main() -> None:
    validate_config()

    engine = get_engine()
    run_id = uuid.uuid4().hex

    print(f"[pipeline.py] run_id={run_id}")

    with Session(engine) as session:
        log_run_started(
            session
            ,run_id
        )
        session.commit()

    with Session(engine) as session:
        with session.begin():
            deleted_stage_rows = delete_completed_stage_runs(
                session
                ,current_run_id = run_id
            )

    print(
        "[pipeline.py] stage cleanup SUCCESS: "
        f"deleted_row={deleted_stage_rows}"
    )

    try:
        with Session(engine) as session:
            with session.begin():
                extraction_result = extract_and_load_raw(
                    session=session
                    ,run_id=run_id
                )

        extraction_message = format_result_message(
            extraction_result
        )

        print(
            "[pipeline.py] extraction SUCCESS: "
            f"{extraction_message}"
        )


        completed_stage_run_id = run_spark_stage(
            run_id = run_id
        )

        if completed_stage_run_id != run_id:
            raise RuntimeError(
                "Spark stage returned an unexpected run_id"
            )
        
        print(
            "[pipeline.py] Spark stage SUCCESS: "
            f"run_id={completed_stage_run_id}"
        )


        with Session.engine() as session:
            with session.begin():
                snapshot_rows = merge_posts_enriched_snapshot(
                    session
                    ,run_id = run_id
                )

                history_rows = merge_posts_enriched_history(
                    session
                    ,run_id = run_id
                )
        
        print(
            "[pipeline.py] snapshot merge SUCCESS: "
            f"affected_rows={snapshot_rows}"
        )

        print(
            "[pipeline.py] history merge SUCCESS: "
            f"affected_rows={history_rows}"
        )

        success_message = (
            f"{extraction_message}"
            f"snapshot_rows={snapshot_rows}"
            f"history_rows={history_rows}"
            
        )

        with Session(engine) as session:
            log_run_success(
                session
                ,run_id
                ,success_message
            )

            session.commit()

        print(
            "[pipeline.py] pipeline SUCCESS: "
            f"run_id={run_id}"
        )
    except Exception as exc:
        failure_message = (
            f"{type(exc).__name__}: {str(exc).strip()}"
        )

        try:
            with Session(engine) as failure_session:
                log_run_failed(
                    failure_session
                    ,run_id
                    ,failure_message
                )
                failure_session.commit()
        
        except Exception as log_exc:
            print("[pipeline.py] failed to record pipeline: "
                  f"{type(log_exc).__name__}: {log_exc}"
                  )
            
        print(
            "[pipeline.py] pipeline FAILED: "
            f"run_id={run_id}"
            f"error={failure_message}"
        )
            
        raise


if __name__ == "__main__":
    main()