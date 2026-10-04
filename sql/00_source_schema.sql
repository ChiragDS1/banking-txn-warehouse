-- Source system ("OLTP side"). Provided. Raw events land as-is, duplicates included.
DROP SCHEMA IF EXISTS src CASCADE;
CREATE SCHEMA src;

CREATE TABLE src.customers (
  customer_id  BIGINT PRIMARY KEY,
  full_name    TEXT NOT NULL,
  email        TEXT NOT NULL,
  city         TEXT,
  home_state   CHAR(2),
  segment      TEXT,
  signup_date  DATE,
  updated_at   TIMESTAMP
);

CREATE TABLE src.accounts (
  account_id   BIGINT PRIMARY KEY,
  customer_id  BIGINT NOT NULL REFERENCES src.customers,
  account_type TEXT NOT NULL,
  opened_date  DATE,
  status       TEXT
);

-- No primary key on txn_id on purpose: the feed resends events.
CREATE TABLE src.txn_events (
  event_id          BIGINT PRIMARY KEY,
  txn_id            BIGINT NOT NULL,
  account_id        BIGINT NOT NULL,
  txn_ts            TIMESTAMP NOT NULL,
  amount            NUMERIC(12,2),
  currency          CHAR(3),
  merchant_category TEXT,
  merchant_name     TEXT,
  channel           TEXT,
  status            TEXT,
  ingested_at       TIMESTAMP NOT NULL
);
