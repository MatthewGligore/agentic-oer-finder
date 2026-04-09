# Phase 2: Data Strategy and Training Preparation
## Agentic OER Finder – Data Inventory

---

## Data Sources Summary

The system relies on three primary data sources to answer "What OER exists for this course?"

| Source | Type | Access | Format | Freshness | Privacy/License |
|--------|------|--------|--------|-----------|-----------------|
| **SimpleSyllabus Library (GGC)** | Syllabus repository | Web scrape + Supabase cache | HTML + JSON | Updated per semester | GGC public, no PII required |
| **Affordable Learning Georgia (ALG)** | OER textbooks & materials | Web scrape + search API | HTML + JSON | Updated continuously | Creative Commons licensed |
| **Web-based OER repos** | Fallback sources | Search/web scrape | HTML | Varies | CC/public domain/open access |

---

## 1. SimpleSyllabus Library (Primary)

**Purpose:** Extract course metadata and required materials to understand what students need.

**Location:** `https://ggc.simplesyllabus.com/en-US/syllabus-library`

**Data Extracted:**
- Course code (e.g., "ENGL 1101")
- Course title
- Term and semester
- Instructor name
- Course objectives and topics
- Grading and assessment methods
- Required and supplementary materials

**Access Method:**
- Selenium-based scraper (`backend/scrapers/library_index_scraper.py`) discovers all syllabuses
- Content scraper (`backend/scrapers/syllabus_content_scraper.py`) parses each syllabus into 8 structured sections (objectives, topics, grading, resources, etc.)
- Bulk scraper orchestrates discovery → parsing → database insertion

**Storage:** Supabase PostgreSQL database
- Table: `syllabuses` (course code, term, URL, metadata)
- Table: `syllabus_sections` (parsed content by section type)

**Quality & Currency:**
- Syllabuses updated by instructors each semester
- Scraper verifies links are valid before insertion
- Cache in Supabase allows fast queries without live scraping on every search

**Privacy & Licensing:**
- No student PII collected (syllabuses are public institutional documents)
- Using institutional data with GGC permission
- Metadata is factual course information; no proprietary content replicated verbatim

---

## 2. Affordable Learning Georgia (ALG)

**Purpose:** Find open textbooks and curated OER materials that match course topics.

**Location:** `https://alg.manifoldapp.org`

**Data Available:**
- Open textbook titles
- Author and publication info
- License information (CC BY, CC BY-SA, public domain, etc.)
- Direct links to resources
- Brief descriptions of content

**Access Method:**
- Web scraper (`backend/scrapers/alg_scraper.py`) searches ALG by course name or keyword
- Query template: "ENGL 1101" + "composition" → returns textbook results
- Alternative: Direct URL search on ALG site

**Quality & Currency:**
- ALG is a USG (University System of Georgia) initiative
- Resources are vetted and curated
- Licenses are explicitly stated (primary value over commercial sources)
- Content is relatively static (updated when new OER is published)

**Privacy & Licensing:**
- All ALG resources are open licensed (CC, public domain, or OA)
- Using ALG's public search API (no authentication required)
- Resources are designed for reuse and remixing

---

## 3. Fallback/Supplementary Sources

**Purpose:** When SimpleSyllabus or ALG doesn't provide sufficient results, use web search or built-in suggestions.

**Data Sources:**
- Course-specific default suggestions (hardcoded for popular gen-ed courses)
- Web search for "open textbooks [course name]"
- LibreTexts, MERLOT, OER Commons (if integrated in future)

**Access Method:**
- Heuristic keyword matching + optional web scraper fallback
- No external API required (local, cost-free)

**Quality & Currency:**
- Suggestions are manually curated for popular courses (ENGL 1101, ITEC, HIST, sciences)
- Web search may include non-OER results; filtered by license detection
- No guarantee of freshness; relies on community maintenance

**Privacy & Licensing:**
- Following links requires users to verify licenses on target sites
- No PII involved

---

## Data Flow

**User Input:**
```
"ENGL 1101"  →  Course code (required)
```

**Data Processing:**
1. **Syllabus Query:** Look up ENGL 1101 in Supabase → fetch course objectives, topics, materials
2. **Keyword Extraction:** From course objectives, extract key topics (e.g., "composition," "writing," "essay")
3. **ALG Search:** Query ALG with extracted keywords → retrieve matching textbooks and materials
4. **Evaluation:** Score each resource using:
   - Rubric criteria (7 dimensions: open license, content quality, accessibility, relevance, currency, pedagogy, technical quality)
   - License detection (automatic identification of CC, GPL, etc.)
5. **Ranking:** Sort by relevance + quality score + license clarity
6. **Response:** Return top 3–5 resources with links, licenses, and how to integrate

**Output:**
```json
{
  "course_code": "ENGL 1101",
  "resources_found": 5,
  "evaluated_resources": [
    {
      "resource": {
        "title": "A Guide to Open Composition Resources",
        "url": "https://example.org/...",
        "license": "CC BY 4.0",
        "description": "Collection of openly licensed writing assignments and rubrics"
      },
      "rubric_evaluation": {
        "overall_score": 8.2,
        "open_license": 10,
        "content_quality": 8,
        "accessibility": 7,
        "relevance": 9,
        "currency": 8,
        "pedagogy": 8,
        "technical_quality": 7
      },
      "integration_guidance": "Use for in-class exercises, peer review assignments, or as supplementary reading..."
    }
  ]
}
```

---

## Data Quality & Validation

**Measures:**
1. **License verification:** Regex and metadata parsing confirm open licenses
2. **Link validation:** Periodic checks ensure URLs remain active
3. **Relevance scoring:** Course keywords matched against resource titles and descriptions
4. **Rubric evaluation:** Automatic scoring on 7 OER quality dimensions (see USE_CASE.md)
5. **Fallback detection:** When ALG/web search returns 0 results, system generates sensible default suggestions instead of empty response

**Known Limitations:**
- SimpleSyllabus data is GGC-specific; no other institutions' syllabuses available
- ALG search may not perfectly match niche courses
- Web scraping may miss resources behind authentication
- License detection uses pattern matching (not 100% foolproof)

---

## Privacy & Compliance

✅ **No student PII:** Syllabuses are public institutional documents; no enrolled student data used  
✅ **Licensed data only:** All external OER sources are CC, public domain, or open-access licensed  
✅ **Institutional use:** SimpleSyllabus access approved for GGC institutional analysis  
✅ **Attribution:** All returned resources include original author/license information  

---

## Summary

| Dimension | Value |
|-----------|-------|
| **Primary data sources** | SimpleSyllabus, ALG, web-based OER |
| **Data types** | Course metadata, syllabus content, OER metadata |
| **Storage** | Supabase PostgreSQL + local fallback suggestions |
| **Freshness** | Syllabuses updated per semester; ALG continuously; fallbacks static |
| **Quality checks** | License verification, link validation, rubric scoring |
| **Privacy risk** | Low (no student PII; institutional + open-licensed data only) |
| **Integration complexity** | Moderate (requires scraping + Supabase, but no API keys needed) |

---

**Document Status:** ✅ Phase 2 Complete  
**Created:** April 7, 2026  
**Next Phase:** Phase 3 – Architecture and Framework Selection
