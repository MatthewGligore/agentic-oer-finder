# Supabase Setup Guide

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Click **"New Project"**
4. Fill in:
   - **Project name**: `agentic-oer-finder` (or similar)
   - **Database password**: Create a strong password (save it securely)
   - **Region**: Select region closest to you (e.g., US-East-1)
5. Click **"Create new project"** and wait for provisioning (~1-2 min)

## Step 2: Get Your Credentials

Once the project is ready:

1. Go to **Settings** → **API** (left sidebar)
2. Copy these three values and add to your `.env` file:
   ```
   SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```
   
   ⚠️ **Security**: The `SERVICE_ROLE_KEY` is sensitive—treat like an API secret. Never commit to git.

3. Create a `.env` file in the `backend/` directory:
   ```bash
   cp backend/.env.example backend/.env
   # Then edit backend/.env and paste your keys
   ```

## Step 3: Create Database Schema

1. In Supabase console, go to **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Copy the contents of [schema.sql](schema.sql) (file in this repo)
4. Paste into the SQL editor and click **"Run"**
5. Verify tables appear in **Table Editor**:
   - `syllabuses`
   - `syllabus_sections`

You should see:
- Table list in left sidebar
- Column details: id, course_code, course_title, term, section_number, course_id, instructor_name, syllabus_url, scraped_at, created_at
- Similar for `syllabus_sections`

## Step 4: Verify Setup

In a Python shell (backend activated):
```python
from backend.llm.supabase_client import get_supabase_client
client = get_supabase_client()
result = client.table('syllabuses').select('*').execute()
print(f"Connected! Tables exist: {result.data is not None}")
```

If you see a success message, you're ready to start scraping!

## Next Steps

After setup, run the bulk scraper:
```bash
cd backend
python cli.py scrape-syllabuses --limit 10  # Test with 10 syllabuses first
python cli.py scrape-syllabuses --all       # Full scrape (takes ~30-60 min depending on library size)
```

Monitor progress in console. Check Supabase console to see data populate in real-time.

## Troubleshooting

**Error: "Invalid API key"**
- Copy credentials exactly (no extra spaces)
- Ensure `.env` file is in `backend/` directory (not root)
- Verify keys are from the correct Supabase project

**Error: "Table not found"**
- Run schema.sql again in Supabase SQL Editor
- Refresh page and check **Table Editor** shows tables

**Connection timeout**
- Check internet connection
- Verify Supabase project is running (Status page in console)
- Try again in 30 seconds
