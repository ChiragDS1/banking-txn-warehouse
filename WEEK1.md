# Week 1 build plan

Each day pairs with one lesson. "Done when" is the acceptance check: if it isn't true, the day isn't done.
Provided: generator, source schema, Compose, Makefile, CI skeleton, test fixtures.
Yours: the model, the load, the quality tests, the CI integration, the README results.

## Day 1 · Lesson 0001: Window functions
- `cp .env.example .env`, `make up data source`.
- In `make psql`, run all six Lesson 0001 patterns against `src.txn_events` (1M+ rows),
  adapted to accounts instead of customers.
- Run query 4 (velocity) with `EXPLAIN (ANALYZE, BUFFERS)`. Add one index that removes the sort. Rerun.
- **Done when:** `sql/20_queries.sql` holds all six queries, and the README results table has the
  before/after time for query 4 and the name of the plan node that disappeared.

## Day 2 · Lesson 0002: Star schema, grain and SCD2
- Write `sql/10_warehouse.sql`. Grain comment above every table.
- Answer the July-transaction question in the file, and write decision 001 (fact grain) and 002 (SCD2 keys).
- **Done when:** `make warehouse` runs twice without error, and `\d dw.dim_customer` shows the
  partial unique index on current rows.

## Day 3 · Lesson 0003: Idempotent loads
- Write `load.py` day 1 and day 2.
- **Done when:** `make load` twice → identical row counts and identical `sum(amount)`;
  `make changes load-day2` → changed customers have exactly two rows, the old one closed.

## Day 4 · Lesson 0004: Data quality as tests
- Implement every test in `tests/test_quality.py`. Remove the skip markers.
- Prove each test bites: break the data on purpose (insert a duplicate, a negative amount,
  a second current row) and watch it fail, then restore.
- **Done when:** `make test` is green with zero skips, and the README data-quality table lists
  which planted problem each check catches.

## Day 5 · Lesson 0005: Docker and CI
- Extend `.github/workflows/ci.yml` with the integration steps described in its comments.
- **Done when:** a push to GitHub shows a green run that built the warehouse from nothing,
  loaded it twice, applied day 2 and passed every quality test. Add the CI badge to the README.

## Weekend · Ship it
- Fill in README Results, At 100× scale, Talking points.
- Push to `github.com/ChiragDS1/banking-txn-warehouse`.
- 30-minute mock: I ask, you answer aloud, on window functions, modeling and idempotency.
