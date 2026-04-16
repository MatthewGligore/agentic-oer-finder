# Agentic OER Finder

Agentic OER Finder helps faculty discover open educational resources by course code, then ranks results with rubric and license checks.

## Documentation Index

| Doc | Purpose |
|---|---|
| [README.md](README.md) | Main quick start and project overview |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design and runtime flow |
| [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) | Live demo prep and fallback steps |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Local and hosted deployment patterns |
| [SUPABASE_SETUP.md](SUPABASE_SETUP.md) | Optional Supabase setup and seeding |
| [backend/README.md](backend/README.md) | Backend API and CLI guide |
| [frontend/README.md](frontend/README.md) | Frontend run/build guide |
| [docs/archive/README.md](docs/archive/README.md) | Archived planning and phase docs |

## Polished Demo State

- Frontend: React + Vite on `http://localhost:3000`
- Backend: Flask API on `http://localhost:8000`
- Default mode: `no_api` (works without OpenAI/Anthropic keys)
- Optional: Supabase-backed syllabus context for stronger relevance

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10-3.13 (recommended)

### 1) Install Dependencies

```bash
# from repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd frontend
npm install
cd ..
```

### 2) Configure Environment

```bash
cp .env.example .env
```

The app runs in local `no_api` mode by default. Supabase is optional.

### 3) Run the App

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

Open `http://localhost:3000`.

## Demo Flow

1. Search a course code such as `ENGL 1101` or `ITEC 1001`.
2. Review ranked resources and license information.
3. Open a resource link and show integration guidance.

See `DEMO_CHECKLIST.md` for a ready-to-run presenter checklist.

## API Quick Reference

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

## Core Documentation

- `ARCHITECTURE.md` - current system architecture
- `DEMO_CHECKLIST.md` - presentation and smoke-test checklist
- `DEPLOYMENT.md` - local and hosted deployment options
- `SUPABASE_SETUP.md` - optional Supabase setup
- `backend/README.md` - backend API and service details
- `frontend/README.md` - frontend details and build notes
- `docs/archive/README.md` - archived planning and phase docs

## Archived Docs

Legacy phase/planning docs were moved from the repository root into `docs/archive/` to keep the polished demo surface clean.

## Troubleshooting

### Frontend cannot reach backend

- Confirm backend is running on `http://localhost:8000`.
- Confirm `frontend/vite.config.js` proxy target is `http://localhost:8000`.

### Port conflict

```bash
PORT=9000 python run.py
```

Then update the frontend proxy target to the same port.
