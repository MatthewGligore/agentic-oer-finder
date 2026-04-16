# Architecture

Agentic OER Finder is a two-tier app:

- React frontend for search and result presentation
- Flask backend for orchestration, scraping, evaluation, and API responses

## High-Level Flow

1. User submits a course code from the UI.
2. Frontend calls `POST /api/search`.
3. Backend OER agent builds course context and candidate resources.
4. Evaluators score quality and open-license signals.
5. Backend returns ranked resources for UI rendering.

## System Components

### Frontend (`frontend/`)

- React + Vite application
- Route-driven views and reusable UI components
- API service layer in `src/services/oerAPI.js`
- Dev server on port 3000, proxying `/api` to backend

### Backend (`backend/`)

- Flask API in `app.py`
- Search orchestration in `oer_agent.py`
- Data collection in `scrapers/`
- Quality and license checks in `evaluators/`
- Optional Supabase integration in `llm/supabase_client.py`

## Data and Search Strategy

- Primary signals: course code, syllabus-derived context, keyword extraction
- Candidate sources: curated and scraped OER sources
- Ranking inputs: relevance + rubric + license checks
- Fallback behavior: return sensible defaults if upstream data is limited

## Runtime Defaults

- Frontend URL: `http://localhost:3000`
- Backend URL: `http://localhost:8000`
- API prefix: `/api`
- Default LLM mode: `no_api`

## Reliability Notes

- If Supabase is unavailable, backend still attempts fallback data paths.
- If external source retrieval is sparse, system returns fallback resources instead of failing hard.
- Health endpoint (`GET /api/health`) provides a simple runtime status check.
