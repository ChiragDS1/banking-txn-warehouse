"""Connection helper. Provided."""
from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg


def dsn() -> str:
    return os.environ.get("DATABASE_URL", "postgresql://bank:bank@localhost:5432/warehouse")


@contextmanager
def connect():
    """One transaction per `with` block: commits on success, rolls back on any error."""
    with psycopg.connect(dsn()) as conn:
        yield conn
