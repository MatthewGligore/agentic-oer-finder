import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AuthPage() {
  const { signIn, supabaseConfigured, status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/saved'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (status === 'authed') {
      navigate(from, { replace: true })
    }
  }, [status, from, navigate])

  if (!supabaseConfigured) {
    return (
      <main className="app-shell">
        <section className="dashboard-hero">
          <h1>Sign in unavailable</h1>
          <p className="hero-lede">
            Add <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> to enable accounts.
          </p>
          <Link className="btn-primary" to="/">
            Back to browse
          </Link>
        </section>
      </main>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const { error: err } = await signIn(email.trim(), password)
      if (err) {
        setError(err.message || 'Authentication failed')
        return
      }
      navigate(from, { replace: true })
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="app-shell auth-page-shell">
      <section className="auth-card">
        <p className="eyebrow">Welcome back</p>
        <h1>Sign in to your account</h1>
        <p className="muted-copy">Access your saved resources and personalized library.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="auth-email">
            Email
          </label>
          <input
            id="auth-email"
            type="email"
            autoComplete="email"
            className="text-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label className="field-label" htmlFor="auth-password" style={{ marginTop: '0.75rem' }}>
            Password
          </label>
          <input
            id="auth-password"
            type="password"
            autoComplete="current-password"
            className="text-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />

          {error ? (
            <p className="error-banner" style={{ marginTop: '0.75rem' }}>
              {error}
            </p>
          ) : null}

          <div className="action-row auth-actions" style={{ marginTop: '1rem' }}>
            <button type="submit" className="primary-action" disabled={busy}>
              {busy ? 'Signing in...' : 'Sign in'}
            </button>
            <Link className="secondary-action auth-link-btn" to="/register">
              Create account
            </Link>
          </div>
        </form>

        <p style={{ marginTop: '1rem', textAlign: 'center' }}>
          <Link to="/">← Back to browse</Link>
        </p>
      </section>
    </main>
  )
}
