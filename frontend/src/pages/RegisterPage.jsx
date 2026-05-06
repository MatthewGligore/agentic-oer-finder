import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { signUp, supabaseConfigured, status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/saved'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
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
          <h1>Registration unavailable</h1>
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
    setNotice(null)
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    try {
      const { error: err } = await signUp(email.trim(), password)
      if (err) {
        setError(err.message || 'Registration failed')
        return
      }
      setNotice('Account created. If email confirmation is enabled, check your inbox.')
      navigate(from, { replace: true })
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="app-shell auth-page-shell">
      <section className="auth-card">
        <p className="eyebrow">Get started</p>
        <h1>Create your account</h1>
        <p className="muted-copy">Register to save resources and keep a personal OER library.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="register-email">
            Email
          </label>
          <input
            id="register-email"
            type="email"
            autoComplete="email"
            className="text-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label className="field-label" htmlFor="register-password" style={{ marginTop: '0.75rem' }}>
            Password
          </label>
          <input
            id="register-password"
            type="password"
            autoComplete="new-password"
            className="text-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />

          <label className="field-label" htmlFor="register-confirm" style={{ marginTop: '0.75rem' }}>
            Confirm password
          </label>
          <input
            id="register-confirm"
            type="password"
            autoComplete="new-password"
            className="text-input"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={6}
          />

          {error ? (
            <p className="error-banner" style={{ marginTop: '0.75rem' }}>
              {error}
            </p>
          ) : null}
          {notice ? <p className="muted-copy">{notice}</p> : null}

          <div className="action-row auth-actions" style={{ marginTop: '1rem' }}>
            <button type="submit" className="primary-action" disabled={busy}>
              {busy ? 'Creating account...' : 'Create account'}
            </button>
            <Link className="secondary-action auth-link-btn" to="/login">
              Back to sign in
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
