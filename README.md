# Agentic OER Finder

Agentic OER Finder is a demo-ready discovery platform that helps faculty locate open educational resources (OER) by course code and returns ranked results with license and rubric-informed scoring.

## Release Overview

- **Frontend:** React + Vite, served at `http://localhost:3000`
- **Backend:** Flask API, served at `http://localhost:8000`
- **Default runtime mode:** `no_api` (works without external LLM keys)
- **Optional enhancement:** Supabase-backed syllabus context for stronger relevance

## Key Capabilities

- Search OER resources by course code and academic term
- Rank and enrich results using evaluation and licensing checks
- Provide a clean API surface for UI and integration workflows
- Support local demo execution with optional cloud data enrichment

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10-3.13

### 1) Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd frontend
npm install
cd ..
```

### 2) Configure environment

```bash
cp .env.example .env
```

The application is configured to run locally in `no_api` mode by default.

### 3) Start services

```bash
# terminal 1 (repo root)
source .venv/bin/activate
python run.py
```

```bash
# terminal 2
cd frontend
npm run dev
```

Open `http://localhost:3000` to access the interface.

## Optional Supabase Integration

1. Create a Supabase project.
2. Add the following values to **backend / repo `.env`** (used by Flask):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_JWT_SECRET` — **JWT Secret** from Supabase **Project Settings → API** (required to verify signed-in users from the frontend).
3. Run `backend/schema.sql` in the Supabase SQL editor (includes `saved_resources` per-user rows, `query_term_stats`, RLS on bookmarks, and telemetry columns).
4. **Enable Auth:** In Supabase **Authentication → Providers**, enable **Email** (password sign-up/sign-in).
5. Add **frontend** env vars (e.g. `frontend/.env.local`) — Vite only exposes variables prefixed with `VITE_`:
   - `VITE_SUPABASE_URL` — same as `SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY` — same as `SUPABASE_ANON_KEY`

When `VITE_SUPABASE_*` are unset, the UI runs in **guest mode**: search and disputes still work; saving resources opens **Sign in**. Without Supabase on the backend, saved resources remain unavailable.

6. (Optional) Seed syllabus data:

```bash
source .venv/bin/activate
python -m backend.cli scrape-syllabuses --limit 10
```

### Learning endpoints (feedback-driven ranking)

- `POST /api/learning/train-reranker` — trains the logistic reranker from global feedback.
- `POST /api/learning/mine-terms` — recomputes `query_term_stats` from impressions + feedback (improves syllabus query variants per subject).
- `GET /api/learning/term-policy?subject=ENGL` — inspect mined term weights.

Disputes and saves are stored **globally** (all users improve retrieval); **saved libraries are per user**.

## API Reference

### Health Check

```http
GET /api/health
```

### Search

```http
POST /api/search
Content-Type: application/json
```

```json
{
  "course_code": "ENGL 1101",
  "term": "Fall 2026"
}
```

### Stats

```http
GET /api/stats
```

### Auth (optional)

```http
GET /api/auth/me
```

Returns `{ "user": { "sub", "email" } | null }` depending on `Authorization: Bearer <Supabase access_token>`.

## Developer Commands

```bash
python -m backend.cli search --course "ENGL 1101"
python -m backend.cli scrape-syllabuses --limit 10
python -m pytest backend/tests/test_api_contracts.py
python -m pytest backend/tests/test_oer_agent_search_profile.py
python -m pytest backend/tests/test_term_miner.py
```

## Troubleshooting

- **Frontend cannot reach backend:** confirm backend is running at `http://localhost:8000` and frontend proxy target points to that URL.
- **Port conflict:** run backend on a different port, for example `PORT=9000 python run.py`, and update frontend proxy settings to match.
