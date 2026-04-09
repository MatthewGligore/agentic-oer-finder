# AGENTIC OER FINDER: DATA STRATEGY & TRAINING PREPARATION

## PART 1: DATA STRATEGY

### 1.1 Data Source

Your system uses **three primary data sources**:

1. **SimpleSyllabus Library** (Primary Source)
   - URL: `https://ggc.simplesyllabus.com/en-US/syllabus-library`
   - Contains ~100+ syllabuses for various courses
   - Includes semester information, instructor names, course codes
   
2. **ALG (Accessing the Classics)**
   - URL: `https://alg.manifoldapp.org`
   - Free cultural heritage texts for humanities courses
   - Provides curated open textbooks and resources

3. **Web Scraping**
   - Live scraping of course syllabuses for metadata extraction
   - Selenium-based JavaScript rendering for dynamic content
   - Fallback to requests library for static content

### 1.2 Data Type

Your system processes **multiple data types**:

| Data Type | Source | Example |
|-----------|--------|---------|
| **Metadata** | Syllabus URLs | Course code, term, section number, instructor |
| **Text Content** | Syllabus pages | Course objectives, topics, grading criteria, resources |
| **Structured Sections** | Parsed syllabuses | 8 section types: objectives, topics, grading, prerequisites, resources, assessment, policies, other |
| **Resource Links** | ALG + Web scraping | URLs to OER materials with titles and descriptions |
| **Licensing Info** | Resource pages | Creative Commons, CC0, open access indicators |

### 1.3 Input and Output

**User Input:**
- Course Code (e.g., "ENGL 1101")
- Optional: Term (e.g., "2026-Fall")

**System Output:**

```json
{
  "course_code": "ENGL 1101",
  "syllabus_found": true,
  "evaluated_resources": [
    {
      "resource": {
        "title": "...",
        "url": "...",
        "description": "...",
        "license": "CC BY 4.0"
      },
      "rubric_evaluation": {
        "overall_score": "8.2/10",
        "criteria_evaluations": {}
      },
      "license_check": {
        "has_open_license": true,
        "license_type": "CC BY"
      },
      "integration_guidance": "..."
    }
  ]
}
```

### 1.4 Data Preparation

Your system implements a **3-stage pipeline**:

**Stage 1: Library Index Scraping** (`library_index_scraper.py`)
- Selenium-based scraping of SimpleSyllabus library
- Extracts syllabus URLs and metadata
- Parses course codes, terms, section numbers
- Uses CSS selectors and regex patterns for data extraction

**Stage 2: Syllabus Content Parsing** (`syllabus_content_scraper.py`)
- Fetches individual syllabus HTML
- Pattern-matching to identify section types
- Text normalization and cleaning
- Extracts 8 section types with automatic categorization

**Stage 3: Database Storage** (`bulk_scraper.py`)
- Validates and deduplicates records
- Batch inserts into Supabase (optimized for 100+ record inserts)
- Maintains course code + term indexes for fast queries

### 1.5 Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|-----------|
| **Dynamic Content** | SimpleSyllabus uses JavaScript rendering | Selenium fallback with headless Chrome |
| **Inconsistent Formats** | Syllabus structure varies by instructor | Pattern matching + rule-based categorization |
| **Missing Data** | Some syllabuses lack course codes | Fallback extraction from URL structure |
| **Rate Limiting** | Web scraping may be throttled | Pagination support with configurable delays |
| **License Ambiguity** | Unclear open license statements | Regex-based detection with high/medium/low confidence scores |
| **Data Quality** | Incomplete or corrupted sections | Validation before database insertion + logging |
| **Stale Data** | Course syllabuses change each term | `scraped_at` timestamp for cache invalidation |

---

## PART 2: TRAINING PLAN

### 2.1 Approach Selected: LLM-Based (Multi-Provider)

Your system uses **Large Language Models** as the primary intelligent component, with support for multiple providers:

- **Primary:** OpenAI GPT-4o
- **Alternative:** Anthropic Claude 3.5 Sonnet
- **Fallback:** Rule-based evaluation (works without API keys)

### 2.2 Model Function

