import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAppState } from '../context/AppState'

function SideNav() {
  const { courseCode } = useAppState()
  const activeCourseLabel = courseCode || 'CHEM-101'

  return (
    <aside className="side-nav">
      <div className="context-card">
        <div className="context-icon">
          <span className="material-symbols-outlined">school</span>
        </div>
        <div>
          <p className="context-title">Course Context</p>
          <p className="context-subtitle">{activeCourseLabel}: Organic Chem</p>
        </div>
      </div>

      <nav className="side-nav-links">
        <NavLink to="/scrape" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">travel_explore</span>
          Scrape Syllabi
        </NavLink>
        <NavLink to="/analysis" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">description</span>
          Current Syllabus
        </NavLink>
        <NavLink to="/results" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">library_books</span>
          Course Materials
        </NavLink>
        <NavLink to="/saved" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">bookmark</span>
          Saved Resources
        </NavLink>
        <NavLink to="/collaboration" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">group</span>
          Collaboration
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined">analytics</span>
          Analytics
        </NavLink>
      </nav>

      <button type="button" className="export-btn">
        Export to LMS
      </button>
    </aside>
  )
}

export default SideNav
