import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import oerAPI from '../services/oerAPI'
import { useAppState } from '../context/AppState'

function ScrapeSyllabiPage() {
  const navigate = useNavigate()
  const { setCourseCode, setTerm } = useAppState()

  const [courseInput, setCourseInput] = useState('')
  const [termInput, setTermInput] = useState('')
  const [limitInput, setLimitInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const onSubmit = async (event) => {
    event.preventDefault()

    const normalizedCourse = courseInput.trim().toUpperCase()
    if (!normalizedCourse) {
      setError('Please enter a course code (e.g., ITEC 1001).')
      return
    }

    setIsLoading(true)
    setError('')
    setResult(null)

    try {
      const parsedLimit = Number(limitInput)
      const data = await oerAPI.scrapeSyllabi(
        normalizedCourse,
        termInput.trim(),
        Number.isFinite(parsedLimit) && parsedLimit > 0 ? parsedLimit : 0,
      )
      setResult(data)
      setCourseCode(normalizedCourse)
      setTerm(termInput.trim())
    } catch (err) {
      setError(err.error || 'Scraping failed. Please try again.')
      setResult(null)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="canvas with-side-nav">
      <section className="results-header">
        <div>
          <p className="eyebrow">Syllabus Scraper</p>
          <h1>Scrape Syllabi by Course Code</h1>
          <p>
            Enter any course like ITEC 1001 or ENGL 1101. We scrape matching syllabi and store
            missing ones in Supabase.
          </p>
        </div>
      </section>

      <section className="result-grid" style={{ gridTemplateColumns: '1fr', marginTop: '1rem' }}>
        <div className="resource-list-panel">
          <form className="search-pill" onSubmit={onSubmit} style={{ borderRadius: '1rem' }}>
            <span className="material-symbols-outlined">travel_explore</span>
            <input
              type="text"
              value={courseInput}
              onChange={(e) => setCourseInput(e.target.value.toUpperCase())}
              placeholder="Course code (e.g., ITEC 1001)"
              disabled={isLoading}
            />
            <input
              type="text"
              value={termInput}
              onChange={(e) => setTermInput(e.target.value)}
              placeholder="Term (optional)"
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !courseInput.trim()}>
              {isLoading ? 'Scraping...' : 'Scrape + Store'}
            </button>
          </form>

          <div style={{ marginTop: '0.8rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <label htmlFor="limitInput" style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
              Limit (optional):
            </label>
            <input
              id="limitInput"
              type="number"
              min="1"
              value={limitInput}
              onChange={(e) => setLimitInput(e.target.value)}
              placeholder="e.g. 25"
              disabled={isLoading}
              style={{ maxWidth: '120px' }}
            />
          </div>

          {error && <p className="error-banner" style={{ marginTop: '1rem' }}>{error}</p>}

          {result && (
            <div style={{ marginTop: '1rem' }}>
              <div className="featured-resource-card">
                <h3 style={{ marginTop: 0 }}>Scrape Complete</h3>
                <p style={{ marginBottom: '0.75rem', color: 'var(--muted)' }}>{result.message}</p>
                <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
                  <li>Course: {result.course_code}</li>
                  <li>Matched syllabi: {result.matched_count}</li>
                  <li>Inserted syllabi: {result.inserted_syllabuses}</li>
                  <li>Inserted sections: {result.inserted_sections}</li>
                  <li>Already in DB: {result.skipped_existing}</li>
                  <li>Total in DB for course: {result.db_total_for_course}</li>
                </ul>
              </div>

              <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                <button type="button" className="primary-action" onClick={() => navigate('/')}>
                  Back to Search
                </button>
                <button type="button" className="secondary-action" onClick={() => navigate('/results')}>
                  View OER Results
                </button>
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

export default ScrapeSyllabiPage
