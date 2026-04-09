import React from 'react'

const quickCourses = ['ENGL 1101', 'ITEC 1001', 'HIST 2111', 'BIOL 1101K']

function SearchAndUploadSection({ courseCode, term, isLoading, error, onCourseCodeChange, onTermChange, onSubmit }) {
  return (
    <section className="home-grid">
      <div className="search-column">
        <form className="search-pill" onSubmit={onSubmit}>
          <span className="material-symbols-outlined">search</span>
          <input
            type="text"
            value={courseCode}
            onChange={(event) => onCourseCodeChange(event.target.value.toUpperCase())}
            placeholder="Enter course code (e.g., ENGL 1101)"
            disabled={isLoading}
          />
          <input
            type="text"
            value={term}
            onChange={(event) => onTermChange(event.target.value)}
            placeholder="Term (optional, e.g., 2026 Fall)"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !courseCode.trim()}>
            {isLoading ? 'Scraping...' : 'Scrape Syllabi'}
          </button>
        </form>

        {error && <p className="error-banner">{error}</p>}

        <div className="quick-access">
          <span>Quick Access (or type any course):</span>
          {quickCourses.map((code) => (
            <button key={code} type="button" onClick={() => onCourseCodeChange(code)}>
              {code}
            </button>
          ))}
        </div>

        <div className="explore-card glow-reveal">
          <div className="overlay" />
          <div>
            <h3>Scrape by Course Section</h3>
            <p>
              We automatically discover matching syllabus sections in the GGC library,
              extract outcomes and key course details, then map OER resources to that context.
            </p>
          </div>
        </div>
      </div>

      <div className="upload-column">
        <div className="upload-card">
          <div className="upload-icon">
            <span className="material-symbols-outlined">travel_explore</span>
          </div>
          <h2>Scrape Syllabus Section</h2>
          <p>No upload needed. Enter a course code and we scrape matching syllabi online.</p>
          <button type="button" className="ghost-upload" onClick={() => onCourseCodeChange('ENGL 1101')}>Use ENGL 1101</button>
          <button type="button" className="primary-upload" onClick={() => onCourseCodeChange('ITEC 1001')}>Use ITEC 1001</button>
        </div>
      </div>
    </section>
  )
}

export default SearchAndUploadSection
