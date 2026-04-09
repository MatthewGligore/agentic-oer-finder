import React from 'react'

function AnalysisDashboardSection({ analysisProgress }) {
  return (
    <section className="analysis-grid">
      <article className="panel progress-panel">
        <div className="meter">
          <div style={{ width: `${analysisProgress}%` }} />
        </div>

        <div className="metric-row">
          <h3>{analysisProgress}%</h3>
          <span>Semantic Mapping</span>
        </div>

        <div className="scan-lines">
          <div className="scan-line muted">[SCANNING] Section III: Nucleophilic Substitution</div>
          <div className="scan-line active">[IDENTIFIED CORE TOPIC] Hydrocarbon Structural Isomerism</div>
          <div className="scan-line muted">[QUEUED] Stereochemistry and chirality module</div>
        </div>
      </article>

      <article className="panel topics-panel">
        <h3>Detected Topics</h3>
        <div className="topic-list">
          <div className="topic-item">
            <span className="material-symbols-outlined">check_circle</span>
            Carbon Bonding
          </div>
          <div className="topic-item">
            <span className="material-symbols-outlined">check_circle</span>
            Functional Groups
          </div>
          <div className="topic-item in-progress">
            <span className="material-symbols-outlined spin">sync</span>
            Substitution Reactions
          </div>
          <div className="topic-item muted">
            <span className="material-symbols-outlined">schedule</span>
            NMR Spectroscopy
          </div>
        </div>
      </article>
    </section>
  )
}

export default AnalysisDashboardSection
