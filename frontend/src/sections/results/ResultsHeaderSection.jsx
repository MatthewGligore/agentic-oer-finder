import React from 'react'

function ResultsHeaderSection({ activeCourseLabel, onImportNew }) {
  return (
    <section className="results-header">
      <div>
        <p className="eyebrow">Curation Hub</p>
        <h1>Discovered OER Resources</h1>
        <p>
          Curated resources aligned with {activeCourseLabel} and filtered for open-license use.
        </p>
      </div>

      <div className="header-actions">
        <button type="button" className="secondary-action">Advanced Filters</button>
        <button type="button" className="primary-action" onClick={onImportNew}>Scrape Another Course</button>
      </div>
    </section>
  )
}

export default ResultsHeaderSection
