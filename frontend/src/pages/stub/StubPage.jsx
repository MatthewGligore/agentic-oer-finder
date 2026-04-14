import React from 'react'

function StubPage({ title, description, icon }) {
  return (
    <main className="canvas with-side-nav">
      <section className="panel empty-state-card">
        <div className="empty-state-icon">
          <span className="material-symbols-outlined">{icon}</span>
        </div>
        <h1>{title}</h1>
        <p>{description}</p>
      </section>
    </main>
  )
}

export default StubPage
