.PHONY: setup start stop status validate-demo import-demo summary test public-check gsc-check import-gsc import-gsc-dry-run start-gsc-scheduler stop-gsc-scheduler gsc-logs

setup:
	./setup.sh

start:
	docker compose up -d postgres

stop:
	docker compose down

status:
	docker compose ps

validate-demo:
	docker compose run --rm app validate data/demo_search_performance.csv

import-demo:
	docker compose run --rm app import-csv data/demo_search_performance.csv

summary:
	docker compose run --rm app summary

test:
	docker compose run --rm --entrypoint python app -m pytest

public-check:
	docker compose run --rm --entrypoint python app scripts/check_public_ready.py

gsc-check:
	docker compose run --rm app gsc-check

import-gsc-dry-run:
	docker compose run --rm app import-gsc --dry-run

import-gsc:
	docker compose run --rm app import-gsc

start-gsc-scheduler:
	docker compose --profile gsc up -d postgres gsc-scheduler

stop-gsc-scheduler:
	docker compose --profile gsc stop gsc-scheduler

gsc-logs:
	docker compose --profile gsc logs --tail=100 gsc-scheduler