The LLM performs **three key functions**:

1. **Course Context Analysis**
   - Analyzes syllabus content to understand learning objectives
   - Identifies key topics and required skills
   - Maps course requirements to OER resource types

2. **Resource Relevance Evaluation**
   - Scores OER resources for relevance to specific courses
   - Explains why a resource matches the course
   - Identifies gaps in resource coverage

3. **Recommendation Generation**
   - Generates integration guidance for educators
   - Suggests pedagogical approaches for using resources
   - Provides implementation tips

### 2.3 Training Method: Prompt Engineering

Your system uses **sophisticated prompt engineering** rather than fine-tuning:

```
System Prompt Template:
"You are an educational content specialist evaluating OER resources 
for college courses. Analyze the provided course syllabus and OER 
resource, then provide a detailed relevance score and integration guidance."

User Prompt:
"Course: {course_name}
Syllabus: {syllabus_content}
OER Resource: {resource_title}
Evaluate this resource's relevance..."
```

**Advantages:**
- No retraining required when courses change
- Works with multiple LLM providers
- Sustainable without API costs (optional fallback mode)
- Human-readable reasoning for educators

### 2.4 Key AI Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Temperature** | 0.7 | Balance between creative suggestions and consistency |
| **Max Tokens** | 2000 | Sufficient for detailed evaluations without excessive costs |
| **Model** | gpt-4o | Superior reasoning for educational context analysis |
| **System Role** | Educational Specialist | Frames LLM for domain-specific reasoning |

### 2.5 Hybrid Evaluation Strategy

Your system combines **three evaluation methods**:

1. **LLM-Based** (GPT-4o)
   - Assesses relevance to course learning objectives
   - Evaluates pedagogical appropriateness
   - Generates human-readable explanations

2. **Rule-Based** (Rubric Evaluator)
   - Applies 7 criteria: Open License, Content Quality, Accessibility, Relevance, Currency, Pedagogical Value, Technical Quality
   - Generates consistent scores (0-10 scale)
   - Works without API keys

3. **Pattern-Matching** (License Checker)
   - Detects 13+ open license patterns (CC BY, CC0, GPL, etc.)
   - Flags restrictive licenses
   - Confidence scoring (high/medium/low)

### 2.6 Evaluation Metrics

| Metric | Method | Target |
|--------|--------|--------|
| **Accuracy** | User feedback on resource relevance | >75% resources marked "useful" |
| **Speed** | API response time | <5 seconds per search |
| **Coverage** | Percent of courses with resources | >80% of required courses |
| **License Confidence** | Regex pattern matching | >90% accuracy on detected licenses |
| **User Satisfaction** | Educator surveys | >4/5 stars for integration guidance |

---

## PART 3: SYSTEM INTEGRATION

### 3.1 Data Flow

**User Request → Data Processing → AI Evaluation → Result Presentation**

1. **User Input** → Educator searches for course code (e.g., "ENGL 1101")
2. **API Request** → Flask endpoint receives search request
3. **Data Retrieval** → OER Agent attempts to fetch:
   - Syllabuses from Supabase (if available)
   - Fallback to live scraping
   - Parse 8 section types (objectives, topics, grading, etc.)
4. **LLM Analysis** → GPT-4o analyzes syllabus content
   - Extracts learning objectives
   - Identifies key topics and skills
5. **Resource Search** → Multi-source aggregation:
   - ALG (open textbooks)
   - Web search results
   - Predefined suggestions
6. **Evaluation** → Three-stage assessment:
   - LLM relevance scoring
   - Rubric-based quality evaluation (7 criteria)
   - License verification and confidence scoring
7. **Integration Guidance** → LLM generates pedagogical recommendations
8. **JSON Response** → Return structured data to frontend
9. **UI Rendering** → React displays results with interactive cards

### 3.2 Tool Use & External Data Sources

