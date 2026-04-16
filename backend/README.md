# Backend (Flask API)

Backend service for course-based OER discovery and evaluation.

## Quick Start

From repo root:

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
python run.py
```

Default backend URL: `http://localhost:8000`

## Endpoints

### Health

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

## CLI Commands

```bash
python -m backend.cli search --course "ENGL 1101"
python -m backend.cli scrape-syllabuses --limit 10
```

## Configuration Notes

- Config class: `backend/config.py`
- Environment file: `.env` in repo root
- Default port: `8000`
- Recommended mode: `DEFAULT_LLM_PROVIDER=no_api`

## Logging

Logs are written under the configured log directory (default `logs/`), plus runtime logs to console.

## Tests

```bash
python backend/test_simple.py
python backend/test_courses.py
```

## Production Run

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.app:app
```

## Troubleshooting

### Missing Packages

```bash
pip install -r backend/requirements.txt
```

### CORS or Connection Errors

- Confirm backend is running on port 8000.
- Confirm frontend proxy target is `http://localhost:8000`.

### Slow Searches

- Use `DEFAULT_LLM_PROVIDER=no_api`.
- Check source connectivity and scraper logs.
