"""Synthetic source data for the warehouse: customers, accounts, and a raw
transaction event feed. This is the "source system" — provided, not graded.

Planted on purpose so your SQL and tests have something to find:
  * resent events: ~0.5% of transactions appear twice in the feed (same txn_id,
    later ingested_at, sometimes pending -> posted). Dedup before you load.
  * velocity bursts: ~1% of accounts get 3-5 charges inside 90 seconds.
  * outliers: ~0.2% of transactions are 20-60x the account's usual amount.
  * dirty rows: a handful of negative or null amounts for your quality checks.

Usage:
  python -m bank_etl.generate base --customers 20000 --txns 1000000 --out data/raw
  python -m bank_etl.generate changes --pct 0.02 --src data/raw/customers.csv \
      --out data/raw/customers_day2.csv
"""
from __future__ import annotations

import argparse
import csv
import random
from collections.abc import Iterator
from dataclasses import astuple, dataclass, fields
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

CATEGORIES = {  # category -> (typical amount, spread)
    "grocery": (55, 25), "fuel": (45, 15), "dining": (38, 20),
    "online_retail": (80, 60), "pharmacy": (30, 15), "electronics": (240, 180),
    "travel": (420, 300), "utilities": (110, 40),
}
SEGMENTS = ["mass", "mass", "mass", "affluent", "small_business"]
CHANNELS = ["card_present", "card_present", "online", "contactless"]
START = datetime(2026, 7, 1)
DAYS = 92  # Jul 1 - Sep 30, 2026


@dataclass(frozen=True)
class Customer:
    customer_id: int
    full_name: str
    email: str
    city: str
    home_state: str
    segment: str
    signup_date: str
    updated_at: str


@dataclass(frozen=True)
class Account:
    account_id: int
    customer_id: int
    account_type: str
    opened_date: str
    status: str


@dataclass(frozen=True)
class TxnEvent:
    event_id: int
    txn_id: int
    account_id: int
    txn_ts: str
    amount: float | None
    currency: str
    merchant_category: str
    merchant_name: str
    channel: str
    status: str
    ingested_at: str


def write_csv(path: Path, rows: Iterator, cls: type) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([fld.name for fld in fields(cls)])
        for row in rows:
            w.writerow(["" if v is None else v for v in astuple(row)])
            n += 1
    return n


def make_customers(n: int, fake: Faker, rng: random.Random) -> list[Customer]:
    out = []
    for i in range(n):
        signup = fake.date_between(start_date="-6y", end_date="-30d")
        out.append(Customer(
            customer_id=100_000 + i,
            full_name=fake.name(),
            email=fake.unique.email(),
            city=fake.city(),
            home_state=fake.state_abbr(include_territories=False),
            segment=rng.choice(SEGMENTS),
            signup_date=signup.isoformat(),
            updated_at=f"{signup.isoformat()} 00:00:00",
        ))
    return out


def make_accounts(customers: list[Customer], rng: random.Random) -> list[Account]:
    out, next_id = [], 5_000_000
    for c in customers:
        for kind in ["checking"] + (["credit"] if rng.random() < 0.55 else []):
            out.append(Account(next_id, c.customer_id, kind, c.signup_date,
                               "open" if rng.random() > 0.03 else "closed"))
            next_id += 1
    return out


