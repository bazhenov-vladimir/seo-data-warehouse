# Google Search Console setup

The starter can import finalized Search Analytics data with the read-only Search Console scope. The setup uses a service account so scheduled imports can run without an interactive browser login.

## Security first

A service-account JSON file contains a private key. Treat it like a password.

- Never attach it to an issue, email it casually, or commit it to Git.
- Store it only as `credentials/gsc-service-account.json` in this project.
- The `credentials/` directory is ignored by Git and mounted read-only in Docker.
- If a key is exposed, disable or delete it in Google Cloud and create a replacement.

## 1. Prepare Google Cloud

1. Create or select a Google Cloud project.
2. Enable the **Google Search Console API**.
3. Create a dedicated service account with no broad Google Cloud roles.
4. Create a JSON key only if a more secure keyless authentication option is not available.
5. Save the downloaded file as:

```text
credentials/gsc-service-account.json
```

## 2. Give the service account access to Search Console

Copy `client_email` from the JSON file. In Search Console, open the required property and go to **Settings → Users and permissions**. Add that email as a restricted or full user. Only a property owner can add users.

## 3. Configure the property

Open `.env` and set:

```dotenv
GSC_SITE_CODE=my_site
GSC_SITE_NAME=My Site
GSC_PROPERTY=sc-domain:example.com
```

Use the property identifier exactly as Search Console defines it:

- Domain property: `sc-domain:example.com`
- URL-prefix property: `https://www.example.com/`

The defaults import seven finalized days ending three days ago:

```dotenv
GSC_LOOKBACK_DAYS=7
GSC_LAG_DAYS=3
GSC_SEARCH_TYPE=web
```

## 4. Verify access

```bash
make gsc-check
```

The command reports only the property and permission level. It does not print the private key.

## 5. Test without changing the database

```bash
make import-gsc-dry-run
```

The dry run prints only row and metric totals; it does not print queries or page URLs.

## 6. Import data

```bash
make import-gsc
```

Imports are idempotent. Re-importing the same date range updates existing metric rows instead of adding duplicates.

For an explicit range:

```bash
docker compose run --rm app import-gsc \
  --start-date 2026-01-01 \
  --end-date 2026-01-31
```

## 7. Run scheduled imports

```bash
make start-gsc-scheduler
make gsc-logs
```

The scheduler runs once when it starts and then every `GSC_INTERVAL_SECONDS` seconds. The default is 86,400 seconds (24 hours). Stop only the scheduler with:

```bash
make stop-gsc-scheduler
```

## Data limitations

Search Console returns up to 25,000 rows per API page; the importer follows `startRow` pagination until the last page. Google also applies internal data limits, and queries grouped by page and query may omit some lower-volume rows. This warehouse therefore stores the detailed data exposed by the API, not a guaranteed lossless event stream.

## Official references

- [Search Analytics query method](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [Querying all available Search Analytics data](https://developers.google.com/webmaster-tools/v1/how-tos/all-your-data)
- [Search Console users and permissions](https://support.google.com/webmasters/answer/7687615)
- [Google service-account key security](https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys)
