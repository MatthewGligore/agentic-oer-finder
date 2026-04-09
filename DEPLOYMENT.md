# Phase 6: Deployment and Monitoring
## Agentic OER Finder – Local Demo & Render Deployment

---

## Primary Path: Local Demo (April 9)

For the April 9 deadline, the primary deployment method is **local demo** (run on your laptop during presentation).

### Local Demo Runbook

#### Step 1: Ensure Environment is Ready

```bash
# Terminal 1: Navigate to project directory
cd /Users/mgligore/code/agentic-oer-finder

# Activate Python environment
source .venv/bin/activate

# Verify .env is configured
cat .env
# Expected: SUPABASE_URL, SUPABASE_ANON_KEY, OPENAI_API_KEY (can be empty)

# Verify requirements installed
pip list | grep -E "flask|supabase|beautifulsoup"
# Expected: Flask, supabase, beautifulsoup4 present
```

#### Step 2: Start Backend

```bash
# Still in Terminal 1
python run.py

# Expected output:
# INFO:werkzeug:WARNING: This is a development server. Do not use it in a production environment.
# Flask app running on http://localhost:8000
# Press Ctrl+C to quit
```

#### Step 3: Start Frontend (New Terminal)

```bash
# Terminal 2
cd /Users/mgligore/code/agentic-oer-finder/frontend

# Verify npm packages installed
npm list react react-dom

# Start dev server
npm run dev

# Expected output:
# ➜  local:   http://localhost:3000/
# ➜  press h to show help
```

#### Step 4: Open Browser & Test

```bash
# Open browser (any terminal)
open http://localhost:3000

# Or manually: type http://localhost:3000 in your browser address bar
```

#### Step 5: Run Demo Queries

In the browser at http://localhost:3000:

1. **Search for ENGL 1101**
   - Type `ENGL 1101` in search box
   - Click "Search"
   - Wait ~7 seconds
   - **Expected:** 2+ results with titles, links, licenses, scores

2. **Search for ITEC 1001**
   - Type `ITEC 1001`
   - Click "Search"
   - **Expected:** 2+ IT-relevant resources

3. **Try edge case: ZZZZ 9999**
   - Type `ZZZZ 9999` (non-existent course)
   - Click "Search"
   - **Expected:** Graceful "no results" or sensible fallback

**Demo Time:** ~3–5 minutes for full walkthrough

#### Step 6: Verify Health Check (Optional/Background)

```bash
# Terminal 3 (separate)
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "backend_available": true}
```

#### Step 7: Stop Services

```bash
# When demo is complete:

# Terminal 1 (backend): Ctrl+C
# Terminal 2 (frontend): Ctrl+C
```

### Local Demo Troubleshooting

| Issue | Solution |
|-------|----------|
| **Backend won't start: "Address already in use"** | Change port: `python run.py --port 8001`, then update frontend API URL to `http://localhost:8001` |
| **Frontend won't start: "EACCES permission denied"** | Try `npm install` again, or use a different port: `npm run dev -- --port 3001` |
| **No results returned** | Check backend logs for Supabase errors; system should fall back to live scraping; if stuck, clear browser cache and retry |
| **CORS error in browser console** | Verify CORS is enabled in `backend/app.py`; default should allow `localhost:3000` |
| **Supabase connection fails** | Verify `.env` has valid SUPABASE_URL and SUPABASE_ANON_KEY; if missing, system falls back to live scraper (slower but functional) |

---

## Secondary Path: Render Deployment (Ready for Post-April 9)

Once April 9 demo is complete, you can deploy to Render (free tier).

### Render Deployment Checklist

**Prerequisites:**
- [ ] GitHub account with project pushed
- [ ] Render.com account (free tier available)
- [ ] Supabase project set up with valid credentials

### Step 1: Prepare Code for Deployment

```bash
# Ensure requirements.txt is up-to-date
cd /Users/mgligore/code/agentic-oer-finder/backend
pip freeze > requirements.txt

# Verify frontend builds
cd /Users/mgligore/code/agentic-oer-finder/frontend
npm run build
# Expected: dist/ folder created with static files

# Commit to GitHub
git add -A
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Backend Service on Render

1. Go to **https://dashboard.render.com**
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository (authorize if needed)
4. Configure:
   - **Name:** `agentic-oer-finder-backend`
   - **Environment:** Python
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && gunicorn app:app`
   - **Port:** 8000
5. Add Environment Variables (from `.env`):
   - `SUPABASE_URL=...`
   - `SUPABASE_ANON_KEY=...`
   - `SUPABASE_SERVICE_ROLE_KEY=...`
   - `OPENAI_API_KEY=` (can be empty for no-API mode)
   - `DEFAULT_LLM_PROVIDER=no_api`
6. Click **"Deploy"**
7. Wait for build to complete (~2 minutes)
8. Note the backend URL (e.g., `https://agentic-oer-finder-backend.onrender.com`)

### Step 3: Create Frontend Service on Render

1. In Render dashboard, click **"New +"** → **"Static Site"**
2. Connect GitHub repository (same as backend)
3. Configure:
   - **Name:** `agentic-oer-finder-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/dist`
4. Add Environment Variable:
   - `VITE_API_URL=https://agentic-oer-finder-backend.onrender.com/api` (replace with your backend URL)
