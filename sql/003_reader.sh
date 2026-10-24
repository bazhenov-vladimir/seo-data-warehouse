#!/usr/bin/env sh
set -eu

reader_user=${WAREHOUSE_READER_USER:-seo_reader}
reader_password=${WAREHOUSE_READER_PASSWORD:-seo_reader_local_only}

psql \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --set=ON_ERROR_STOP=1 \
    --set=reader_user="$reader_user" \
    --set=reader_password="$reader_password" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'reader_user', :'reader_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'reader_user')
\gexec

SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'reader_user', :'reader_password')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'reader_user')
\gexec

SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'reader_user')
\gexec

SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA public TO %I', :'reader_user')
\gexec

SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT SELECT ON TABLES TO %I',
    current_user,
    :'reader_user'
)
\gexec
SQL
