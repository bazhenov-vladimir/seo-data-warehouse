#!/usr/bin/env sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "Start Docker Desktop and run this command again."
    exit 1
fi

if [ ! -f .env ]; then
    cp .env.example .env
fi

ensure_env_default() {
    key=$1
    value=$2
    if ! grep -q "^${key}=" .env; then
        printf '%s=%s\n' "$key" "$value" >> .env
    fi
}

ensure_env_default METABASE_PORT 3000
ensure_env_default METABASE_ADMIN_EMAIL admin@example.local
ensure_env_default METABASE_ADMIN_PASSWORD local_admin_2026
ensure_env_default METABASE_SESSION_SECRET local_session_secret_2026
ensure_env_default METABASE_DB_NAME metabase_app
ensure_env_default METABASE_DB_USER metabase_app
ensure_env_default METABASE_DB_PASSWORD metabase_app_local_only
ensure_env_default WAREHOUSE_READER_USER seo_reader
ensure_env_default WAREHOUSE_READER_PASSWORD seo_reader_local_only

echo "Starting the warehouse and Metabase..."
docker compose --profile dashboard up -d postgres metabase-db metabase
docker compose exec -T postgres sh /docker-entrypoint-initdb.d/003_reader.sh

echo "Creating the read-only connection and starter dashboard..."
docker compose --profile dashboard run --rm metabase-provision

dashboard_port=$(sed -n 's/^METABASE_PORT=//p' .env | tail -n 1)
printf '\nDashboard: http://localhost:%s\n' "${dashboard_port:-3000}"
echo "Login details are stored in your local .env file."