5. Click **"Deploy"**
6. Wait for build to complete (~3 minutes)
7. Note the frontend URL (e.g., `https://agentic-oer-finder-frontend.onrender.com`)

### Step 4: Smoke Test Deployed App

```bash
# Test backend health
curl https://agentic-oer-finder-backend.onrender.com/api/health

# Test frontend in browser
open https://agentic-oer-finder-frontend.onrender.com

# Search for a course
# Type "ENGL 1101" and submit
# Expected: Results appear within 10–15 seconds (slightly slower than local due to cold startup)
```

### Step 5: Configure Auto-Deploy (Optional)

In Render dashboard:
- Go to backend service
- Click **"Settings"** → **"Auto-Deploy"** → Enable
- Render will automatically redeploy on GitHub push

---

## Simple Monitoring Plan

**April 9 – May 5 (Recognition Event):**

### Weekly Checks (15 minutes)

1. **Verify Services Are Running**
   ```bash
   # If deployed to Render:
   curl https://[backend-url]/api/health
   # Expected: 200 OK
   ```

2. **Manual Search Test** (in browser or curl)
   ```bash
   curl -X POST https://[backend-url]/api/search \
     -H "Content-Type: application/json" \
     -d '{"course_code":"ENGL 1101"}'
   # Expected: 200 OK with 2+ resources
   ```

3. **Check Logs for Errors** (Render dashboard)
   - Go to service → **"Logs"**
   - Look for ERROR or WARNING messages
   - Note any patterns

4. **Document Issues** (GitHub Issues or text file)
   - Issue: [describe]
   - When: [date/time]
   - Resolution: [action taken or pending]

### What to Monitor

| Issue | Severity | Action |
|-------|----------|--------|
| Backend returns 500 errors | 🔴 CRITICAL | Restart service; check logs; notify |
| Frontend UI is broken | 🟡 HIGH | Check Render logs; redeploy if needed |
| No database connectivity | 🟡 HIGH | Verify Supabase credentials; restart backend |
| Slow response (>30 sec) | 🟠 MEDIUM | Check server load; consider upgrading if needed |
| Typos/grammar in results | 🟢 LOW | Document for post-event fixes |

### Issue Escalation

If issue blocks functionality:
1. Check logs (Render dashboard)
2. Attempt restart (Render dashboard → "Restart")
3. Check GitHub for recent commits
4. Review `.env` variables in Render dashboard
5. Rollback to known-good version if needed

---

## "How to Use" Instructions (For Users/Faculty)

**To be provided alongside live URL (if deployed) or during demo:**

### Local Demo Instructions (For April 9 Presentation)

```
1. Open http://localhost:3000 in your browser
2. Enter a GGC course code (e.g., "ENGL 1101")
3. Click "Search"
4. Review the OER results:
   - Click any link to view the full resource on ALG or other site
   - Note the license (should be CC BY or similar open license)
   - Use the integration guidance to plan how to use in your course
5. Try another course code or adjust your search
```

### Deployed App Instructions (For May 5 Recognition Event or Post-April-9)

```
1. Go to: [LIVE URL]
2. Enter your course code (or try "ENGL 1101")
3. Click "Search"
4. Review results within 10–15 seconds
5. Click resource links to view materials
6. Verify licenses and decide to adopt
```

---

## Deployment Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│ DEVELOPMENT (April 7–9)                             │
│ Local machine (localhost:3000 & localhost:8000)    │
│ Primary method for April 9 deadline                │
└─────────────────────────────────────────────────────┘
                    │
                    ▼ (If needed post-April-9)
┌─────────────────────────────────────────────────────┐
│ PRODUCTION (Render Deployment)                      │
│ Frontend: https://agentic-oer-finder-frontend... │
│ Backend:  https://agentic-oer-finder-backend...  │
│ Database: Supabase (cloud PostgreSQL)             │
└─────────────────────────────────────────────────────┘
```

---

## Roll-Back Plan

If a deployment fails:

1. **Before April 9:** Use local demo (always available as fallback)
2. **After April 9 (if deployed):**
   - Go to Render dashboard → desired service
   - Click **"Deploy"** (or **"Restart"**)
   - Or roll back to previous commit on GitHub; Render will auto-redeploy

---

## Files and Scripts

| File/Script | Purpose |
|-------------|---------|
| `run.py` | Starts Flask backend locally |
| `frontend/package.json` | npm scripts for frontend (build, dev, preview) |
| `backend/config.py` | Configuration defaults and environment handling |
| `.env` | Local env vars (Supabase credentials, LLM provider) |
| `Render` dashboard | Deployment and monitoring UI |

---

## Deliverable Summary

✅ **Local demo runbook:** Step-by-step to start, test, and stop  
✅ **Edge case troubleshooting:** Common issues and solutions  
✅ **Render deployment checklist:** Ready for post-April-9 deployment  
✅ **Monitoring plan:** Weekly checks and issue escalation  
✅ **"How to use" instructions:** For both local demo and deployed version  
✅ **Roll-back plan:** If deployed, how to recover from failures  

---

**Document Status:** ✅ Phase 6 Complete (Local) / ⏳ Render (Secondary, Post-April-9)  
**Created:** April 7, 2026  
**Next Phase:** Phase 7 – Scaling and Optimization (Optional, Post-April-9)
