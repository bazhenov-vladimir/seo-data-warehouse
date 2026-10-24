# Browser dashboard with Metabase

Metabase adds a browser interface for SEO specialists who do not want to write SQL. It runs locally and connects to the warehouse with a dedicated read-only PostgreSQL user.

## Start the dashboard

First complete the normal `./setup.sh` workflow. Then run:

```bash
./dashboard.sh
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\dashboard.ps1
```

The first start downloads the pinned open-source Metabase image and can take several minutes. Open [http://localhost:3000](http://localhost:3000) when setup finishes.

Login details are stored in your local `.env` file:

```dotenv
METABASE_ADMIN_EMAIL=admin@example.local
METABASE_ADMIN_PASSWORD=local_admin_2026
```

These defaults are intended only for a local starter installation. Change the password before using the project on a shared computer. Metabase binds to `127.0.0.1`, so it is not exposed to other computers by default.

## Included dashboard

The provisioning script creates **SEO Performance Overview** with:

- total organic clicks;
- total organic impressions;
- clicks and impressions over time;
- SEO opportunity pages;
- top landing pages for the latest 28-day window in the warehouse.

The script also creates a separate `seo_reader` PostgreSQL account with `SELECT` access only. Metabase never receives the warehouse administrator password.

## Useful commands

```bash
make dashboard-status
make dashboard-logs
make dashboard-stop
```

Stopping the dashboard preserves its questions, settings, and application database.

## Re-running provisioning

Running `./dashboard.sh` again is safe. It reuses the existing **SEO Warehouse** connection and **SEO Performance Overview** dashboard instead of creating duplicates.

## Local starter versus production

This configuration is suitable for a local portfolio project or an individual SEO specialist. A production deployment should additionally use unique secrets, TLS, backups for both PostgreSQL volumes, restricted network access, monitoring, and a documented upgrade process.

## Official references

- [Running Metabase on Docker](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker)
- [Configuring the Metabase application database](https://www.metabase.com/docs/latest/installation-and-operation/configuring-application-database)
- [Setting up Metabase through its API](https://www.metabase.com/articles/set-up-metabase-from-code-with-the-api)
- [Metabase licensing](https://www.metabase.com/license/)
