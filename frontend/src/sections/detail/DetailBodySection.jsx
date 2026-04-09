import React from 'react'
import { Link } from 'react-router-dom'

function DetailBodySection({ resource, scorePercent }) {
  return (
    <>
      <section className="detail-grid">
        <article className="panel syllabus-panel">
          <h3>Syllabus Module Snapshot</h3>

          <div className="learning-outcome">
            <span>LO 3.1</span>
            <p>Nucleophilic Substitution (SN1/SN2)</p>
          </div>
          <div className="learning-outcome primary">
            <span>LO 3.2</span>
            <p>Elimination Reactions (E1/E2)</p>
          </div>
          <div className="learning-outcome">
            <span>LO 3.3</span>
            <p>Carbocation Rearrangements</p>
          </div>
        </article>

        <article className="panel score-panel">
          <div className="score-ring" style={{ '--progress': scorePercent }}>
            <div>
              <strong>{scorePercent}%</strong>
              <span>Match</span>
            </div>
          </div>

          <div className="score-copy">
            <h3>Strong Alignment</h3>
            <p>{resource.guidance}</p>

            <div className="meta-row">
              <span>{resource.license}</span>
              <span>Score: {resource.score.toFixed(1)}/100</span>
            </div>

            <div className="action-row">
              <a href={resource.url} target="_blank" rel="noopener noreferrer">Download Free (OER)</a>
              <Link to="/results">Back to Results</Link>
            </div>
          </div>
        </article>
      </section>

      <section className="panel gap-panel">
        <h3>Identified Content Gaps</h3>
        <p>
          Carbocation rearrangements coverage appears thin in this resource. Consider adding a
          supplemental module to fully satisfy LO 3.3.
        </p>
        <button type="button">Find Supplements</button>
      </section>
    </>
  )
}

export default DetailBodySection
