"""YOU WRITE THESE (Week 1, Day 4 — Lesson 0004). Data-quality checks as tests.

Each test runs against the live warehouse after `make load`. Remove the skip
marker as you implement each one. Keep each assertion message useful: when it
fails in CI, the message is all you get.
"""
import pytest

TODO = pytest.mark.skip(reason="Week 1 Day 4: implement")


@TODO
def test_fact_one_row_per_txn_id(scalar):
    """No duplicate txn_id in dw.fact_transaction."""


@TODO
def test_fact_keeps_latest_version(scalar):
    """For resent txns, the fact row matches the src event with the latest ingested_at."""


@TODO
def test_no_bad_amounts_in_fact(scalar):
    """No NULL or negative amounts reached the fact table."""


@TODO
def test_every_fact_row_has_its_dimensions(scalar):
    """No orphan foreign keys (customer, account, date)."""


@TODO
def test_one_current_row_per_customer(scalar):
    """dim_customer: exactly one is_current row per natural key."""


@TODO
def test_scd2_validity_ranges_do_not_overlap(scalar):
    """dim_customer: for each customer, valid_from/valid_to ranges are contiguous and disjoint."""


@TODO
def test_load_is_idempotent(conn, scalar):
    """Snapshot row counts + a checksum of fact amounts, rerun the day-1 load, compare."""


@TODO
def test_source_and_warehouse_reconcile(scalar):
    """Distinct valid txn_ids in src == rows in fact. Sum of amounts matches to the cent."""
