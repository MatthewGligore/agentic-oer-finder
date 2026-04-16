# Phase 7: Scaling and Optimization
## Agentic OER Finder – Future Roadmap

---

## Overview

Phase 7 is **optional** and focused on improvements post-April 9. It outlines potential enhancements to expand scope, improve performance, and increase adoption.

---

## Roadmap

### Tier 1: High-Impact Improvements (1–2 months post-April-9)

#### 1.1 Expand Course Coverage

**Current State:**
- ~100 GGC courses in Supabase (from SimpleSyllabus library)
- Limited to ENGL, ITEC, HIST, and sciences

**Improvement:**
- Scrape full SimpleSyllabus library for all 300+ GGC courses
- Add ALG-specific course mappings (ALG knows which OER fit which subjects)
- **Effort:** 4–6 hours (scraper already built; scale infrastructure)
- **Benefit:** Faculty can search any GGC course, not just popular ones

**Implementation:**
```bash
python backend/cli.py scrape-syllabuses --all
# Inserts all 300+ courses into Supabase; query time improves from 3-5s to <1s
```

#### 1.2 Improve ALG Search Quality

**Current State:**
- ALG scraper searches by course name + keywords
- Sometimes returns 0 results; system falls back to hardcoded suggestions

**Improvement:**
- Implement smarter keyword extraction (NLP-based or prompt-based)
- Cache ALG search results (reduce scraping; faster searches)
- Add ALG API integration (if available) instead of web scraping
- **Effort:** 6–8 hours
- **Benefit:** More consistent results; faster search time

**Implementation:**
```python
# Example: Use spaCy or NLTK to extract key terms
from spacy import load
nlp = load("en_core_web_sm")
doc = nlp("This course covers composition, writing, and critical thinking.")
keywords = [token.text for token in doc if token.pos_ in ['NOUN', 'ADJ']]
# Result: ['composition', 'writing', 'critical', 'thinking']
```

#### 1.3 Add More OER Sources

**Current State:**
- SimpleSyllabus (GGC syllabuses)
- ALG (open textbooks)
- Generic fallback suggestions

**Improvement:**
- Integrate OpenStax (popular free textbooks)
- Integrate MERLOT (peer-reviewed OER)
- Integrate LibreTexts (open resource library)
- Integrate OER Commons (search + discovery)
- **Effort:** 8–12 hours (one scraper per source)
- **Benefit:** More diverse and abundant OER options for users

**Implementation:**
```python
# New scrapers in backend/scrapers/
openstax_scraper.py      # Search OpenStax by subject
merlot_scraper.py        # Query MERLOT API
libretexts_scraper.py    # Browse LibreTexts bookshelves
oer_commons_scraper.py   # Search OER Commons hub
```

---

### Tier 2: User Experience Improvements (2–4 weeks post-April-9)

#### 2.1 Advanced Search & Filtering

**Current State:**
- Simple text input (course code only)

**Improvement:**
- **Filter by:** License type, resource type (textbook, video, interactive), educational level
- **Sort by:** Relevance, quality score, license openness, date added
- **Faceted search:** Show available filters before search
- **Saved searches:** Let faculty bookmark favorite resources
- **Effort:** 6–8 hours (frontend + backend API changes)
- **Benefit:** Faculty get exactly what they need faster

**Mockup:**
```
Search: [ENGL 1101] [Search]

Filters (Left Panel):
  ☑ Open License
    ☐ CC BY (CC0, CC BY-SA, etc.)
  ☑ Resource Type
    ☑ Textbook
    ☐ Video
    ☐ Interactive
  ☑ Educational Level
    ☑ Undergraduate
    ☐ Graduate
  ☑ Rating
    ☑ 7+ out of 10

Results: 12 resources matching filters
```

#### 2.2 Resource Detail Pages

**Current State:**
- List of resources with basic info

**Improvement:**
- Detailed page per resource:
  - Full description and table of contents (if available)
  - User reviews and ratings
  - Integration examples (how other courses use it)
  - Download/export syllabus with resource integrated
- **Effort:** 8–10 hours
- **Benefit:** Faculty can make faster adoption decisions

#### 2.3 Comparison Tool

**Current State:**
- View one resource at a time

**Improvement:**
- Compare 2–3 resources side-by-side (rubric scores, license, features, cost)
- "Replace my current textbook" workflow
- **Effort:** 4–6 hours
- **Benefit:** Easy decision-making for switching from commercial to OER

---

### Tier 3: Institutional Integration (1–3 months post-April-9)

#### 3.1 LMS Integration (Canvas)

**Current State:**
- Standalone web app

**Improvement:**
- Canvas plugin / LTI integration
- "Insert OER" button inside Canvas course editor
- Direct linking from syllabus to OER resources within LMS
- **Effort:** 12–16 hours (LMS API setup, authentication)
- **Benefit:** Faculty workflow integration; higher adoption

#### 3.2 GGC Registrar Integration

**Current State:**
- Manual course code entry

**Improvement:**
- Auto-pull list of courses faculty teaches (from registrar)
- Pre-populate search with faculty's actual course roster
- Bulk OER search (search for all courses taught in semester)
- **Effort:** 8–12 hours (registrar API, auth)
- **Benefit:** Faster, personalized discovery

