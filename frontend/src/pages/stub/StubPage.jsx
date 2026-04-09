import React from 'react'

function StubPage({ title, description, icon }) {
  return (
    <main className="canvas with-side-nav">
      <section style={{ textAlign: 'center', padding: '3rem 1rem' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 'inherit' }}>
            {icon}
          </span>
        </div>
        <h1 style={{ marginBottom: '0.5rem', color: 'var(--primary)' }}>{title}</h1>
        <p style={{ color: 'var(--muted)', maxWidth: '500px', margin: '0 auto' }}>
          {description}
        </p>
      </section>
    </main>
  )
}

export default StubPage
