# Recognition Event Narrative
## Agentic OER Finder – May 5, 2026 Presentation

---

## 2-Minute Demo Script

**[Open browser, go to `http://localhost:3000`]**

**"Hi, I built an AI agent that helps GGC faculty find free textbooks and open educational resources in seconds.**

**Here's the problem: A faculty member wants to teach ENGL 1101 but doesn't want to burden students with a $200 textbook. They have to manually search multiple websites—OER Commons, ALG, LibreTexts—and spend 30+ minutes vetting materials and checking licenses.

**Our agent solves this with four steps:**

1. **[Type "ENGL 1101" and click Search]** *Faculty enters their course code*

2. **[Wait 5–10 seconds for results]** *System automatically:*
   - Queries GGC's syllabus database (Supabase) to understand what students need
   - Searches the Affordable Learning Georgia library for open textbooks
   - Falls back to smart suggestions if no exact matches
   
3. **[Results appear]** *Each resource shows:*
   - Title and link (clickable)
   - License (e.g., "CC BY 4.0"—fully open)
   - Quality score (based on openness, relevance, accessibility)
   - How to integrate it (e.g., 'Use as primary textbook or supplementary reading')

4. **[Click a resource link]** *Faculty jumps to ALG or the actual OER and can preview before deciding to adopt*

**[Scroll through results]** The system found 2+ relevant resources in 7 seconds. Each has a 7–10 score, open licenses, and actionable guidance.

**Let me try another course: [Type "ITEC 1001" and search]** Same fast process, different subject area.

**This system cuts faculty research time from 30 minutes to under 2 minutes—and it's built on free tools: open-source scrapers, a Supabase database, and a React frontend.**

---

## 5-Minute Extended Narrative (Per Phase)

### Phase 1: Ideation (Problem & User)

**"Faculty at GGC want to offer free or low-cost materials, but finding quality OER is a chore. Our user is a busy instructor who needs fast, relevant resources. Success means: course code in → relevant OER out in under 30 seconds."**

### Phase 2: Data Strategy (Where the Data Comes From)

**"We use three data sources: GGC's SimpleSyllabus library (what courses need), the Affordable Learning Georgia repository (open textbooks), and web-based OER as fallback. All sources are free and openly licensed—no student data involved, only institutional course info and published OER."**

### Phase 3: Architecture (How It Works)

**"High-level: User → React form → Flask backend orchestrator → database + ALG scraper + evaluators → scored results. If the database is unavailable, we scrape live. If ALG has no results, we suggest defaults. Multiple fallbacks mean the system always returns something useful."**

### Phase 4: Development (What We Built)

**"We built a Flask API with an 'OER Agent' that orchestrates the pipeline: fetch syllabus, extract keywords, search ALG, evaluate quality, and rank by relevance. Each resource gets scored on 7 dimensions: open license, content quality, accessibility, relevance, currency, pedagogy, and technical quality. All code is documented and handles edge cases gracefully."**

### Phase 5: Testing (Does It Work?)

**"We tested on five GGC courses: ENGL 1101, ITEC 1001, ITEC 2150, ENGL 1102, ITEC 3150. All returned relevant results. We also tested edge cases—unknown courses, empty input, special characters—and the system failed gracefully each time. No crashes, all errors handled."**

### Phase 6: Deployment (Where to Access)

**"For this project, we demo locally on my laptop [gesture to screen]. The system is also ready to deploy to Render (free cloud) for live use. Future deployment will include simple monitoring to ensure links stay active and the system keeps running."**

### Phase 7: Scaling (What's Next)

**"Post-April 9, we can expand to all 300+ GGC courses, integrate more OER sources (OpenStax, MERLOT, LibreTexts), add Canvas LMS integration so faculty see 'Insert OER' inside their course editor, and gather faculty feedback to improve ranking and search."**

---

## Key Takeaway (Closing)

**"This project shows that you can build a real, useful AI system without expensive APIs or complex models. By combining web scraping, a smart database, and thoughtful UX, we've created a tool that saves faculty time and helps students access better, cheaper course materials. The hardest part wasn't the technology—it was understanding what faculty actually need."**

---

## Answers to Likely Questions

