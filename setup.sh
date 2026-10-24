#!/usr/bin/env sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker was not found. Install Docker Desktop and run this script again."
    echo "https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose is unavailable. Start or update Docker Desktop."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but not running. Start Docker Desktop and try again."
    exit 1
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created local configuration: .env"
fi

mkdir -p credentials

echo "Starting PostgreSQL..."
docker compose up -d postgres

attempt=0
until docker compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
        echo "PostgreSQL did not become ready. Run: docker compose logs postgres"
        exit 1
    fi
    sleep 2
done

docker compose exec -T postgres sh /docker-entrypoint-initdb.d/003_reader.sh

echo "Building the importer..."
docker compose build app

echo "Validating synthetic data..."
docker compose run --rm app validate data/demo_search_performance.csv

echo "Importing synthetic data..."
docker compose run --rm app import-csv data/demo_search_performance.csv

echo "\nSEO Data Warehouse Starter is ready.\n"
docker compose run --rm app summary

echo "\nUseful commands:"
echo "  make status"
echo "  make summary"
echo "  make import-demo"
echo "  make stop"