#### 3.3 Institutional Dashboard

**Current State:**
- Individual faculty use

**Improvement:**
- Admin dashboard showing:
  - Most-searched courses
  - Popular OER across institution
  - Faculty adoption stats
  - Cost savings from OER adoption
- **Effort:** 10–12 hours
- **Benefit:** Institutional visibility; budget justification for OER initiatives

---

### Tier 4: Data & Quality (Ongoing)

#### 4.1 Community Contributions

**Current State:**
- Curated by development team only

**Improvement:**
- Allow faculty to:
  - Add OER resources they've found
  - Rate and review resources
  - Share integration tips and syllabi
- Peer-review process for new contributions
- **Effort:** 12–16 hours (UGC platform, moderation workflow)
- **Benefit:** Crowdsourced data; community engagement

#### 4.2 AI-Enhanced Evaluation

**Current State:**
- Rule-based rubric scoring (heuristic)

**Improvement:**
- Fine-tune LLM (GPT, Claude, or local model) on OER quality rubric
- Replace regex license detection with more robust NLP
- Better relevance ranking (training on course syllabuses + OER matches)
- **Effort:** 20–30 hours (data labeling, model training)
- **Benefit:** More accurate quality scores; better relevance ranking

#### 4.3 Real-Time Data Updates

**Current State:**
- Syllabuses refreshed per semester; ALG cached intermittently

**Improvement:**
- Auto-scrape SimpleSyllabus weekly
- Set up scheduled ALG search updates (daily)
- Track resource URL health (check for broken links)
- Automated alerts if links break
- **Effort:** 6–8 hours (Render cron jobs or AWS Lambda)
- **Benefit:** Freshness; reliability

---

## Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| **Expand course coverage** | High | Medium | **1** |
| **Improve ALG search** | High | Medium | **1** |
| **Add more OER sources** | High | High | **2** |
| **Advanced search/filtering** | High | Medium | **2** |
| **Resource detail pages** | Medium | Medium | **3** |
| **LMS integration** | High | High | **3** |
| **Institutional dashboard** | Medium | High | **4** |
| **Community contributions** | Medium | High | **4** |
| **AI-enhanced evaluation** | High | High | **4** |
| **Real-time data updates** | Medium | Medium | **5** |
| **Comparison tool** | Medium | Low | **5** |
| **Registrar integration** | Medium | High | **4** |

---

## Implementation Roadmap (Timeline)

```
April 9 (Launch) ────────────────────────────────────────────────────

April–May (Tier 1):
  Week 1: Add more OER sources (OpenStax, MERLOT)
  Week 2–3: Improve ALG search + expand course coverage
  Week 4: Real-time data update pipeline

May–June (Tier 2):
  Week 1–2: Advanced search & filtering UI
  Week 3–4: Resource detail pages

June–July (Tier 3):
  Week 1–2: Canvas LMS integration (pilot)
  Week 3–4: Institutional dashboard

July–August (Tier 4):
  Week 1–2: AI-enhanced evaluation (fine-tuning)
  Week 3–4: Community contributions (beta)

Fall 2026+: Ongoing improvements based on usage data
```

---

## Estimated Effort & Cost

| Phase | Effort (Hours) | Cost (If Outsourced) | Timeline |
|-------|----------------|----------------------|----------|
| **Tier 1 (High-impact)** | 18–26 | $2,000–$3,500 (2–3 devs × 1 week) | 1 month |
| **Tier 2 (UX)** | 18–24 | $2,500–$3,500 (2 devs × 1 week) | 2–4 weeks |
| **Tier 3 (Integration)** | 28–40 | $4,000–$6,000 (2–3 devs × 2 weeks) | 2–3 months |
| **Tier 4 (Data/AI)** | 38–60 | $5,500–$9,000 (2–3 devs × 2–3 weeks) | 2–3 months |
| **Total** | **102–150 hours** | **$14,000–$21,500** | **4–6 months** |

---

## Success Metrics (Post-April-9)

- **Adoption:** X faculty using system by June 30
- **Search coverage:** 90%+ of GGC courses searchable
- **ALG match rate:** 80%+ of searches return ≥2 resources
- **Time saved:** Faculty spend <2 min to find applicable OER (vs. 30+ min manual search)
- **Cost saved:** Conservative estimate of $X per course in textbook costs avoided

---

## Known Constraints

1. **Budget:** Development is volunteer/academic; no budget for paid APIs (use free tiers only)
2. **Maintenance:** System requires ongoing monitoring and updates as sources change
3. **Scaling:** Supabase free tier may need upgrade if usage grows significantly (estimated: after ~1000 searches/day)
4. **Licensing:** Any new sources must be openly licensed or fair-use compliant

---

## Conclusion

Phase 7 roadmap provides a **clear path to scale** beyond the April 9 MVP. Tier 1 improvements (expand courses, add sources, improve search) are high-impact and achievable within 1 month. Institutional integration (Tier 3) will require stakeholder coordination but will drive faculty adoption.

The system is designed to be **modular and extensible**—adding new OER sources or search tools is straightforward. Each tier builds on the previous one without breaking changes.

---

**Document Status:** ✅ Phase 7 Complete  
**Created:** April 7, 2026  
**Target:** Post-April-9 Implementation
