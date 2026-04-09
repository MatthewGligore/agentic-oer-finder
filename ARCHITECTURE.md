# Phase 3: Architecture and Framework Selection
## Agentic OER Finder – System Design

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ USER / GGC FACULTY                                              │
│ "Find OER for ENGL 1101" (via React web form)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATION LAYER (Flask + OER Agent)                         │
│ • Parse user request (course code)                              │
│ • Select and sequentially call tools                            │
│ • Evaluate and rank results                                     │
│ • Prepare JSON response                                         │
└────────────────┬──────────────────────────┬──────────────────────┘
                 │                          │
      ┌──────────▼──────────┐    ┌─────────▼──────────┐
      │ TOOL 1: DATABASE    │    │ TOOL 2: SCRAPER    │
      │ (Supabase)          │    │ (ALG + Web)        │
      │ • Query course code │    │ • Search by keyword│
      │ • Extract syllabus  │    │ • Identify matching│
      │ • Get objectives    │    │ • Extract metadata │
      └──────────┬──────────┘    └─────────┬──────────┘
                 │                          │
      ┌──────────▼──────────┐    ┌─────────▼──────────┐
      │ TOOL 3: EVALUATOR   │    │ TOOL 4: FALLBACK   │
      │ • Rubric scoring    │    │ • Default sugg.    │
      │ • License detection │    │ • Web search       │
      │ • Quality metrics   │    │ • LLM enhance      │
      └──────────┬──────────┘    └─────────┬──────────┘
                 │                          │
                 └──────────────┬───────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE TO USER                                                │
│ • 3-5 resources with links, licenses, and integration guidance  │
│ • JSON from Flask API, rendered by React frontend              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Decisions

### User & Interface
- **User:** GGC faculty (primary), course coordinators
- **Interface:** React + Vite web form (local development mode or hosted URL)
- **Input:** Single text field (course code, e.g., "ENGL 1101")
- **Output:** List of resources with scores, links, and integration tips

### Orchestration Layer
- **Framework:** Flask (Python) + custom OER Agent class
- **Approach:** Synchronous pipeline (no need for async at this scale)
- **LLM integration:** Optional; defaults to no-API mode (heuristic-based)
  - If LLM available → enhance ranking and evaluation summaries
  - If not available → use rule-based evaluation (license regex, keyword matching)
- **Error handling:** Multi-level fallback
  - Level 1: Query Supabase for syllabus
  - Level 2: If Supabase unavailable, scrape SimpleSyllabus live
  - Level 3: If search returns 0 results, provide default suggestions for course
  - Level 4: Log errors but never return empty response

### Tools

| Tool | Purpose | Implementation | Cost |
|------|---------|-----------------|------|
| **Supabase** | Course syllabuses + sections | PostgreSQL database (hosted) | Free tier sufficient |
| **ALG Scraper** | Open textbooks and materials | BeautifulSoup4 web scraper | No cost (public site) |
| **SimpleSyllabus Scraper** | GGC course metadata | Selenium + requests fallback | No cost (GGC public) |
| **Rubric Evaluator** | Quality scoring on 7 dimensions | Python rule-based engine | No cost (local) |
| **License Checker** | Detect CC, GPL, public domain, open access | Regex pattern matching | No cost (local) |
| **LLM Client** (optional) | Enhance evaluation summaries | OpenAI/Anthropic API (optional) or local to Ollama | Free fallback mode |

### Data Flow (5 Steps)

**Step 1: Parse Input**
```
User submits: "ENGL 1101"
System normalizes to course code: "ENGL 1101"
```

**Step 2: Fetch Course Context**
```
Supabase query: SELECT * FROM syllabuses WHERE course_code='ENGL 1101'
Result: Course title, objectives, topics, required materials
Fallback: If unavailable, live-scrape SimpleSyllabus and cache result
```

**Step 3: Extract Keywords**
```
From course objectives/topics, identify key terms:
  ENGL 1101 → ["composition", "writing", "essay", "grammar", "rhetoric"]
Pass keywords to search tools
```

**Step 4: Search & Identify OER**
```
ALG Scraper: Search ALG with "composition writing essay" → Get matching resources
Fallback: If ALG returns few results, suggest default OER for ENGL 1101
Result: List of 5-15 candidate resources with metadata
```

