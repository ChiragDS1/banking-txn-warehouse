"""Shared fixtures. Provided."""
import psycopg
import pytest

from bank_etl.db import dsn


@pytest.fixture(scope="session")
def conn():
    """Live warehouse connection. Tests that need it skip when Postgres isn't up."""
    try:
        c = psycopg.connect(dsn(), connect_timeout=2)
    except psycopg.OperationalError:
        pytest.skip("Postgres not reachable; run `make up` first")
    yield c
    c.close()


@pytest.fixture
def scalar(conn):
    """scalar('SELECT count(*) ...') -> the single value."""
    def run(sql: str, params=None):
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0]
    return run
