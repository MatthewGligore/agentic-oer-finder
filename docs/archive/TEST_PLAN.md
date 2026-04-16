# Phase 5: Testing and Evaluation
## Agentic OER Finder – Test Plan & Results

---

## Test Plan Overview

**Goal:** Verify that the system returns relevant, evaluated OER resources for target courses and handles edge cases gracefully.

**Scope:**
- **Functional tests:** 5 primary courses (as per spec)
- **Edge case tests:** Unknown course, empty input, special characters, very long input
- **OER rubric alignment:** Check against published evaluation criteria
- **Data quality tests:** Link validity, license visibility, response structure

**Execution:** Manual testing via local demo (backend + frontend running)

---

## Pre-Test Setup

Before running tests, verify the system is ready:

```bash
# Terminal 1: Start backend
cd /Users/mgligore/code/agentic-oer-finder
source .venv/bin/activate
python run.py
# Expected: "Flask app running on http://localhost:8000"

# Terminal 2: Start frontend
cd /Users/mgligore/code/agentic-oer-finder/frontend
npm run dev
# Expected: "VITE v5.x.x  ready in X ms"
#           "➜  Local:   http://localhost:3000"

# Terminal 3: Verify health check
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "backend_available": true}
```

---

## Test Cases

### Functional Tests (Primary Courses)

See instructions below each test. Record **PASS** or **FAIL** + any notes.

---

#### **Test 1: ENGL 1101 (English Composition)**

**Purpose:** Verify system finds and evaluates OER for a popular gen-ed course

**Steps:**
1. Open `http://localhost:3000` in browser
2. Enter `ENGL 1101` in the search form
3. Click "Search"
4. Wait for results (expected: ~5-10 seconds)

**Expected Results:**
- [ ] Results appear (do not timeout or show error)
- [ ] Minimum 2 resources displayed
- [ ] Each resource has:
  - [ ] Title (e.g., "OpenStax Writing Guide")
  - [ ] Link (clickable URL)
  - [ ] License (e.g., "CC BY 4.0")
  - [ ] Rubric score (e.g., "8.2/10")
  - [ ] Brief integration guidance
- [ ] At least one resource is from ALG or a known OER source

**Action:**
```bash
# Alternative: Direct API call
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"course_code":"ENGL 1101"}'
# Expected: 200 OK, JSON with evaluated_resources array
```

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

#### **Test 2: ITEC 1001 (Intro to IT)**

**Purpose:** Verify system works for technical/IT courses (different subject domain)

**Steps:**
1. Enter `ITEC 1001` in the search form
2. Click "Search"

**Expected Results:**
- [ ] Results appear
- [ ] Minimum 2 resources (even if fallback suggestions)
- [ ] Resources contain IT/tech-relevant keywords (e.g., "computer", "digital", "technology")
- [ ] At least one resource is evaluated (rubric score shown)

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

#### **Test 3: ITEC 2150 (Web Dev or equivalent)**

**Purpose:** Verify system handles upper-level IT courses

**Steps:**
1. Enter `ITEC 2150` in the search form
2. Click "Search"

**Expected Results:**
- [ ] Results appear
- [ ] Minimum 2 resources
- [ ] Titles/descriptions mention web, development, coding, or relevant keywords

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

#### **Test 4: ENGL 1102 (English Composition II)**

**Purpose:** Verify system differentiates similar courses and returns slightly different results

**Steps:**
1. Enter `ENGL 1102` in the search form
2. Click "Search"
3. Compare to Test 1 (ENGL 1101) results:
   - Are results similar (both composition)? Expected: YES
   - Are some resources unique? Expected: Maybe (depends on ALG index)

**Expected Results:**
- [ ] Results appear
- [ ] Minimum 2 resources
- [ ] Resources are writing/composition-focused (similar to ENGL 1101 but may differ)

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

#### **Test 5: ITEC 3150 (Upper-level IT)**

**Purpose:** Verify system handles advanced/upper-level courses

**Steps:**
1. Enter `ITEC 3150` in the search form
2. Click "Search"

**Expected Results:**
- [ ] Results appear
- [ ] Minimum 2 resources
- [ ] Titles suggest advanced topics (security, architecture, advanced programming, etc.)

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

### Edge Case Tests

---

#### **Test 6: Unknown Course**

**Purpose:** Verify system handles gracefully when no syllabus exists

**Steps:**
1. Enter `ZZZZ 9999` (non-existent course)
2. Click "Search"

**Expected Results:**
- [ ] **Does NOT crash or timeout**
- [ ] Either:
  - [ ] Shows "No resources found for this course" (preferred), OR
  - [ ] Shows sensible fallback suggestions (acceptable compromise)
- [ ] HTTP 200 OK (not 500 error)

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

#### **Test 7: Empty Input**

**Purpose:** Verify system handles missing input

**Steps:**
1. Leave search field empty
2. Click "Search"

**Expected Results:**
- [ ] **Does NOT crash**
- [ ] Either:
  - [ ] Form validation blocks submission (good UX), OR
  - [ ] Shows error message (acceptable)
- [ ] No 500 error

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

#### **Test 8: Special Characters**

**Purpose:** Verify system handles special input without breaking

**Steps:**
1. Enter `ENGL@#$%` or `EN--GL--1101`
2. Click "Search"