**Step 5: Evaluate & Rank**
```
For each resource, calculate:
  - Rubric score (1-10): open license, content quality, accessibility, relevance, etc.
  - Relevance explanation: How does it match the course?
  - Integration guidance: How can faculty use it?
Rank by relevance + quality score
Return top 3-5 resources in JSON response
```

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend** | Python 3.10+ | Mature scraping libraries, easy data handling |
| **API Framework** | Flask | Lightweight, straightforward routing |
| **Database** | Supabase (PostgreSQL) | Free tier, managed, Postgres SQL support |
| **Frontend** | React + Vite | Fast dev server, modern UX, easy deployment |
| **Scraping** | BeautifulSoup4, Selenium | Handles both static and JS-rendered HTML |
| **LLM** | OpenAI/Anthropic (optional) | Can use local Ollama or no-API mode |
| **Deployment** | Render (or local) | Free tier, supports Node + Python |

---

## Known Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Supabase unavailable** | Can't query syllabuses → slow fallback to live scraping | Fallback scraper implemented; graceful degradation |
| **ALG search returns 0 results** | User sees empty/generic results | Default course-specific suggestions hardcoded; ensures non-empty response |
| **SimpleSyllabus site structure changes** | Scraper breaks; new setup required | Fallback to keyword-based search; monitor scraper logs |
| **Invalid LLM API key** | 401 errors in logs; confusion | Default to no-API mode; automatic fallback; no blockage |
| **High search volume** | Slow response time | Supabase caching; ALG search is fast; evaluation is local (no bottleneck) |
| **Licensing misdetection** | Wrong license shown to user | Regex patterns tested; recommendation to verify on ALG; noted in output |

---

## Framework & Library Choices

- **Backend:** Flask (not FastAPI) — synchronous suffices, easier for multi-tool orchestration
- **Database:** Supabase (not DynamoDB, MongoDB) — SQL is clearer for course queries, free tier exists
- **Frontend:** React (not Vue) — larger ecosystem, Vite bundler is fast
- **Scraping:** BeautifulSoup4 (not Playwright) — lower overhead for non-SPA sites; Selenium fallback for JS
- **LLM:** Pluggable architecture — can run OpenAI, Anthropic, local Ollama, or no-API mode

---

## Component Interaction Summary

**On User Request (e.g., "ENGL 1101"):**

1. React form → POST `/api/search` with `{"course_code": "ENGL 1101"}`
2. Flask receives request, creates OER Agent
3. OER Agent executes pipeline:
   - Query Supabase for ENGL 1101 syllabus
   - Extract keywords (composition, writing, etc.)
   - Search ALG for matching textbooks
   - Evaluate each resource (rubric + license)
   - Rank by relevance + quality
4. Return JSON: `{ evaluated_resources: [...], summary: "...", processing_time: "..." }`
5. React renders list of resources with links, scores, integration tips

**Fallback Behavior:**
- No Supabase → scrape SimpleSyllabus live (slower, but works)
- No ALG results → return hardcoded suggestions for that course
- No LLM available → use rule-based evaluation (still scores, no summary)

---

## Deployment Architecture

**Development Mode (April 9):**
- Backend: `python run.py` → Flask on `http://localhost:8000`
- Frontend: `npm run dev` → Vite on `http://localhost:3000`
- Database: Supabase (cloud) or local PostgreSQL
- Demo: Local browser access

**Production Mode (Future):**
- Backend: Render service (Python) or Cloud Run
- Frontend: Render service (Node.js) or Vercel
- Database: Supabase (cloud)
- Monitoring: Render logs + periodic health checks

---

## Success Criteria for Architecture

✅ **Single course code input** → **multiple evaluated OER** (no extra form fields needed)  
✅ **Sub-30-second response time** (goal; local SQLite would be faster but Supabase acceptable)  
✅ **Graceful degradation** (if any component fails, system still returns results via fallback)  
✅ **Clear license information** (all results include CC/open-license info)  
✅ **Actionable integration guidance** (faculty know how to use each resource)  

---

**Document Status:** ✅ Phase 3 Complete  
**Created:** April 7, 2026  
**Next Phase:** Phase 4 – Development and Integration (complete; moving to Phase 5 – Testing)
