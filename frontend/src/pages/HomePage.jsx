import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppState } from '../context/AppState'

function HomePage() {
  const navigate = useNavigate()
  const {
    analysisDetail,
    analysisProgress,
    analysisStage,
    courseCode,
    error,
    isLoading,
    missingSyllabus,
    normalizedResources,
    results,
    searchResources,
    setCourseCode,
    setTerm,
    term,
    toggleSavedResource,
  } = useAppState()

  const resourceCount = normalizedResources.length
  const hasResults = normalizedResources.length > 0
  const scoreAverage = hasResults
    ? (
      normalizedResources.reduce((total, item) => total + Number(item.finalRankScore || 0), 0) / resourceCount
    ).toFixed(2)
    : '0.00'

  const handleSubmit = async (event) => {
    event.preventDefault()
    await searchResources(courseCode, term)
  }

  const quickCourses = ['ENGL 1101', 'ITEC 1001', 'HIST 2111', 'BIOL 1101K']

  const topCriteria = (criteriaScores = {}) => (
    Object.entries(criteriaScores)
      .map(([name, value]) => ({ name, score: Number(value || 0) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 4)
  )

  const scoreBand = (score) => {
    if (score >= 4.3) return 'excellent'
    if (score >= 3.4) return 'strong'
    if (score >= 2.4) return 'fair'
    return 'weak'
  }

  return (
    <main className="canvas dashboard-page">
      <section className="panel dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Agentic OER Finder</p>
          <h1>Discover high-fit OER in one guided workflow.</h1>
          <p className="lead-copy">
            Production-ready discovery console for faculty support teams: scrape, score, rank, and hand off recommendations with confidence.
          </p>

          <div className="dashboard-stats">
            <article className="stat-card">
              <span className="stat-label">Analysis</span>
              <strong>{analysisProgress}%</strong>
              <span className="stat-note">{analysisStage}</span>
            </article>

            <article className="stat-card">
              <span className="stat-label">Results</span>
              <strong>{resourceCount}</strong>
              <span className="stat-note">Ranked resources</span>
            </article>

            <article className="stat-card">
              <span className="stat-label">Avg score</span>
              <strong>{scoreAverage} / 5</strong>
              <span className="stat-note">Current recommendation quality</span>
            </article>
          </div>

          <div className="quick-course-row">
            {quickCourses.map((code) => (
              <button key={code} type="button" className="chip-button" onClick={() => setCourseCode(code)}>
                {code}
              </button>
            ))}
          </div>
        </div>

        <aside className="pipeline-card" aria-live="polite">
          <p className="eyebrow">Discovery pipeline</p>
          <h2>{isLoading ? analysisStage : hasResults ? 'Search complete' : 'Ready to search'}</h2>
          <p>{isLoading ? analysisDetail : hasResults ? 'Ranked resources are ready for review and bookmarking.' : 'Enter a course code to start discovery.'}</p>
          <div className="analysis-meter" role="progressbar" aria-valuenow={analysisProgress} aria-valuemin={0} aria-valuemax={100}>
            <div className="analysis-meter-fill" style={{ width: `${analysisProgress}%` }} />
          </div>
          <p className="pipeline-stage-note">{analysisDetail}</p>
          <div className="pipeline-footer">
            <span>{analysisProgress}% complete</span>
            <button type="button" className="secondary-action" onClick={() => navigate('/saved')}>
              Open Saved
            </button>
          </div>
          {isLoading && (
            <div className="loading-inline">
              <span className="spinner" />
              <span>Running scraping and rubric evaluation...</span>
            </div>
          )}
        </aside>
      </section>

      <section className="panel search-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Course search</p>
            <h2>Search course resources</h2>
            <p className="muted-copy">Use course code and optional term to run a full scrape and evaluation cycle.</p>
          </div>
          <span className="result-badge">{resourceCount ? `${resourceCount} ranked` : 'No results yet'}</span>
        </div>

        <form className="dashboard-search" onSubmit={handleSubmit}>
          <input
            type="text"
            value={courseCode}
            onChange={(event) => setCourseCode(event.target.value.toUpperCase())}
            placeholder="Course code, e.g. ENGL 1101"
            disabled={isLoading}
          />
          <input
            type="text"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder="Term, e.g. 2026 Fall"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !courseCode.trim()}>
            {isLoading ? 'Searching...' : 'Run intelligent search'}
          </button>
        </form>

        {error && <p className="error-banner" role="alert">{error}</p>}

        {missingSyllabus && (
          <div className="empty-results-card" style={{ marginTop: '1rem', textAlign: 'left' }}>
            <p className="empty-results-title">Syllabus missing for {missingSyllabus.courseCode}</p>
            <p>{missingSyllabus.message}</p>
            <div className="action-row" style={{ marginTop: '0.6rem' }}>
              <button
                type="button"
                className="primary-action"
                onClick={() => navigate(missingSyllabus.scrapeUiPath || '/scrape')}
              >
                Open Syllabus Scraper
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="panel dashboard-results">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Results</p>
            <h2>{results ? `Results for ${results.course_code}` : 'Search to populate results'}</h2>
            <p className="muted-copy">
              {results
                ? 'Each card includes rank, score, rationale, rubric snapshot, and save controls.'
                : 'Ranked resources will appear here after search.'}
            </p>
          </div>
        </div>

        {isLoading && !hasResults ? (
          <div className="resource-card-grid single-column">
            {[1, 2, 3].map((card) => (
              <article key={card} className="resource-card skeleton-card">
                <div className="skeleton skeleton-title" />
                <div className="skeleton skeleton-line" />
                <div className="skeleton skeleton-line short" />
                <div className="skeleton skeleton-line" />
              </article>
            ))}
          </div>
        ) : hasResults ? (
          <div className="resource-card-grid" style={{ gridTemplateColumns: '1fr' }}>
            {normalizedResources.map((resource) => (
              <article key={resource.id} className={`resource-card resource-card-rich score-${scoreBand(resource.finalRankScore)}`}>
                <div className="card-section card-header-section">
                  <div className="resource-card-head">
                    <div className="resource-icon-square">
                      <img src={resource.thumbnailUrl} alt={`${resource.title} icon`} loading="lazy" />
                      <span className="material-symbols-outlined">{resource.visualType}</span>
                    </div>
                    <div className="resource-heading-copy">
                      <p className="rank-pill">Rank #{resource.rank}</p>
                      <h3>{resource.title}</h3>
                      <p className="resource-domain">{resource.hostname}</p>
                    </div>
                  </div>
                  <span className="score-chip score-chip-large">{resource.finalRankScore.toFixed(2)} / 5</span>
                </div>

                <div className="card-section card-body-section">
                  <p>{resource.description}</p>
                  <p><strong>Why ranked here:</strong> {resource.reasoningSummary}</p>
                  <div className="meta-row compact">
                    <span>{resource.license}</span>
                    <span>{resource.source}</span>
                  </div>
                </div>

                <div className="card-section card-rubric-section">
                  <p className="rubric-title">Rubric highlights</p>
                  <div className="rubric-strip">
                    {topCriteria(resource.criteriaScores).map(({ name, score }) => (
                      <div key={name} className="rubric-row">
                        <div className="rubric-row-head">
                          <span>{name.replaceAll('_', ' ')}</span>
                          <strong>{score.toFixed(1)} / 5</strong>
                        </div>
                        <div className="rubric-bar">
                          <div style={{ width: `${Math.min(100, Math.max(0, (score / 5) * 100))}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card-section card-footer-section">
                  <div className="action-row">
                    <a href={resource.url} target="_blank" rel="noopener noreferrer">
                      Open resource
                    </a>
                    <button
                      type="button"
                      className="secondary-action"
                      onClick={() => toggleSavedResource(resource)}
                    >
                      {resource.saved ? 'Unsave' : 'Save to library'}
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-results-card">
            <p className="empty-results-title">No ranked results yet.</p>
            <p>Run an intelligent search above to start resource discovery.</p>
          </div>
        )}
      </section>

      <section className="panel dashboard-info-grid">
        <article className="feature-card">
          <span className="material-symbols-outlined">speed</span>
          <div>
            <h3>Fast execution loop</h3>
            <p>Searches stream from scrape to rank with visible progress and clear status indicators.</p>
          </div>
        </article>
        <article className="feature-card">
          <span className="material-symbols-outlined">verified</span>
          <div>
            <h3>Transparent scoring</h3>
            <p>Each recommendation includes rationale and criterion-level signal for review confidence.</p>
          </div>
        </article>
        <article className="feature-card">
          <span className="material-symbols-outlined">dashboard</span>
          <div>
            <h3>Team-ready dashboard</h3>
            <p>Responsive interface with dark-mode ergonomics for long review and curation sessions.</p>
          </div>
        </article>
      </section>
    </main>
  )
}

export default HomePage
