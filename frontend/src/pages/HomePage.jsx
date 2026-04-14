import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppState } from '../context/AppState'

function HomePage() {
  const navigate = useNavigate()
  const {
    analysisProgress,
    courseCode,
    error,
    featuredResource,
    isLoading,
    normalizedResources,
    results,
    searchResources,
    setCourseCode,
    setTerm,
    term,
  } = useAppState()

  const resourceCount = normalizedResources.length
  const hasResults = Boolean(results)

  const handleSubmit = async (event) => {
    event.preventDefault()
    await searchResources(courseCode, term)
  }

  const quickCourses = ['ENGL 1101', 'ITEC 1001', 'HIST 2111', 'BIOL 1101K']

  return (
    <main className="canvas dashboard-page">
      <section className="panel dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Agentic OER Finder</p>
          <h1>Search OER from a dashboard that keeps the workflow in view.</h1>
          <p className="lead-copy">
            Start with a course code, track syllabus analysis in real time, and review the best-fit open resources without leaving the page.
          </p>

          <div className="dashboard-stats">
            <article className="stat-card">
              <span className="stat-label">Analysis</span>
              <strong>{analysisProgress}%</strong>
              <span className="stat-note">Pipeline progress</span>
            </article>

            <article className="stat-card">
              <span className="stat-label">Results</span>
              <strong>{resourceCount}</strong>
              <span className="stat-note">Ranked resources</span>
            </article>

            <article className="stat-card">
              <span className="stat-label">Syllabus source</span>
              <strong>{results?.syllabus_info?.from_database ? 'Supabase' : 'Live scrape'}</strong>
              <span className="stat-note">Latest lookup path</span>
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
          <h2>{isLoading ? 'Analyzing resources' : 'Ready to search'}</h2>
          <p>
            {isLoading
              ? 'Running syllabus checks, source discovery, and rubric scoring.'
              : 'Enter a course code to start ranking open resources.'}
          </p>
          <div className="analysis-meter" role="progressbar" aria-valuenow={analysisProgress} aria-valuemin={0} aria-valuemax={100}>
            <div className="analysis-meter-fill" style={{ width: `${analysisProgress}%` }} />
          </div>
          <div className="pipeline-footer">
            <span>{analysisProgress}% complete</span>
            <button type="button" className="secondary-action" onClick={() => navigate('/results')} disabled={!hasResults}>
              Open Results
            </button>
          </div>
        </aside>
      </section>

      <section className="panel search-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Course search</p>
            <h2>Find OER resources</h2>
            <p className="muted-copy">Search by course code and optional term. The dashboard updates as soon as the analysis finishes.</p>
          </div>
          <span className="result-badge">{resourceCount ? `${resourceCount} ranked` : 'Waiting for search'}</span>
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
            {isLoading ? 'Searching...' : 'Search OER'}
          </button>
        </form>

        {error && <p className="error-banner">{error}</p>}
      </section>

      <section className="panel dashboard-results">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Results</p>
            <h2>{results ? `Results for ${results.course_code}` : 'Search to populate the dashboard'}</h2>
            <p className="muted-copy">
              {results
                ? 'The strongest match is highlighted first, with the remaining resources arranged in a quick scan grid.'
                : 'Your search results will appear here, including scores, licenses, and source links.'}
            </p>
          </div>

          {hasResults && (
            <button type="button" className="primary-action" onClick={() => navigate('/results')}>
              View Full Results
            </button>
          )}
        </div>

        {hasResults ? (
          <>
            {featuredResource && (
              <article className="featured-resource-card">
                <div className="featured-resource-copy">
                  <p className="tiny-tag">Primary match</p>
                  <h3>{featuredResource.title}</h3>
                  <p>{featuredResource.description}</p>

                  <div className="meta-row">
                    <span>{featuredResource.license}</span>
                    <span>Score {featuredResource.score.toFixed(1)} / 100</span>
                  </div>

                  <div className="action-row">
                    <a href={featuredResource.url} target="_blank" rel="noopener noreferrer">
                      Open resource
                    </a>
                    {featuredResource.sourceSearchUrl && (
                      <a href={featuredResource.sourceSearchUrl} target="_blank" rel="noopener noreferrer">
                        Browse source
                      </a>
                    )}
                  </div>
                </div>
              </article>
            )}

            <div className="resource-card-grid">
              {normalizedResources.slice(1).map((resource) => (
                <article key={resource.id} className="resource-card">
                  <div className="resource-card-head">
                    <h3>{resource.title}</h3>
                    <span className="score-chip">{resource.score.toFixed(1)} / 100</span>
                  </div>

                  <p>{resource.description}</p>

                  <div className="meta-row compact">
                    <span>{resource.license}</span>
                    <span>{resource.source}</span>
                  </div>

                  <a href={resource.url} target="_blank" rel="noopener noreferrer">
                    Open resource
                  </a>
                </article>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-results-card">
            <p className="empty-results-title">No search has been run yet.</p>
            <p>Enter a course code above to bring back the dashboard-style workflow.</p>
          </div>
        )}
      </section>
    </main>
  )
}

export default HomePage
