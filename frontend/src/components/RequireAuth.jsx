import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RequireAuth({ children }) {
  const { user, status, supabaseConfigured } = useAuth()
  const location = useLocation()

  if (!supabaseConfigured) {
    return children
  }

  if (status === 'loading') {
    return (
      <main className="app-shell">
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <div className="spinner" style={{ display: 'inline-block', width: '2rem', height: '2rem' }} />
          <p style={{ marginTop: '1rem', opacity: 0.8 }}>Checking session…</p>
        </div>
      </main>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}
