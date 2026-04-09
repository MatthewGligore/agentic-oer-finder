import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAppState } from '../context/AppState'

function TopNav() {
  const { isDarkMode, setIsDarkMode } = useAppState()

  return (
    <header className="top-nav">
      <div className="top-nav-left">
        <span className="brand-wordmark">ScholarFlow</span>
        <nav className="top-links">
          <NavLink to="/" className={({ isActive }) => `top-link ${isActive ? 'active' : ''}`}>
            Browse
          </NavLink>
          <NavLink to="/scrape" className={({ isActive }) => `top-link ${isActive ? 'active' : ''}`}>
            Scrape Syllabi
          </NavLink>
          <NavLink
            to="/analysis"
            className={({ isActive }) => `top-link ${isActive ? 'active' : ''}`}
          >
            My Syllabus
          </NavLink>
        </nav>
      </div>

      <div className="top-nav-right">
        <button
          type="button"
          className="icon-btn"
          onClick={() => setIsDarkMode((prev) => !prev)}
          aria-label="Toggle color theme"
        >
          <span className="material-symbols-outlined">contrast</span>
        </button>
        <button type="button" className="icon-btn" aria-label="Notifications">
          <span className="material-symbols-outlined">notifications</span>
        </button>
        <button type="button" className="icon-btn" aria-label="Settings">
          <span className="material-symbols-outlined">settings</span>
        </button>
        <div className="avatar-pill">PR</div>
      </div>
    </header>
  )
}

export default TopNav
