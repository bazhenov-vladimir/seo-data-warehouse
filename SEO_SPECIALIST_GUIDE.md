# Setup guide for SEO specialists

This guide assumes no programming experience. You only need Docker Desktop and the downloaded project folder.

## 1. Install Docker Desktop

Download Docker Desktop from the official Docker website, install it, and wait until it reports that Docker is running.

## 2. Download the project

On GitHub, choose **Code → Download ZIP**, extract the archive, and open the extracted folder.

## 3. Open a terminal in the project folder

- **macOS:** right-click the folder in Finder and choose **New Terminal at Folder**. If the option is unavailable, open Terminal, type `cd `, drag the folder into the Terminal window, and press Enter.
- **Windows:** right-click inside the folder and choose **Open in Terminal**.

## 4. Run the setup

On macOS or Linux:

```bash
./setup.sh
```

If macOS reports a permission error, run this once and try again:

```bash
chmod +x setup.sh
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The first run downloads the required Docker images, so it can take several minutes. A successful setup ends with a table containing `demo_docs` and `demo_shop` totals.

## 5. Check the project later

```bash
make status
make summary
```

On Windows, where `make` may not be installed:

```powershell
docker compose ps
docker compose run --rm app summary
```

## 6. Stop the project

```bash
make stop
```

Or on Windows:

```powershell
docker compose down
```

Stopping the project does not delete the imported data.

## Troubleshooting

### Docker is not running

Open Docker Desktop, wait until it is ready, and run the setup again.

### Port 55432 is already in use

Open `.env`, change `POSTGRES_PORT=55432` to another unused port such as `55433`, save the file, and run the setup again.

### View PostgreSQL logs

```bash
docker compose logs postgres
```

### Start over

The database is stored in a Docker volume. Deleting that volume permanently removes the local warehouse data, so this guide intentionally does not provide a reset command.

## What comes next

The included data is synthetic. A later release will add a guided Google Search Console connection and scheduled imports without changing the database structure.
