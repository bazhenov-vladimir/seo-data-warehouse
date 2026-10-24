$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Install and start Docker Desktop, then run this command again."
    exit 1
}

docker info | Out-Null

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

function Add-EnvDefault {
    param([string]$Key, [string]$Value)
    if (-not (Select-String -Path ".env" -Pattern "^$([regex]::Escape($Key))=" -Quiet)) {
        Add-Content -Path ".env" -Value "$Key=$Value"
    }
}

Add-EnvDefault "METABASE_PORT" "3000"
Add-EnvDefault "METABASE_ADMIN_EMAIL" "admin@example.local"
Add-EnvDefault "METABASE_ADMIN_PASSWORD" "local_admin_2026"
Add-EnvDefault "METABASE_SESSION_SECRET" "local_session_secret_2026"
Add-EnvDefault "METABASE_DB_NAME" "metabase_app"
Add-EnvDefault "METABASE_DB_USER" "metabase_app"
Add-EnvDefault "METABASE_DB_PASSWORD" "metabase_app_local_only"
Add-EnvDefault "WAREHOUSE_READER_USER" "seo_reader"
Add-EnvDefault "WAREHOUSE_READER_PASSWORD" "seo_reader_local_only"

Write-Host "Starting the warehouse and Metabase..."
docker compose --profile dashboard up -d postgres metabase-db metabase
docker compose exec -T postgres sh /docker-entrypoint-initdb.d/003_reader.sh
Write-Host "Creating the read-only connection and starter dashboard..."
docker compose --profile dashboard run --rm metabase-provision
$dashboardPort = ((Select-String -Path ".env" -Pattern "^METABASE_PORT=").Line -split "=", 2)[1]
Write-Host "Dashboard: http://localhost:$dashboardPort"
Write-Host "Login details are stored in your local .env file."
