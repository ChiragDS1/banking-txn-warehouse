"""Unit tests for the provided generator. They also show the pytest patterns
(tmp_path, fixtures, parametrize) you'll use in test_quality.py."""
import csv
import subprocess
import sys
from collections import Counter

import pytest


@pytest.fixture(scope="module")
def raw(tmp_path_factory):
    out = tmp_path_factory.mktemp("raw")
    subprocess.run([sys.executable, "-m", "bank_etl.generate", "base", "--customers", "300",
                    "--txns", "20000", "--out", str(out)], check=True, capture_output=True)
    return out


def read(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def test_counts(raw):
    assert len(read(raw / "customers.csv")) == 300
    txn_ids = {r["txn_id"] for r in read(raw / "txn_events.csv")}
    assert len(txn_ids) == 20000


def test_feed_contains_resent_events(raw):
    dupes = [k for k, n in Counter(r["txn_id"] for r in read(raw / "txn_events.csv")).items() if n > 1]
    assert dupes, "the feed should contain some resent txn_ids to dedup"


def test_feed_contains_dirty_amounts(raw):
    amounts = [r["amount"] for r in read(raw / "txn_events.csv")]
    assert any(a == "" for a in amounts) or any(a.startswith("-") for a in amounts)


@pytest.mark.parametrize("col", ["event_id", "txn_id", "account_id", "txn_ts", "ingested_at"])
def test_required_columns_never_empty(raw, col):
    assert all(r[col] for r in read(raw / "txn_events.csv"))


def test_day2_snapshot_changes_some_customers(raw, tmp_path):
    out = tmp_path / "day2.csv"
    subprocess.run([sys.executable, "-m", "bank_etl.generate", "changes", "--pct", "0.1",
                    "--src", str(raw / "customers.csv"), "--out", str(out)], check=True,
                   capture_output=True)
    before = {r["customer_id"]: r for r in read(raw / "customers.csv")}
    after = read(out)
    changed = [r for r in after if r["customer_id"] in before and r != before[r["customer_id"]]]
    new = [r for r in after if r["customer_id"] not in before]
    assert changed and new
