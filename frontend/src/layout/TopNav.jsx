import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAppState } from '../context/AppState'

function TopNav() {
  const { isDarkMode, setIsDarkMode } = useAppState()
  const [menuOpen, setMenuOpen] = useState(false)

  const navItems = [
    { to: '/', label: 'Browse' },
    { to: '/scrape', label: 'Scrape Syllabi' },
    { to: '/saved', label: 'Saved Resources' },
  ]

  return (
    <header className="top-nav">
      <div className="top-nav-left">
        <button
          type="button"
          className="icon-btn mobile-only"
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-label="Toggle navigation menu"
          aria-expanded={menuOpen}
        >
          <span className="material-symbols-outlined">{menuOpen ? 'close' : 'menu'}</span>
        </button>
        <span className="brand-wordmark">ScholarFlow Console</span>
        <nav className="top-links">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `top-link ${isActive ? 'active' : ''}`}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="top-nav-right">
        <button
          type="button"
          className="icon-btn"
          onClick={() => setIsDarkMode((prev) => !prev)}
          aria-label="Toggle color theme"
        >
          <span className="material-symbols-outlined">{isDarkMode ? 'light_mode' : 'dark_mode'}</span>
        </button>
        <div className="avatar-pill">Ops</div>
      </div>

      <nav className={`top-links-mobile ${menuOpen ? 'open' : ''}`}>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `top-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

export default TopNav
