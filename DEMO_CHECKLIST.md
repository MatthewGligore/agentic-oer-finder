# Quick Reference: April 9 Demo Checklist
## Agentic OER Finder – Live Demo Ready List

---

## The Day Before (April 8)

### Morning
- [ ] Verify backend starts: `python run.py` (should see no 401 errors)
- [ ] Verify frontend starts: `cd frontend && npm run dev` (should see localhost:3000)
- [ ] Test one search manually (ENGL 1101) to warm up the system

### Evening
- [ ] Finalize presentation narrative from RECOGNITION_EVENT.md
- [ ] Print or prepare slides (optional but helpful)
- [ ] Rehearse 2-minute demo script (3x)
- [ ] Charge laptop battery fully
- [ ] Test HDMI cable (if projector available)

---

## April 9 (Event Day)

### 15 Minutes Before Event Start

```bash
# Terminal 1: Start Backend
cd /Users/mgligore/code/agentic-oer-finder
source .venv/bin/activate
python run.py
# Wait for: "Flask app running on http://localhost:8000"

# Terminal 2: Start Frontend (new terminal/tab)
cd /Users/mgligore/code/agentic-oer-finder/frontend
npm run dev
# Wait for: "Local:   http://localhost:3000"

# Terminal 3 (optional): Keep cursor here for live demo
# Paste search commands if needed
```

### 5 Minutes Before Event start

- [ ] Open browser to `http://localhost:3000`
- [ ] Verify page loads without errors
- [ ] Test one quick search (ENGL 1101) to ensure system is warm
- [ ] Close browser (will reopen during demo)

### Demo Time (~3–5 minutes)

**[Opening Statement]**  
"I've built an AI agent that helps GGC faculty find free textbooks in seconds. Here's the problem and the solution."

**[Live Demo — 2 minutes]**

1. Open browser to http://localhost:3000
2. Type "ENGL 1101" in search box
3. Click "Search"
4. Wait 5–10 seconds for results
5. Scroll through results: titles, links, licenses, scores
6. Click one link to show actual resource

**[Brief Narrative — 3 minutes]**

Quickly summarize each phase:
- **Phase 1:** Faculty need fast OER discovery (problem)
- **Phase 2:** We use Supabase + ALG + web sources (data)
- **Phase 3:** User → Flask orchestration → tools → evaluated results (architecture)
- **Phase 4:** Built scrapers, evaluators, API, UI (development)
- **Phase 5:** Tested on 5 courses + edge cases (testing)
- **Phase 6:** Deployed locally today; Render-ready for production (deployment)
- **Phase 7:** Future: expand sources, add LMS integration, institutional dashboard (roadmap)

**[Q&A — 5 minutes]**

See RECOGNITION_EVENT.md for 10 likely questions + answers.

---

## If Anything Goes Wrong

### "Results don't appear / timeout"
1. Check Terminal 1 (backend) for errors
2. Look for "ERROR" in Flask logs
3. If Supabase error → System will fall back to live scraping (slower but works)
4. Refresh browser and retry

### "Frontend doesn't load"
1. Check Terminal 2 for VITE errors
2. Try a different port: `npm run dev -- --port 3001` (then visit localhost:3001)
3. Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### "CORS or backend connection error in browser"
1. Verify both Terminal 1 and Terminal 2 are running
2. Verify http://localhost:8000 responds: `curl http://localhost:8000/api/health`
3. Check that CORS_ORIGINS in `backend/config.py` includes localhost:3000

### "System returns empty results"
1. This should not happen (fallback suggestions always apply)
2. If it does: Check logs for Supabase error; system should return defaults
3. Try a different course: ITEC 1001

### "Laptop/internet goes down"
1. **Local demo is offline-ready** — database is cached in Supabase (accessible if internet works)
2. If no internet:
   - Results will be delayed (Supabase unavailable → live scrape)
   - Fallback suggestions still appear
   - Demo still works, just slower
3. **Backup plan:** Close browser, repeat demo on fresh search (warm up cache)

### "Projector/screen not working"
1. Tell audience: "Let me show you on my laptop screen instead"
2. Gather people around laptop (they can still see)
3. Proceed with demo

---

## Success Signals During Demo

✅ **Backend Terminal:** "Flask app running on http://localhost:8000" (no 401 errors)  
✅ **Frontend Terminal:** "Local: http://localhost:3000/" (no build errors)  
✅ **Browser:** Page loads; search box appears  
✅ **Search results:** 2+ resources appear within ~10 seconds with titles, links, licenses, scores  
✅ **Audience:** They can see how fast and relevant the search is  

---

## Post-Demo

- [ ] Thank audience and gather feedback
- [ ] Share URL (localhost:3000 or live Render URL if deployed)
- [ ] Offer to email faculty the system or slides
- [ ] Note any feature requests for post-event roadmap

---

## Presentation Essentials (Bring)

- [ ] Laptop + charger + power cable
- [ ] HDMI cable (for projector, if available)
- [ ] Phone (backup, or to show links work)
- [ ] Printed slides or use case (optional hand-out)
- [ ] Note card with 5-minute narrative (backup notes)

---

## Timing

| Task | Duration |
|------|----------|
| Setup (backend + frontend) | 3–5 min |
| Demo (live search) | 2–3 min |
| Narrative (5 phases + closing) | 3–5 min |
| Q&A | 5–10 min |
| **Total** | **13–23 min** (well within time limit) |

---

## Demo Courses (Go-To List If You Need Backup)

If ENGL 1101 has issues, try these in order:
1. ITEC 1001 — Tech/IT course; should return relevant results
2. ENGL 1102 — Similar to ENGL 1101; should work if 1101 doesn't
3. ITEC 2150 — Upper-level tech
4. ZZZZ 9999 — Show edge case handling (graceful no-results message)

---

## Real-Time Search Commands (If Needed)

If browser search is slow, you can demonstrate via curl in Terminal 3:

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"course_code":"ENGL 1101"}'

# Output: JSON with evaluated_resources array (can show in Terminal)
# Shows the backend is working even if UI is slow
```

---

## Final Confidence Check

Before starting demo, mentally verify:
- [ ] I've run this system 2+ times successfully in the past 24 hours
- [ ] I know what ENGL 1101 results should look like
- [ ] I can explain the 5-step architecture in 30 seconds
- [ ] I have backup courses ready if the first one stalls
- [ ] I'm comfortable answering "What would make this better?" (Phase 7 roadmap)

**You've got this.** The system works. The documentation is solid. The demo are clear. Go show everyone what you built.

---

**Status:** ✅ Ready for April 9  
**Last Checked:** April 7, 2026  
**Confidence Level:** 🟢 HIGH
