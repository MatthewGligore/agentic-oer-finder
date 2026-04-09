import React from 'react'
import { Link } from 'react-router-dom'

function ResultsContentSection({ error, activeCourseLabel, featuredResource, resources, onSelectResource }) {
  if (error) {
    return <p className="error-banner">{error}</p>
  }

  if (resources.length === 0) {
    return (
      <section className="panel empty-state">
        <span className="material-symbols-outlined">search_off</span>
        <h3>No resources found yet</h3>
        <p>Try another course code or run a broader syllabus search.</p>
        <Link to="/">Back to Search</Link>
      </section>
    )
  }

  return (
    <section className="results-layout">
      <aside className="panel filters-panel">
        <h3>
          <span className="material-symbols-outlined">filter_list</span>
          Refine Search
        </h3>

        <div className="filter-group">
          <p>Syllabus Alignment</p>
          <label><input type="checkbox" defaultChecked /> Ch 1: Atomic Orbitals</label>
          <label><input type="checkbox" defaultChecked /> Ch 2: Molecular Bonds</label>
          <label><input type="checkbox" /> Ch 3: Alkanes</label>
        </div>

        <div className="filter-group">
          <p>License Type</p>
          <div className="pill-row">
            <span className="pill active">CC BY 4.0</span>
            <span className="pill">CC BY-SA</span>
            <span className="pill">Public Domain</span>
          </div>
        </div>
      </aside>

      <div className="result-cards">
        {featuredResource && (
          <article className="panel hero-result">
            <div className="hero-result-media" />
            <div className="hero-result-copy">
              <p className="tiny-tag">{activeCourseLabel} • Primary Match</p>
              <h2>{featuredResource.title}</h2>
              <p>{featuredResource.description}</p>

              <div className="meta-row">
                <span>{featuredResource.license}</span>
                <span>Quality: {featuredResource.score.toFixed(1)}/100</span>
              </div>

              <div className="action-row">
                <Link
                  to={`/resource/${encodeURIComponent(featuredResource.id)}`}
                  onClick={() => onSelectResource(featuredResource)}
                >
                  View Alignment
                </Link>
                <a href={featuredResource.url} target="_blank" rel="noopener noreferrer">Open Resource</a>
              </div>
            </div>
          </article>
        )}

        <div className="mini-grid">
          {resources.slice(1).map((resource) => (
            <article key={resource.id} className="panel mini-card">
              <p className="tiny-tag">Resource</p>
              <h3>{resource.title}</h3>
              <p>{resource.description}</p>

              <div className="meta-row compact">
                <span>{resource.license}</span>
                <span>{resource.score.toFixed(1)}</span>
              </div>

              <Link
                to={`/resource/${encodeURIComponent(resource.id)}`}
                onClick={() => onSelectResource(resource)}
              >
                View Details
              </Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

export default ResultsContentSection