def make_events(accounts: list[Account], n_txns: int, fake: Faker,
                rng: random.Random) -> Iterator[TxnEvent]:
    merchants = {c: [fake.company() for _ in range(40)] for c in CATEGORIES}
    open_accts = [a for a in accounts if a.status == "open"]
    habit = {a.account_id: rng.uniform(0.5, 1.8) for a in open_accts}  # spend scale
    bursty = set(rng.sample([a.account_id for a in open_accts], k=max(1, len(open_accts) // 100)))
    event_id, txn_id = 1, 90_000_000

    def event(acct: int, ts: datetime, amount: float | None, cat: str,
              status: str, lag_s: int) -> TxnEvent:
        nonlocal event_id
        e = TxnEvent(event_id, txn_id, acct, ts.strftime("%Y-%m-%d %H:%M:%S"),
                     amount, "USD", cat, rng.choice(merchants[cat]), rng.choice(CHANNELS),
                     status, (ts + timedelta(seconds=lag_s)).strftime("%Y-%m-%d %H:%M:%S"))
        event_id += 1
        return e

    produced = 0
    while produced < n_txns:
        acct = rng.choice(open_accts).account_id
        cat = rng.choices(list(CATEGORIES), weights=[22, 14, 18, 16, 7, 5, 3, 15])[0]
        mean, sd = CATEGORIES[cat]
        amount: float | None = round(max(1.0, rng.gauss(mean, sd)) * habit[acct], 2)
        roll = rng.random()
        if roll < 0.002:
            amount = round(amount * rng.uniform(20, 60), 2)          # outlier
        elif roll < 0.00215:
            amount = None                                            # dirty: null
        elif roll < 0.0023:
            amount = -amount                                         # dirty: negative
        ts = START + timedelta(seconds=rng.randrange(DAYS * 86400))

        burst = acct in bursty and rng.random() < 0.02
        for k in range(rng.randint(3, 5) if burst else 1):
            t = ts + timedelta(seconds=k * rng.randint(8, 25))
            if rng.random() < 0.005:                                 # resent / updated
                yield event(acct, t, amount, cat, "pending", rng.randint(1, 30))
                yield event(acct, t, amount, cat, "posted", rng.randint(300, 7200))
            else:
                yield event(acct, t, amount, cat, "posted", rng.randint(1, 30))
            txn_id += 1
            produced += 1


def make_changes(src: Path, pct: float, rng: random.Random, fake: Faker) -> list[Customer]:
    """Day-2 snapshot of customers: a fraction moved state or changed segment."""
    with src.open() as f:
        rows = [Customer(**{**r, "customer_id": int(r["customer_id"])}) for r in csv.DictReader(f)]
    changed_at = "2026-10-01 06:00:00"
    out = []
    for c in rows:
        if rng.random() < pct:
            if rng.random() < 0.6:
                c = Customer(**{**c.__dict__, "city": fake.city(),
                                "home_state": fake.state_abbr(include_territories=False),
                                "updated_at": changed_at})
            else:
                c = Customer(**{**c.__dict__, "segment": rng.choice(SEGMENTS[3:]),
                                "updated_at": changed_at})
        out.append(c)
    # a few brand-new customers arrive in the day-2 snapshot too
    start = max(c.customer_id for c in rows) + 1
    for i in range(max(1, len(rows) // 500)):
        out.append(Customer(start + i, fake.name(), fake.unique.email(), fake.city(),
                            fake.state_abbr(include_territories=False), "mass",
                            "2026-09-30", changed_at))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("base")
    b.add_argument("--customers", type=int, default=20_000)
    b.add_argument("--txns", type=int, default=1_000_000)
    b.add_argument("--seed", type=int, default=42)
    b.add_argument("--out", type=Path, default=Path("data/raw"))
    c = sub.add_parser("changes")
    c.add_argument("--pct", type=float, default=0.02)
    c.add_argument("--seed", type=int, default=43)
    c.add_argument("--src", type=Path, default=Path("data/raw/customers.csv"))
    c.add_argument("--out", type=Path, default=Path("data/raw/customers_day2.csv"))
    a = p.parse_args()

    rng, fake = random.Random(a.seed), Faker("en_US")
    Faker.seed(a.seed)
    if a.cmd == "base":
        customers = make_customers(a.customers, fake, rng)
        accounts = make_accounts(customers, rng)
        print("customers", write_csv(a.out / "customers.csv", iter(customers), Customer))
        print("accounts ", write_csv(a.out / "accounts.csv", iter(accounts), Account))
        print("events   ", write_csv(a.out / "txn_events.csv",
                                     make_events(accounts, a.txns, fake, rng), TxnEvent))
    else:
        rows = make_changes(a.src, a.pct, rng, fake)
        print("customers (day 2)", write_csv(a.out, iter(rows), Customer))


if __name__ == "__main__":
    main()
