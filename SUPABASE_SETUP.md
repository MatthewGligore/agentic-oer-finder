# Supabase Setup

Supabase is optional but recommended for stronger syllabus context and faster repeated searches.

## 1) Create a Supabase Project

1. Create a new project in Supabase.
2. Open Settings -> API.
3. Copy:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

Keep the service role key private.

## 2) Configure Local Environment

From repo root:

```bash
cp .env.example .env
```

Add your keys to `.env`:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## 3) Create Tables

Run the SQL in `backend/schema.sql` from the Supabase SQL editor.

Expected tables:

- `syllabuses`
- `syllabus_sections`

## 4) Optional: Seed Syllabus Data

```bash
source .venv/bin/activate
python -m backend.cli scrape-syllabuses --limit 10
```

Then scale up as needed:

```bash
python -m backend.cli scrape-syllabuses
```

## 5) Validate Runtime

Start backend and call health/search endpoints:

```bash
python run.py
curl http://localhost:8000/api/health
```

## Troubleshooting

### Invalid API key

- Re-copy keys exactly.
- Confirm `.env` is in repo root.
- Confirm keys are from the same Supabase project.

### Tables missing

- Re-run `backend/schema.sql`.
- Confirm both expected tables appear in Supabase Table Editor.

### Supabase unavailable

- The app still runs with fallback behavior; searches may be slower/less contextual.
