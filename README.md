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
2. Add the following values to `.env`:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
3. Run `backend/schema.sql` in the Supabase SQL editor.
4. (Optional) Seed syllabus data:

```bash
source .venv/bin/activate
python -m backend.cli scrape-syllabuses --limit 10
```

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

## Developer Commands

```bash
python -m backend.cli search --course "ENGL 1101"
python -m backend.cli scrape-syllabuses --limit 10
python -m pytest backend/tests/test_api_contracts.py
python -m pytest backend/tests/test_oer_agent_search_profile.py
```

## Troubleshooting

- **Frontend cannot reach backend:** confirm backend is running at `http://localhost:8000` and frontend proxy target points to that URL.
- **Port conflict:** run backend on a different port, for example `PORT=9000 python run.py`, and update frontend proxy settings to match.
