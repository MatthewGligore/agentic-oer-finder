import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAppState } from '../context/AppState'

function SideNav() {
  const { courseCode } = useAppState()
  const activeCourseLabel = courseCode || 'No course selected'
  const contextHint = courseCode ? 'Active search context' : 'Set from Browse or Scrape'

  return (
    <aside className="side-nav">
      <div className="context-card">
        <div className="context-icon">
          <span className="material-symbols-outlined">school</span>
        </div>
        <div>
          <p className="context-title">Course Context</p>
          <p className="context-subtitle">{activeCourseLabel}</p>
          <p className="context-note">{contextHint}</p>
        </div>
      </div>

      <div className="side-status-card">
        <p className="context-title">System Status</p>
        <p className="context-subtitle">
          <span className="status-dot" />
          Search services online
        </p>
        <p className="context-note">Realtime scraping and ranking are available.</p>
      </div>

      <nav className="side-nav-links">
        <NavLink to="/" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">search</span>
          Browse
        </NavLink>
        <NavLink to="/scrape" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">travel_explore</span>
          Scrape Syllabi
        </NavLink>
        <NavLink to="/saved" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">bookmark</span>
          Saved Resources
        </NavLink>
      </nav>

    </aside>
  )
}

export default SideNav
