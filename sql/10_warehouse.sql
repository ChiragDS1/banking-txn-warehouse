-- YOU WRITE THIS (Week 1, Day 2 — Lesson 0002).
-- Star schema in schema `dw`. Re-runnable: drop and recreate.
--
-- Write the grain of each table as a comment above it before writing any columns.
--
-- Required tables:
--   dw.dim_customer      SCD Type 2 on (home_state, city, segment).
--                        surrogate key, natural key, valid_from, valid_to, is_current.
--   dw.dim_account       Type 1 is fine. Link to the customer how? Decide and justify in docs/decisions.md.
--   dw.dim_date          One row per calendar day, Jul 1 - Dec 31 2026 (generate_series).
--   dw.dim_merchant      (optional) category + name.
--   dw.fact_transaction  Grain: one row per txn_id, latest version only.
--                        Which customer surrogate key does a July transaction get
--                        after the customer moves in October? Write the answer down.
--
-- Constraints to include: primary keys, foreign keys, NOT NULLs, a CHECK on amount,
-- and a partial unique index guaranteeing one current row per customer in dim_customer.

DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;
