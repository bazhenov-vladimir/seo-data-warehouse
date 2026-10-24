.PHONY: setup start stop status validate-demo import-demo summary test public-check

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
