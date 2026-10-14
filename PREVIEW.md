# Branch preview

The current checkout is served at https://courtoracle.fyi. Deployment builds the
working tree, including uncommitted changes; it does not commit or merge anything.
The site uses the restored local database configured in the root `.env`.

The real `.env` stays private on the server and is not part of Git. `.env.example`
documents the required variables without credentials. The existing database is
named `oracle_db_restored_20261013` because the backup was restored separately
from the initial `oracle_db`; keep that name in this machine's `.env`. Changing
the variable alone selects another database and does not rename or copy data.

```bash
# Build and start, or redeploy after changing files.
docker compose -f docker-compose.database.yml -f docker-compose.preview.yml up -d --build --wait

# Inspect status and app logs.
docker compose -f docker-compose.database.yml -f docker-compose.preview.yml ps
docker compose -f docker-compose.database.yml -f docker-compose.preview.yml logs --tail=100 web-frontend web-backend

# Stop just the preview while retaining the database.
docker compose -f docker-compose.database.yml -f docker-compose.preview.yml stop web-frontend web-backend
```

The frontend uses a standalone Next.js production build on Node 22. Browser API
calls stay on the site's origin; Next.js proxies `/api/` to the private Gunicorn
backend. Local development uses the same relative calls and proxies to Django on
`127.0.0.1:8000` by default. The hosted backend uses `requirements-web.txt`, with
Django 5.2 LTS and only web-serving dependencies. Data/ML dependencies stay in the
original requirements file. The web containers do not run imports, prediction
jobs, or migrations on startup.

Only the frontend joins the existing Traefik network; the backend and PostgreSQL
use the application's private Docker network. Traefik handles the domain, HTTPS
certificate, and HTTP-to-HTTPS redirect. No new host ports are published for the
web containers. PostgreSQL remains available on host loopback only.

Runtime memory limits: frontend 256 MiB, backend 192 MiB, database 256 MiB. Each
service is limited to 0.5 CPU and restarts automatically. Build-time memory can be
higher; the frontend build limits the Node heap to 512 MiB and uses one worker.
Secrets and the SQL backup are excluded from Docker build contexts and Git.

The newer CSV exports do not contain model predictions. New games display `--`
for missing predictions. To review populated recent box scores, use
https://courtoracle.fyi/home?date=2026-10-12; restored predictions are available on
historical dates such as 2025-05-02.
