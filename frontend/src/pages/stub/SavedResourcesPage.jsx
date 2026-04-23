import React, { useEffect, useMemo } from 'react'
import { useAppState } from '../../context/AppState'

export default function SavedResourcesPage() {
  const { savedResources, refreshSavedResources, toggleSavedResource } = useAppState()

  useEffect(() => {
    refreshSavedResources()
  }, [refreshSavedResources])

  const sorted = useMemo(
    () => [...savedResources].sort((a, b) => Number(b.final_rank_score || 0) - Number(a.final_rank_score || 0)),
    [savedResources],
  )
  const avgScore = sorted.length
    ? (sorted.reduce((total, item) => total + Number(item.final_rank_score || 0), 0) / sorted.length).toFixed(2)
    : '0.00'

  const getDomain = (url, source) => {
    try {
      return new URL(url).hostname.replace(/^www\./, '')
    } catch {
      return (source || 'resource').toLowerCase()
    }
  }

  const topCriteria = (resource) => {
    const raw = resource.evaluation_payload?.criteria_scores || {}
    return Object.entries(raw)
      .map(([name, value]) => ({ name, score: Number(value || 0) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3)
  }

  return (
    <main className="canvas with-side-nav">
      <section className="results-header">
        <div>
          <p className="eyebrow">Saved Resources</p>
          <h1>Bookmarked OER snapshots with ranking context.</h1>
          <p>Saved cards persist in Supabase with score, source, and rationale from search time.</p>
        </div>
        <div className="header-stat-group">
          <div className="header-stat-card">
            <span>Total saved</span>
            <strong>{sorted.length}</strong>
          </div>
          <div className="header-stat-card">
            <span>Average score</span>
            <strong>{avgScore}</strong>
          </div>
        </div>
      </section>
      <section className="panel dashboard-results">
        {sorted.length === 0 ? (
          <div className="empty-results-card">
            <p className="empty-results-title">No saved resources yet.</p>
            <p>Save any ranked resource from Browse and it will appear here instantly.</p>
          </div>
        ) : (
          <div className="resource-card-grid single-column">
            {sorted.map((resource) => (
              <article key={resource.id} className="resource-card resource-card-rich">
                <div className="card-section card-header-section">
                  <div className="resource-card-head">
                    <div className="resource-icon-square">
                      <img
                        src={
                          resource.evaluation_payload?.thumbnail_url
                          || resource.evaluation_payload?.image_url
                          || `https://www.google.com/s2/favicons?sz=256&domain=${getDomain(resource.resource_url, resource.source)}`
                        }
                        alt={`${resource.title} icon`}
                        loading="lazy"
                      />
                      <span className="material-symbols-outlined">library_books</span>
                    </div>
                    <div className="resource-heading-copy">
                      <p className="rank-pill">Saved resource</p>
                      <h3>{resource.title}</h3>
                      <p className="resource-domain">{getDomain(resource.resource_url, resource.source)}</p>
                    </div>
                  </div>
                  <span className="score-chip score-chip-large">{Number(resource.final_rank_score || 0).toFixed(2)} / 5</span>
                </div>

                <div className="card-section card-body-section">
                  <p>{resource.description}</p>
                  <p><strong>Course:</strong> {resource.course_code}</p>
                  <p><strong>Why ranked here:</strong> {resource.reasoning_summary || 'No summary saved.'}</p>
                  <div className="meta-row compact">
                    <span>{resource.license || 'Unknown license'}</span>
                    <span>{resource.source || 'Unknown source'}</span>
                  </div>
                </div>

                {topCriteria(resource).length > 0 && (
                  <div className="card-section card-rubric-section">
                    <p className="rubric-title">Rubric highlights</p>
                    <div className="rubric-strip">
                      {topCriteria(resource).map(({ name, score }) => (
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
                )}

                <div className="card-section card-footer-section">
                  <div className="action-row">
                    <a href={resource.resource_url} target="_blank" rel="noopener noreferrer">Open resource</a>
                    <button
                      type="button"
                      className="secondary-action"
                      onClick={() => toggleSavedResource({ saved: true, savedId: resource.id })}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
