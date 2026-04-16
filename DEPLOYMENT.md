# Deployment Guide

This project supports two practical deployment modes:

1. Local demo/runtime (recommended for development and live demos)
2. Hosted deployment (backend + static frontend)

## Local Deployment

### Backend

```bash
cd /path/to/agentic-oer-finder
source .venv/bin/activate
python run.py
```

Backend default: `http://localhost:8000`

### Frontend

```bash
cd /path/to/agentic-oer-finder/frontend
npm run dev
```

Frontend default: `http://localhost:3000`

### Smoke Test

```bash
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"course_code":"ENGL 1101"}'
```

## Hosted Deployment Pattern

### Backend Service

- Runtime: Python
- Build command: `pip install -r backend/requirements.txt`
- Start command: `gunicorn backend.app:app`
- Environment variables:
  - `PORT` (platform-provided or 8000)
  - `DEFAULT_LLM_PROVIDER` (typically `no_api`)
  - `SUPABASE_URL` (optional)
  - `SUPABASE_ANON_KEY` (optional)
  - `SUPABASE_SERVICE_ROLE_KEY` (optional)

### Frontend Static Site

- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/dist`
- Runtime API target:
  - If using proxy in local dev, no change
  - For hosted frontend/backend split, set your API base URL in frontend config if needed

## Post-Deploy Verification

1. Health endpoint returns HTTP 200.
2. Search endpoint returns `evaluated_resources` for a known course.
3. Browser UI loads and can complete a search flow.

## Common Issues

### Port mismatch

- Ensure backend service and proxy/API target use the same port.

### Missing dependencies

- Reinstall backend requirements and frontend packages.

### Source connectivity issues

- If Supabase is unavailable, the app should still run with fallback behavior.

## Recommended Production Hardening

1. Run backend behind Gunicorn with multiple workers.
2. Keep `DEFAULT_LLM_PROVIDER=no_api` unless keys are intentionally configured.
3. Add uptime checks for `/api/health`.
4. Capture and review logs for scrape/evaluation failures.
