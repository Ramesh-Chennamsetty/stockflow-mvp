# StockFlow Frontend

This folder contains the StockFlow MVP frontend.

## Local Run

Install dependencies and start Vite:

```bash
npm install
npm run dev
```

Open: http://localhost:5173

## Connect Backend

Create `.env.local`:

```text
VITE_API_URL=https://your-backend-url.onrender.com/api
```

For local backend:

```text
VITE_API_URL=http://localhost:3000/api
```

## Vercel

Set the root directory to `frontend`, use the Vite framework preset, and add
`VITE_API_URL=https://<render-service>.onrender.com/api` to all environments.
