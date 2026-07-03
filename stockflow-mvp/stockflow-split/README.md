# StockFlow MVP - Separated Frontend and API Backend

This version separates the project into two deployable parts:

- `frontend/` - Static frontend deployed on Vercel
- `backend/` - Python API backend deployed on Render

## Deployment URLs

Frontend URL: `https://your-frontend-url.vercel.app`

Backend URL: `https://your-backend-url.onrender.com`

API Base URL: `https://your-backend-url.onrender.com/api`

## Render backend configuration

When the repository root is `stockflow-split`, use:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python server.py
```

The root `render.yaml` contains the same settings for Blueprint deployments.

## How to Connect

Set this Vercel environment variable after deploying the backend:

```text
VITE_API_URL=https://your-backend-url.onrender.com/api
```

Then redeploy frontend on Vercel.
