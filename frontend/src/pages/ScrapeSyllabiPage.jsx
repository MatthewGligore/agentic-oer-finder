import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import oerAPI from '../services/oerAPI'
import { useAppState } from '../context/AppState'

function ScrapeSyllabiPage() {
  const navigate = useNavigate()
  const { courseCode, term, setCourseCode, setTerm } = useAppState()

  const [courseInput, setCourseInput] = useState('')
  const [termInput, setTermInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const scrapeSteps = ['Input validation', 'Remote fetch', 'Normalization', 'Database sync']

  useEffect(() => {
    if (courseCode && !courseInput) {
      setCourseInput(courseCode)
    }
    if (term && !termInput) {
      setTermInput(term)
    }
  }, [courseCode, term, courseInput, termInput])

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
      const data = await oerAPI.scrapeSyllabi(
        normalizedCourse,
        termInput.trim(),
      )
      setResult(data)
      setCourseCode(normalizedCourse)
      setTerm(termInput.trim())
    } catch (err) {
      setError(err.error || 'Scraping failed. Please try again.')
      if (err?.suggested_course_codes || err?.course_not_found) {
        setResult(err)
      } else {
        setResult(null)
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="canvas with-side-nav">
      <section className="results-header scraper-hero">
        <div className="scraper-hero-copy">
          <p className="eyebrow">Syllabus Scraper</p>
          <h1>Capture missing syllabi and refresh source coverage.</h1>
          <p>
            Target one course to enrich your syllabus store. Results immediately feed into resource discovery quality.
          </p>
        </div>
        <div className="scraper-hero-stat">
          <p className="stat-label">Status</p>
          <strong>{isLoading ? 'Scrape running' : 'Ready for scrape'}</strong>
          <p className="stat-note">{isLoading ? 'Live processing in progress' : 'Fast refresh for targeted course coverage'}</p>
        </div>
      </section>

      <section className="result-grid scraper-layout">
        <div className="resource-list-panel">
          <form className="scraper-form-panel" onSubmit={onSubmit}>
            <div className="scraper-form-head">
              <h2>Run a targeted scrape</h2>
              <p className="muted-copy">Search one course at a time and persist any missing records.</p>
            </div>

            <div className="scraper-form-grid">
              <label className="scraper-field">
                <span>Course code</span>
                <input
                  type="text"
                  value={courseInput}
                  onChange={(e) => setCourseInput(e.target.value.toUpperCase())}
                  placeholder="e.g. ITEC 1001"
                  disabled={isLoading}
                />
              </label>
              <label className="scraper-field">
                <span>Term (optional)</span>
                <input
                  type="text"
                  value={termInput}
                  onChange={(e) => setTermInput(e.target.value)}
                  placeholder="e.g. Fall 2025"
                  disabled={isLoading}
                />
              </label>
              <button type="submit" className="primary-action scraper-submit" disabled={isLoading || !courseInput.trim()}>
                {isLoading ? 'Scraping...' : 'Scrape + Store'}
              </button>
            </div>

            <p className="scraper-form-tip">
              Tip: Leave term blank to pull all available matching syllabi.
            </p>
          </form>

          <div className="scrape-step-grid">
            {scrapeSteps.map((step, index) => (
              <div key={step} className={`scrape-step ${isLoading && index <= 2 ? 'active' : ''}`}>
                <span>{index + 1}</span>
                <p>{step}</p>
              </div>
            ))}
          </div>

          {error && <p className="error-banner scraper-error" role="alert">{error}</p>}

          {result && (
            <div className="scraper-result-wrap">
              <div className="featured-resource-card scraper-result-card">
                <h3>{result.course_not_found ? 'No Syllabi Found Yet' : 'Scrape Complete'}</h3>
                <p className="scraper-result-message">
                  {result.message || 'Scrape request finished.'}
                </p>
                <ul className="scraper-result-list">
                  <li>Course: {result.course_code}</li>
                  <li>Matched syllabi: {result.matched_count}</li>
                  <li>Inserted syllabi: {result.inserted_syllabuses}</li>
                  <li>Inserted sections: {result.inserted_sections}</li>
                  <li>Already in DB: {result.skipped_existing}</li>
                  {typeof result.db_total_for_course === 'number' && <li>Total in DB for course: {result.db_total_for_course}</li>}
                </ul>

                {Array.isArray(result.suggested_course_codes) && result.suggested_course_codes.length > 0 && (
                  <div className="scraper-suggestions">
                    <p>Possible matches in library index:</p>
                    <div className="pill-row">
                      {result.suggested_course_codes.map((code) => (
                        <button
                          key={code}
                          type="button"
                          className="pill"
                          onClick={() => setCourseInput(code)}
                        >
                          {code}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="scraper-result-actions">
                <button type="button" className="primary-action" onClick={() => navigate('/')}>
                  Back to Browse
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