**Q: "Does this require an API key or cost anything?"**  
A: No API keys needed for the core system. We use Supabase (free tier), scrapers (free), and no LLM APIs. Cost is $0 to run.

**Q: "What happens if the websites change or go down?"**  
A: Good question. We have fallback suggestions hardcoded so searches never return empty. If SimpleSyllabus changes, the scraper logs the error, and we fall back to live scraping (slow but functional). System gracefully degrades.

**Q: "How do you know the OER are actually good?"**  
A: We score them on an evidence-based rubric (open license, content quality, accessibility, etc.). All ALG resources are curated and peer-reviewed already. Faculty can click the link and preview before adopting. We're not replacing faculty judgment—we're reducing the time to find candidates.

**Q: "Can this be used at other schools (not just GGC)?"**  
A: Absolutely. The architecture is generic. Any school can:  
1. Swap SimpleSyllabus for their own course database or registrar API
2. Plug in their preferred OER repositories (ALG is USG-wide)
3. Deploy the same code

We designed it to be modular.

**Q: "What was the hardest part?"**  
A: Three things:
1. **SimpleSyllabus scraping** – The site uses JavaScript rendering, so we added Selenium as a fallback
2. **Handling when ALG has 0 results** – We solved this with smart default suggestions
3. **Configuration management** – We had placeholder API keys causing 401 errors; we fixed it by auto-detecting placeholders and forcing no-API mode

**Q: "How long did this take?"**  
A: ~40–50 hours of development, testing, and documentation (roughly 2 weeks part-time).

---

## Slides (Optional Visual Aids for Presentation)

**Slide 1: Problem**
```
Problem: Faculty spend 30+ min finding relevant OER
User: GGC faculty, course coordinators
Solution: AI agent to find + evaluate OER in <2 minutes
```

**Slide 2: Architecture**
```
[Simple diagram]
User → Search Form → Flask API → Supabase / ALG → Evaluator → Results
```

**Slide 3: Tech Stack**
```
Frontend: React + Vite
Backend: Flask + Python
Database: Supabase (PostgreSQL)
Tools: BeautifulSoup4 (scraping), regex (license detection)
```

**Slide 4: Demo Results**
```
Course: ENGL 1101
Time: 7 seconds
Resources: 2–5 (with rubric scores)
Licenses: 100% open (CC BY, public domain)
Example: "Writing Guide with Handbook - OpenStax (CC BY 4.0, Score: 8.2/10)"
```

**Slide 5: Key Metrics**
```
✓ Sub-30-second search
✓ 3+ resources per course
✓ 100% open licenses
✓ 7-criterion rubric evaluation
✓ Zero cost to operate
✓ Graceful error handling
```

**Slide 6: What's Next**
```
Tier 1 (1 month):
  - Expand to all 300 GGC courses
  - Add OpenStax, MERLOT sources
  - Improve ALG search recall

Tier 2 (2–3 months):
  - Canvas LMS integration
  - Institutional dashboard
  - Faculty reviews & ratings
```

---

## Delivery Notes

**Timing:**
- **Demo:** 2–3 minutes (show live search, explain workflow)
- **Full narrative:** 5 minutes (one sentence per phase)
- **Q&A:** 5–10 minutes (be ready for edge case questions)

**Setup (15 min before event):**
- Have backend running: `python run.py` (Terminal 1)
- Have frontend running: `npm run dev` (Terminal 2)
- Open browser to `http://localhost:3000`
- Refresh to confirm it loads
- Have 3–4 test courses ready (ENGL 1101, ITEC 1001, ENGL 1102, ITEC 3150)

**Backup Plan (if internet/laptop fails):**
- Print slides or bring backup laptop
- Have pre-recorded 2-min video demo (optional)
- Can still explain architecture and results verbally

**What to Bring:**
- Laptop + power adapter + HDMI cable (for projector)
- Phone as backup (to show links work)
- Printed use-case doc + data inventory (hand out as extras)

---

## Post-Event Follow-Up

**After May 5:**
1. Send live URL (if deployed) to faculty mailing list
2. Collect feedback via simple form (Google Form)
3. Document what worked and what didn't
4. Plan Tier 1 roadmap based on feedback
5. Celebrate the achievement! 🎉

---

**Presentation Status:** ✅ Ready for May 5, 2026  
**Last Updated:** April 7, 2026
