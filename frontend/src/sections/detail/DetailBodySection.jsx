import React from 'react'
import { Link } from 'react-router-dom'

function DetailBodySection({ resource, scorePercent }) {
  return (
    <>
      <section className="detail-grid">
        <article className="panel syllabus-panel">
          <h3>Syllabus Alignment Snapshot</h3>
          {resource.matchedTopics?.length > 0 ? (
            resource.matchedTopics.map((topic, idx) => (
              <div key={`${topic}-${idx}`} className={`learning-outcome ${idx === 0 ? 'primary' : ''}`}>
                <span>Topic</span>
                <p>{topic}</p>
              </div>
            ))
          ) : (
            <p className="muted-copy">No topic-level matches were extracted for this resource.</p>
          )}
        </article>

        <article className="panel score-panel">
          <div className="score-ring" style={{ '--progress': scorePercent }}>
            <div>
              <strong>{scorePercent}%</strong>
              <span>Match</span>
            </div>
          </div>

          <div className="score-copy">
            <h3>Scoring Breakdown</h3>
            <p>{resource.guidance}</p>

            <div className="meta-row">
              <span>{resource.license}</span>
              <span>Final: {resource.finalRankScore.toFixed(1)}/5</span>
              <span>Rubric: {resource.rubricScore.toFixed(1)}/5</span>
              <span>Relevance: {resource.relevanceScore.toFixed(1)}/5</span>
            </div>

            {resource.relevanceRationale && <p className="muted-copy">{resource.relevanceRationale}</p>}

            <div className="action-row">
              <a href={resource.url} target="_blank" rel="noopener noreferrer">Download Free (OER)</a>
              <Link to="/results">Back to Results</Link>
            </div>
          </div>
        </article>
      </section>

      <section className="panel gap-panel">
        <h3>Criterion-Level Evaluation</h3>
        {resource.criteriaList?.length > 0 ? (
          <dl className="criteria-grid criteria-grid-rich">
            {resource.criteriaList.map((criterion) => (
              <React.Fragment key={criterion.name}>
                <dt>{criterion.name}</dt>
                <dd>
                  <span className="criterion-score">{criterion.score.toFixed(1)} / 5</span>
                  <span className="muted-copy">{criterion.explanation}</span>
                  <a className="criterion-link" href={criterion.evidenceLink} target="_blank" rel="noopener noreferrer">
                    Evidence
                  </a>
                </dd>
              </React.Fragment>
            ))}
          </dl>
        ) : (
          <p className="muted-copy">No criterion details are available for this resource.</p>
        )}
      </section>
    </>
  )
}

export default DetailBodySection
