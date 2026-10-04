# One command per step. `make all` runs the whole day-1 pipeline from nothing.
-include .env
export
PSQL = docker compose exec -T db psql -v ON_ERROR_STOP=1 -U $(POSTGRES_USER) -d $(POSTGRES_DB)

.PHONY: up down reset data changes source warehouse load load-day2 test lint psql all

up:          ## start Postgres and wait until healthy
	docker compose up -d --wait

down:
	docker compose down

reset:       ## drop everything, including the database volume
	docker compose down -v

data:        ## generate day-1 source files (20k customers, 1M transactions)
	python -m bank_etl.generate base --out data/raw

changes:     ## generate the day-2 customer snapshot for SCD2
	python -m bank_etl.generate changes

source:      ## create the source schema and COPY the CSVs in
	$(PSQL) -f /sql/00_source_schema.sql -f /sql/01_seed_source.sql

warehouse:   ## create the star schema (you write sql/10_warehouse.sql)
	$(PSQL) -f /sql/10_warehouse.sql

load:        ## run your idempotent load for day 1
	python -m bank_etl.load --day 1

load-day2:   ## load the day-2 customer snapshot (SCD2 changes)
	python -m bank_etl.load --day 2

test:
	pytest -q

lint:
	ruff check src tests

psql:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

all: up data source warehouse load test
