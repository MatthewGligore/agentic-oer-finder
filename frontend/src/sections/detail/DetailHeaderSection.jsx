import React from 'react'

function DetailHeaderSection({ title }) {
  return (
    <section className="detail-header">
      <p className="chip">Alignment Audit</p>
      <h1>Resource Alignment</h1>
      <p>
        Evaluating <strong>{title}</strong> against your syllabus outcomes and module objectives.
      </p>
    </section>
  )
}

export default DetailHeaderSection
