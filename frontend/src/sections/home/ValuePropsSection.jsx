import React from 'react'

function ValuePropsSection() {
  return (
    <section className="value-grid">
      <article>
        <p className="value-kicker">
          <span className="material-symbols-outlined">verified</span> OER Verified
        </p>
        <h4>Compliance First</h4>
        <p>Resources are checked for license compliance and accessibility standards.</p>
      </article>

      <article>
        <p className="value-kicker">
          <span className="material-symbols-outlined">auto_awesome</span> Semantic Analysis
        </p>
        <h4>Smart Mapping</h4>
        <p>AI suggestions are ranked against outcomes and assessment language.</p>
      </article>

      <article>
        <p className="value-kicker">
          <span className="material-symbols-outlined">group</span> Institutional Network
        </p>
        <h4>Peer Insights</h4>
        <p>See what educators across institutions adopt for matching course structures.</p>
      </article>
    </section>
  )
}

export default ValuePropsSection
