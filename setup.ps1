$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker was not found. Install Docker Desktop and run this script again."
    Write-Host "https://www.docker.com/products/docker-desktop/"
    exit 1
}

docker compose version | Out-Null
docker info | Out-Null

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created local configuration: .env"
}

New-Item -ItemType Directory -Force -Path "credentials" | Out-Null

Write-Host "Starting PostgreSQL..."
docker compose up -d postgres

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    docker compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $ready) {
    Write-Host "PostgreSQL did not become ready. Run: docker compose logs postgres"
    exit 1
}

Write-Host "Building the importer..."
docker compose build app
Write-Host "Validating synthetic data..."
docker compose run --rm app validate data/demo_search_performance.csv
Write-Host "Importing synthetic data..."
docker compose run --rm app import-csv data/demo_search_performance.csv
Write-Host "SEO Data Warehouse Starter is ready."
docker compose run --rm app summary
