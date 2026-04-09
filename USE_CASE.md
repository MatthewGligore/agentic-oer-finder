# Phase 1: Ideation and Use Case Definition
## Agentic OER Finder for GGC Faculty

---

## Problem Statement

**In one sentence:** Faculty at Georgia Gwinnett College (GGC) need a fast, accurate way to discover open educational resources (OER) that match their course content and learning objectives, without manually searching multiple repositories or spending budget on commercial textbooks.

---

## User Definition

**Primary User:** GGC Faculty  
- Instructors teaching gen-ed courses (English composition, history, sciences, information technology)
- Goal: Find and integrate low-cost or free materials to reduce student costs and improve course outcomes
- Constraints: Limited time during course planning; may not be familiar with OER repositories or licensing

**Secondary User:** Course coordinators and curriculum developers  
- Goal: Build or update course curricula using available OER
- Constraints: Need to vet materials quickly and ensure licensing compliance

---

## Success Criteria

A faculty member can:
1. **Search by course code** (e.g., "ENGL 1101")
2. **Receive relevant results** of 3+ open educational resources in **less than 30 seconds**
3. **See actionable information** for each resource:
   - Title and link to the resource
   - License type (e.g., Creative Commons, CC BY)
   - Brief description or relevance explanation
   - How to integrate into the course (assignments, assessments, etc.)

Success = Faculty can quickly evaluate and integrate OER without additional research.

---

## Scope

### In Scope
- **Gen-ed courses at GGC:** ENGL 1101/1102, ITEC 1001/2150/3150 (and similar introductory courses)
- **OER sources:** 
  - SimpleSyllabus library (GGC course syllabuses)
  - Affordable Learning Georgia (ALG) open textbooks and materials
  - Web-based OER repositories (secondary fallback)
- **Resource types:** Textbooks, reading materials, course modules, open educational websites
- **Evaluation:** Quality scoring using OER rubric (licensing, content quality, accessibility, relevance)
- **Output format:** Web-based search interface (locally runnable or hosted)

### Out of Scope
- **K-12 and pre-college materials** (focus on college-level courses only)
- **Paid or commercial textbooks** (OER only)
- **Proprietary or restricted-license materials**
- **Real-time, comprehensive marketplace** (not a commercial OER aggregator; this is a targeted agent for GGC courses)
- **Student tutorial or homework help** (focus on faculty resource discovery)
- **Integration into GGC LMS** (initially a standalone tool; LMS integration is future work)

---

## Scope Agreement

✅ **Confirmed with requirements:**
- User: GGC Faculty, focused on gen-ed courses
- Success: <30 second search, 3+ results with links and licenses
- In-scope: SimpleSyllabus, ALG, web-based OER
- Out-of-scope: Paid/K-12 materials, LMS integration

---

## Deliverable Summary

This use case document establishes:
- **What the problem is:** Faculty time and budget barriers to finding OER
- **Who it serves:** GGC faculty and curriculum developers
- **What success looks like:** Fast, relevant, actionable OER discovery
- **What's in/out:** Gen-ed courses, SimpleSyllabus + ALG primary sources, evaluation rubric, licensed OER only

This use case **drives all downstream phases** (data strategy, architecture, development, testing, deployment).

---

**Document Status:** ✅ Phase 1 Complete  
**Created:** April 7, 2026  
**Next Phase:** Phase 2 – Data Strategy and Training Preparation
