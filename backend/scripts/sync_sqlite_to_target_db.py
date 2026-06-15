from __future__ import annotations

import argparse
import importlib
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select, tuple_
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional for this utility.
    load_dotenv = None

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if load_dotenv:
    load_dotenv(BACKEND_DIR / ".env")

from core.config import settings
from core.database import Base


MODEL_MODULES = [
    "ai_chat",
    "booking",
    "capacity",
    "checkin",
    "customer_profile",
    "dish",
    "favorite",
    "moderation_log",
    "notification",
    "owner_profile",
    "restaurant",
    "restaurant_taxonomy",
    "review",
    "search_history",
    "user",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy missing rows from local SQLite seed DB to another WHAT2EAT database."
    )
    parser.add_argument("--source-url", default=os.getenv("SOURCE_DATABASE_URL") or settings.DATABASE_URL)
    parser.add_argument("--target-url", default=os.getenv("TARGET_DATABASE_URL"))
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--create-tables", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target_url = _normalize_database_url(args.target_url)
    source_url = _normalize_database_url(args.source_url)
    if not target_url:
        raise SystemExit("Missing TARGET_DATABASE_URL. Pass --target-url or set TARGET_DATABASE_URL.")
    if source_url == target_url:
        raise SystemExit("Source and target database URLs are the same. Refusing to sync.")

    _load_models()
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)

    if args.create_tables and not args.dry_run:
        Base.metadata.create_all(bind=target_engine)

    print(f"Source: {_safe_url(source_url)}")
    print(f"Target: {_safe_url(target_url)}")
    print(f"Mode: {'dry-run' if args.dry_run else 'write'}")

    total_inserted = 0
    total_seen = 0
    with Session(source_engine) as source, Session(target_engine) as target:
        for table in Base.metadata.sorted_tables:
            seen, inserted = _sync_table(
                source=source,
                target=target,
                table=table,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                target_dialect=target_engine.dialect.name,
            )
            total_seen += seen
            total_inserted += inserted
            print(f"{table.name}: source={seen}, inserted={inserted}")

    print(f"Done. Source rows scanned: {total_seen}. Rows inserted: {total_inserted}.")


def _load_models() -> None:
    for module_name in MODEL_MODULES:
        importlib.import_module(f"models.{module_name}")


def _sync_table(
    *,
    source: Session,
    target: Session,
    table: Any,
    batch_size: int,
    dry_run: bool,
    target_dialect: str,
) -> tuple[int, int]:
    primary_keys = list(table.primary_key.columns)
    if not primary_keys:
        return 0, 0

    rows_seen = 0
    rows_inserted = 0
    result = source.execute(select(table))

    for batch in _chunks(result.mappings(), batch_size):
        rows = [dict(row) for row in batch]
        if not rows:
            continue

        rows_seen += len(rows)
        missing_rows = _missing_primary_key_rows(target, table, primary_keys, rows)
        if dry_run:
            rows_inserted += len(missing_rows)
            continue
        if not missing_rows:
            continue

        inserted = _insert_rows(target, table, missing_rows, target_dialect)
        rows_inserted += inserted
        target.commit()

    return rows_seen, rows_inserted


def _missing_primary_key_rows(target: Session, table: Any, primary_keys: list[Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(primary_keys) == 1:
        pk = primary_keys[0]
        values = [row[pk.name] for row in rows]
        existing = set(target.execute(select(pk).where(pk.in_(values))).scalars().all())
        return [row for row in rows if row[pk.name] not in existing]

    key_columns = [table.c[column.name] for column in primary_keys]
    values = [tuple(row[column.name] for column in primary_keys) for row in rows]
    existing_rows = target.execute(select(*key_columns).where(tuple_(*key_columns).in_(values))).all()
    existing = {tuple(row) for row in existing_rows}
    return [row for row in rows if tuple(row[column.name] for column in primary_keys) not in existing]


def _insert_rows(target: Session, table: Any, rows: list[dict[str, Any]], target_dialect: str) -> int:
    try:
        if target_dialect == "postgresql":
            statement = postgres_insert(table).values(rows).on_conflict_do_nothing()
            result = target.execute(statement)
        else:
            result = target.execute(table.insert(), rows)
        return max(result.rowcount or 0, 0)
    except IntegrityError:
        target.rollback()
        inserted = 0
        for row in rows:
            try:
                if target_dialect == "postgresql":
                    statement = postgres_insert(table).values(row).on_conflict_do_nothing()
                    result = target.execute(statement)
                else:
                    result = target.execute(table.insert(), row)
                target.commit()
                inserted += max(result.rowcount or 0, 0)
            except IntegrityError:
                target.rollback()
        return inserted


def _chunks(rows: Iterable[Any], size: int) -> Iterable[list[Any]]:
    chunk: list[Any] = []
    for row in rows:
        chunk.append(row)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _normalize_database_url(url: str | None) -> str:
    if not url:
        return ""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def _safe_url(url: str) -> str:
    if "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" in rest:
        rest = rest.split("@", 1)[1]
    return f"{scheme}://{rest}"


if __name__ == "__main__":
    main()
