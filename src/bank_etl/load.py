"""YOU WRITE THIS (Week 1, Day 3 — Lesson 0003): src.* -> dw.* star schema.

Rules the load must satisfy (tests in tests/test_quality.py check them):
  1. Idempotent: running `--day 1` twice leaves every dw table exactly as after one run.
  2. Dedup: fact_transaction has one row per txn_id, the latest version
     (latest ingested_at; break ties on event_id).
  3. SCD2: `--day 2` loads data/raw/customers_day2.csv. Changed customers get their
     current row closed (valid_to, is_current=false) and a new current row.
     Unchanged customers are untouched. New customers get one current row.
  4. Atomic: a failure halfway leaves the warehouse as it was (one transaction per step).
  5. Bad rows (NULL or negative amounts) never reach the fact table. Count them
     and print how many were rejected.

Suggested shape (change it if you have a better one, and say why in docs/decisions.md):
  stage_transactions()  dedup src.txn_events into a staging table with ROW_NUMBER
  load_dim_date()       generate_series, ON CONFLICT DO NOTHING
  load_dim_customer()   SCD2 merge from a snapshot table
  load_dim_account()    upsert
  load_fact()           INSERT ... ON CONFLICT (txn_id) DO UPDATE, only when changed

Do the heavy lifting in SQL inside Postgres. Python orchestrates, times each step,
and logs row counts.
"""
from __future__ import annotations

import argparse
import time

from bank_etl.db import connect


def step(name: str, conn, sql: str, params: dict | None = None) -> int:
    """Run one SQL step, print its duration and affected rows. Provided."""
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql, params or {})
        n = cur.rowcount
    print(f"{name:<24} {n:>10,} rows  {time.perf_counter() - t0:6.2f}s")
    return n


def load_day1() -> None:
    with connect() as conn:  # noqa: F841  (remove once you use conn)
        raise NotImplementedError("Week 1 Day 3: write the day-1 load")


def load_day2() -> None:
    raise NotImplementedError("Week 1 Day 3: write the SCD2 day-2 load")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--day", type=int, choices=[1, 2], required=True)
    a = p.parse_args()
    load_day1() if a.day == 1 else load_day2()


if __name__ == "__main__":
    main()
