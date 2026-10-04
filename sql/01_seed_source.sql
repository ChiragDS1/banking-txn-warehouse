-- Provided. Server-side COPY reads the CSVs mounted at /data inside the container.
\timing on
COPY src.customers  FROM '/data/raw/customers.csv'  WITH (FORMAT csv, HEADER true);
COPY src.accounts   FROM '/data/raw/accounts.csv'   WITH (FORMAT csv, HEADER true);
COPY src.txn_events FROM '/data/raw/txn_events.csv' WITH (FORMAT csv, HEADER true, NULL '');
ANALYZE src.customers; ANALYZE src.accounts; ANALYZE src.txn_events;
SELECT 'customers' AS t, count(*) FROM src.customers
UNION ALL SELECT 'accounts', count(*) FROM src.accounts
UNION ALL SELECT 'txn_events', count(*) FROM src.txn_events;