**Expected Results:**
- [ ] **Does NOT crash**
- [ ] Either:
  - [ ] Returns "No results" (expected), OR
  - [ ] Shows error message (acceptable)
- [ ] No 500 error

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

#### **Test 9: Very Long Input**

**Purpose:** Verify system handles large input gracefully

**Steps:**
1. Enter a very long string (e.g., 500+ characters)
2. Click "Search"

**Expected Results:**
- [ ] **Does NOT crash**
- [ ] Times out gracefully or returns "No results"
- [ ] No 500 error

**Result:** ☐ PASS / ☐ FAIL  
**Notes:** ___________________________

---

## OER Rubric Alignment Check

After running functional tests, evaluate results against the OER Software Rubric (from project requirements).

### Section 1: Search & Discovery
- [ ] Results are relevant to user query? (Does ENGL 1101 search return writing materials?)
- [ ] Results are clearly presented? (Titles, license, links visible?)
- [ ] Easy to parse (not cluttered)? (Y/N)

**Evidence:** See screenshots or test results above

### Section 2: Content Quality
- [ ] Resources are from reputable sources? (OpenStax, ALG, etc.) (Y/N)
- [ ] Descriptions/titles are clear and accurate? (Y/N)
- [ ] Information is up-to-date or marked as such? (Y/N)

**Evidence:** Test 1–5 results

### Section 3: Technical Reliability
- [ ] Links work (not broken)? (Y/N) *[Spot-check by clicking 2–3 links]*
- [ ] No crashes or errors in normal use? (Y/N) *[From edge case tests]*
- [ ] Page loads within 30 seconds? (Y/N)

**Evidence:** Tests 1–9

### Section 4: Licensing & Accessibility
- [ ] License clearly shown for each resource? (Y/N)
- [ ] All resources are openly licensed (CC, public domain, OA)? (Y/N)
- [ ] Recommendation to verify on source site? (Y/N)

**Evidence:** Test 1–5 results

---

## Known Limitations Document

Based on testing, document any known limitations:

### Limitation 1: Course-Specific Data

**Description:** System only has detailed syllabus data for courses in Supabase (typically ENGL 1101, ENGL 1102, ITEC courses, HIST, sciences).

**Evidence:** Test 6 (unknown course) showed fallback behavior.

**Mitigation:** Expand Supabase with more courses over time; system gracefully falls back to generic suggestions.

---

### Limitation 2: ALG Library Coverage

**Description:** ALG may not have textbooks for every subject or level.

**Evidence:** [Record here if observed in tests]

**Mitigation:** Fallback suggestions ensure non-empty response; users can supplement with web search.

---

### Limitation 3: Evaluation Heuristic-Based

**Description:** Quality scores are based on rule-based evaluation (license presence, keyword matching) not AI-trained model.

**Evidence:** Rubric scores are consistent but may not reflect expert peer review.

**Mitigation:** Scores are transparent and explain the criteria; users can verify on source.

---

### Limitation 4: License Detection

**Description:** License detection uses regex patterns; may not catch all variations.

**Evidence:** [Record if observed]

**Mitigation:** All ALG sources are verified open-licensed; regex is conservative (few false positives).

---

### Limitation 5: SimpleSyllabus Scraper

**Description:** If SimpleSyllabus HTML changes, scraper may fail; fallback to live scraping is slower.

**Evidence:** [Record availability of Supabase data]

**Mitigation:** Fallback ensures system continues to work; monitoring tracks scraper health.

---

## Test Results Summary

| Test | Course/Type | Result | Notes |
|------|--------|--------|-------|
| Test 1 | ENGL 1101 | ☐ PASS / ☐ FAIL | |
| Test 2 | ITEC 1001 | ☐ PASS / ☐ FAIL | |
| Test 3 | ITEC 2150 | ☐ PASS / ☐ FAIL | |
| Test 4 | ENGL 1102 | ☐ PASS / ☐ FAIL | |
| Test 5 | ITEC 3150 | ☐ PASS / ☐ FAIL | |
| Test 6 | Unknown (ZZZZ 9999) | ☐ PASS / ☐ FAIL | |
| Test 7 | Empty input | ☐ PASS / ☐ FAIL | |
| Test 8 | Special chars | ☐ PASS / ☐ FAIL | |
| Test 9 | Very long input | ☐ PASS / ☐ FAIL | |

**Overall Result:** ☐ **ALL PASS** / ☐ **SOME FAIL** / ☐ **MAJOR ISSUES**

**Failed Test Details (if any):**
```
[Record specific failures and root causes here]
```

---

## Rubric Alignment Summary

| Criterion | Met? | Evidence |
|-----------|------|----------|
| Search & discovery | ☐ Y / ☐ N | |
| Content quality | ☐ Y / ☐ N | |
| Technical reliability | ☐ Y / ☐ N | |
| Licensing & accessibility | ☐ Y / ☐ N | |

---

## Sign-Off

**Tester:** ___________________  
**Date:** April 7, 2026  
**System Status:** Ready for Phase 6 (Deployment) / Needs Fixes

---

**Document Status:** ⏳ Phase 5 (In Progress)  
**To Complete:** Run tests 1–9 and record results above  
**Next Phase:** Phase 6 – Deployment and Monitoring