| Tool | Purpose | Technology |
|------|---------|-----------|
| **SimpleSyllabus Scraper** | Discover & fetch course syllabuses | Selenium + BeautifulSoup |
| **ALG Scraper** | Find open textbooks | Requests + BeautifulSoup |
| **Supabase ORM** | Persistent storage & fast queries | PostgreSQL + Supabase SDK |
| **LLM API** | Intelligent content analysis | OpenAI / Anthropic REST API |
| **License Checker** | Verify open licenses | Regex pattern matching |
| **Rubric Evaluator** | Quality scoring | Python rule engine |

### 3.3 Output Presentation

**For Educators (Frontend UI):**
- **Search Results Page:** Shows 5-10 top-rated OER resources with visual score cards
- **Resource Detail View:** Full resource information with:
  - Quality rubric breakdown (7 criteria with scores)
  - License verification status
  - LLM-generated integration tips
  - Direct links to resources
- **Saved Resources:** Educators can bookmark resources for later use

**For Developers (API Response):**

```json
{
  "course_code": "ENGL 1101",
  "resources_found": 12,
  "evaluated_resources": [
    {
      "resource": {
        "title": "...",
        "url": "...",
        "license": "CC BY 4.0",
        "source": "OER Commons"
      },
      "relevance_explanation": "...",
      "rubric_evaluation": {
        "overall_score": 8.2,
        "criteria_evaluations": {}
      },
      "license_check": {},
      "integration_guidance": "..."
    }
  ]
}
```

---

## IMPLEMENTATION TIMELINE

| Phase | Duration | Status |
|-------|----------|--------|
| **Phase 1: Data Infrastructure** | 2 weeks | ✅ Complete |
| **Phase 2: Scraping Pipeline** | 3 weeks | ✅ Complete |
| **Phase 3: LLM Integration** | 2 weeks | ✅ Complete |
| **Phase 4: Evaluation Engines** | 2 weeks | ✅ Complete |
| **Phase 5: Frontend Development** | 4 weeks | ✅ Complete |
| **Phase 6: Testing & Optimization** | 2 weeks | In Progress |

---

## SYSTEM ARCHITECTURE SUMMARY

The Agentic OER Finder follows a **layered architecture**:

### Frontend Layer (React + Vite)
- SearchForm component for user input
- ResultsPage displaying evaluated resources
- ResourceDetailPage with full rubric breakdown

### REST API Layer (Flask)
- `/api/search` - Main search endpoint
- `/api/stats` - Statistics and metrics
- `/api/scrape-syllabi` - Bulk scraping operations

### OER Agent Orchestration
- Coordinates all data sources and evaluation engines
- Implements fallback logic (Supabase → Live Scraping)
- Manages LLM interactions and caching

### Data Sources & Scrapers
- **Supabase PostgreSQL:** Stores syllabuses and parsed sections
- **SimpleSyllabus Scraper:** Discovers and fetches syllabuses
- **ALG Scraper:** Retrieves open textbooks
- **Live Web Scraping:** Fallback for real-time data

### Evaluation Engines
- **LLM Evaluator:** GPT-4o analyzes course context and resource relevance
- **Rubric Scorer:** 7-criteria quality rubric with 0-10 scoring
- **License Checker:** Pattern-based detection of 13+ open licenses

### Logging & Utilities
- Usage logger (CSV/JSON format) for analytics
- Configuration management via environment variables

---

## KEY DESIGN DECISIONS

1. **No API Key Required**: System works without LLM API keys using rule-based fallback
2. **Multi-Source Data**: Combines library index, live scraping, and cached data
3. **Hybrid Evaluation**: Combines LLM + rule-based approaches for robustness
4. **Modular Architecture**: Each component (scraper, evaluator, LLM) is independently testable
5. **Scalable Storage**: Supabase enables batch operations and full-text search
6. **Educator-Focused Output**: Results optimized for non-technical educators

---

## FUTURE ENHANCEMENTS

1. **Fine-tuning**: Train custom models on educator feedback
2. **Personalization**: Remember user preferences and past searches
3. **Community Ratings**: Aggregate educator feedback on resources
4. **Curriculum Mapping**: Support for multi-course curriculum design
5. **Export Functionality**: Generate syllabus integration documents
6. **Analytics Dashboard**: Metrics on resource popularity and effectiveness

---

End of Document
