import React from 'react'
import { useAppState } from '../context/AppState'

const CRITERIA_ORDER = [
  'Accessibility',
  'Content Quality',
  'Currency/Up-to-date',
  'Open License',
  'Pedagogical Value',
  'Relevance to Course',
  'Technical Quality',
]

const CRITERIA_ALIASES = {
  'Currency / Up to date': 'Currency/Up-to-date',
  'Accessability': 'Accessibility',
}

function getCriterionName(criterion) {
  return CRITERIA_ALIASES[criterion] || criterion
}

function getCriterionEval(criteria, criterion) {
  const key = getCriterionName(criterion)
  return criteria?.[key] || {}
}

function formatCriterionScore(criteria, name) {
  const score = Number(getCriterionEval(criteria, name)?.score)
  return Number.isFinite(score) ? `${score.toFixed(1)} / 5` : 'N/A'
}

function getCriterionLink(resource, criterion) {
  const key = getCriterionName(criterion)
  const mapped = resource?.criterionLinks?.[key]
  if (mapped) {
    return mapped
  }

  const evidence = getCriterionEval(resource?.criteria, criterion)?.evidence
  if (Array.isArray(evidence)) {
    const linked = evidence.find((item) => item?.url)
    if (linked?.url) {
      return linked.url
    }
  }

  return resource?.url || '#'
}

function HomePage() {
  const {
    analysisProgress,
    courseCode,
    error,
    isLoading,
    normalizedResources,
    results,
    searchResources,
    setCourseCode,
    setTerm,
    term,
  } = useAppState()

  const handleSubmit = async (event) => {
    event.preventDefault()
    await searchResources(courseCode, term)
  }

  const quickCourses = ['ENGL 1101', 'ITEC 1001', 'HIST 2111', 'BIOL 1101K']

  return (
    <main className="app-shell">
      <section className="simple-panel hero-panel home-hero">
        <div className="hero-grid">
          <div>
            <p className="kicker">Agentic OER Finder</p>
            <h1 className="hero-title">Find Better OER In Minutes, Not Days</h1>
            <p className="subtle-copy hero-copy">
              Search by course code, pull syllabus context from Supabase or live scrape when missing, then rank
              resources against a rubric with criterion-level evidence.
            </p>

            <div className="hero-chip-row">
              {quickCourses.map((code) => (
                <button key={code} type="button" className="chip-button" onClick={() => setCourseCode(code)}>
                  {code}
                </button>
              ))}
            </div>
          </div>

          <aside className="hero-status-card" aria-live="polite">
            <p className="status-kicker">Discovery Pipeline</p>
            <h3>{isLoading ? 'Analyzing resources...' : 'Ready to search'}</h3>
            <p>
              {isLoading
                ? 'Running syllabus checks, source discovery, and rubric scoring now.'
                : 'Enter any course code to start sourcing and ranking open resources.'}
            </p>
            <div className="analysis-meter" role="progressbar" aria-valuenow={analysisProgress} aria-valuemin={0} aria-valuemax={100}>
              <div className="analysis-meter-fill" style={{ width: `${analysisProgress}%` }} />
            </div>
            <p className="analysis-percent">{analysisProgress}%</p>
          </aside>
        </div>

        <form className="search-form elevated-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={courseCode}
            onChange={(event) => setCourseCode(event.target.value.toUpperCase())}
            placeholder="Course code (for example ENGL 1101)"
            disabled={isLoading}
          />
          <input
            type="text"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder="Term (optional, for example 2026 Fall)"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !courseCode.trim()}>
            {isLoading ? 'Finding resources...' : 'Find OER'}
          </button>
        </form>

        {error && <p className="error-banner">{error}</p>}
      </section>

      {results && (
        <section className="simple-panel results-panel">
          <div className="results-panel-head">
            <div>
              <h2 className="results-title">Results for {results.course_code}</h2>
              <p className="subtle-copy results-meta">
                Syllabus source: {results?.syllabus_info?.from_database ? 'Supabase' : 'Live scrape'}
              </p>
            </div>
            <div className="result-count-badge">{normalizedResources.length} resources</div>
          </div>

          <p className="subtle-copy section-copy">
            Ranked by rubric score with criterion-level evidence links so you can verify each signal quickly.
          </p>

          {normalizedResources.length === 0 && <p>No resources were returned for this course.</p>}

          <div className="results-list">
            {normalizedResources.map((resource) => (
              <article key={resource.id} className="result-item">
                <div className="result-header">
                  <h3>{resource.title}</h3>
                  <span className="score-chip">Overall {resource.score.toFixed(1)} / 5</span>
                </div>

                <p>{resource.description}</p>
                <p className="meta-line">License: {resource.license}</p>
                <div className="source-line">
                  <span>Source: {resource.source}</span>
                  {resource.sourceSearchUrl && (
                    <a href={resource.sourceSearchUrl} target="_blank" rel="noopener noreferrer">
                      Browse source listing
                    </a>
                  )}
                </div>

                <dl className="criteria-grid criteria-grid-rich">
                  {CRITERIA_ORDER.map((criterion) => (
                    <React.Fragment key={criterion}>
                      <dt>{criterion}</dt>
                      <dd>
                        <span className="criterion-score">{formatCriterionScore(resource.criteria, criterion)}</span>
                        <a
                          className="criterion-link"
                          href={getCriterionLink(resource, criterion)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Evidence
                        </a>
                      </dd>
                    </React.Fragment>
                  ))}
                </dl>

                <a className="resource-link" href={resource.url} target="_blank" rel="noopener noreferrer">
                  Open resource
                </a>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}

export default HomePage
