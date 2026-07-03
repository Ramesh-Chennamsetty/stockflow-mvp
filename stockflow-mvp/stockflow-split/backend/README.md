# StockFlow API Backend

Python HTTP API backend with SQLite, sessions, tenant-scoped products, and Server-Sent Events.

## Local Run

```bash
python server.py
```

API: http://localhost:3000/api
Health: http://localhost:3000/api/health

## Render Settings

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
python server.py
```

Environment Variables:

```text
ENV=production
FRONTEND_URL=https://your-frontend-url.vercel.app
DATABASE_PATH=/var/data/stockflow.db
```

`FRONTEND_URL` may contain a comma-separated list of exact frontend origins.
Do not include URL paths or trailing slashes.

The included `render.yaml` provisions a persistent disk at `/var/data` so
accounts and inventory survive service restarts and deployments.
