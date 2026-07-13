from __future__ import annotations

import os
from typing import TypedDict

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class SequenceConfig(TypedDict):
    table: str
    column: str
    sequence: str


SEQUENCES: list[SequenceConfig] = [
    {
        "table": "etl_run_log",
        "column": "id",
        "sequence": "etl_run_log_id_seq",
    },
    {
        "table": "posts_enriched_history",
        "column": "id",
        "sequence": "posts_enriched_history_id_seq",
    },
]


def required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value


def get_sequence_state(
    engine: Engine,
    sequence_name: str,
) -> tuple[int | None, bool]:
    query = text(
        f"""
        SELECT
            last_value,
            is_called
        FROM public.{sequence_name}
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query).mappings().one()

    last_value = row["last_value"]
    is_called = bool(row["is_called"])

    return last_value, is_called


def get_max_id(
    engine: Engine,
    table_name: str,
    column_name: str,
) -> int:
    query = text(
        f"""
        SELECT COALESCE(MAX({column_name}), 0)
        FROM public.{table_name}
        """
    )

    with engine.connect() as connection:
        maximum_id = connection.execute(query).scalar_one()

    return int(maximum_id)


def determine_target_sequence_state(
    source_last_value: int | None,
    source_is_called: bool,
    source_max_id: int,
    target_max_id: int,
) -> tuple[int, bool]:
    """
    Determine a safe target sequence state.

    Empty, unused source sequence:
        last_value = 1
        is_called = False
        next generated value = 1

    Used source sequence:
        target is set to at least the highest known sequence/table value
        is_called = True
        next generated value = safe_value + 1
    """

    source_sequence_value = source_last_value or 0

    source_is_unused = (
        source_max_id == 0
        and target_max_id == 0
        and source_is_called is False
    )

    if source_is_unused:
        return max(source_sequence_value, 1), False

    safe_value = max(
        source_sequence_value,
        source_max_id,
        target_max_id,
    )

    if safe_value < 1:
        safe_value = 1

    return safe_value, True


def synchronize_sequence(
    target_engine: Engine,
    sequence_name: str,
    safe_value: int,
    is_called: bool,
) -> None:
    query = text(
        """
        SELECT setval(
            CAST(:sequence_name AS regclass),
            :safe_value,
            :is_called
        )
        """
    )

    with target_engine.begin() as connection:
        connection.execute(
            query,
            {
                "sequence_name": f"public.{sequence_name}",
                "safe_value": safe_value,
                "is_called": is_called,
            },
        )


def main() -> None:
    load_dotenv()

    source_engine = create_engine(
        required_env("SOURCE_DATABASE_URL"),
        pool_pre_ping=True,
    )

    target_engine = create_engine(
        required_env("TARGET_DIRECT_DATABASE_URL"),
        pool_pre_ping=True,
    )

    failed = False

    try:
        for item in SEQUENCES:
            sequence_name = item["sequence"]
            table_name = item["table"]
            column_name = item["column"]

            source_last_value, source_is_called = get_sequence_state(
                source_engine,
                sequence_name,
            )

            source_max_id = get_max_id(
                source_engine,
                table_name,
                column_name,
            )

            target_max_id = get_max_id(
                target_engine,
                table_name,
                column_name,
            )

            safe_value, target_is_called = (
                determine_target_sequence_state(
                    source_last_value=source_last_value,
                    source_is_called=source_is_called,
                    source_max_id=source_max_id,
                    target_max_id=target_max_id,
                )
            )

            print(
                f"{sequence_name}: "
                f"source_last={source_last_value}, "
                f"source_called={source_is_called}, "
                f"source_max={source_max_id}, "
                f"target_max={target_max_id}, "
                f"setting_target={safe_value}, "
                f"target_called={target_is_called}"
            )

            synchronize_sequence(
                target_engine=target_engine,
                sequence_name=sequence_name,
                safe_value=safe_value,
                is_called=target_is_called,
            )

            target_last_value, actual_target_is_called = (
                get_sequence_state(
                    target_engine,
                    sequence_name,
                )
            )

            sequence_passed = (
                target_last_value == safe_value
                and actual_target_is_called == target_is_called
            )

            if sequence_passed:
                print(
                    f"{sequence_name}: verification=PASS"
                )
            else:
                failed = True
                print(
                    f"{sequence_name}: verification=FAIL, "
                    f"actual_last={target_last_value}, "
                    f"actual_called={actual_target_is_called}"
                )

        if failed:
            raise RuntimeError(
                "One or more target sequences failed verification"
            )

        print("SEQUENCE SYNCHRONIZATION: PASS")

    finally:
        source_engine.dispose()
        target_engine.dispose()


if __name__ == "__main__":
    main()