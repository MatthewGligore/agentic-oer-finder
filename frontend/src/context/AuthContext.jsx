import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { supabase } from '../lib/supabaseClient'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null)
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    if (!supabase) {
      setSession(null)
      setUser(null)
      setStatus('anonymous')
      return undefined
    }

    let cancelled = false

    supabase.auth.getSession().then(({ data }) => {
      if (cancelled) return
      const s = data.session
      setSession(s)
      setUser(s?.user ?? null)
      setStatus(s?.user ? 'authed' : 'anonymous')
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setUser(nextSession?.user ?? null)
      setStatus(nextSession?.user ? 'authed' : 'anonymous')
    })

    return () => {
      cancelled = true
      subscription.unsubscribe()
    }
  }, [])

  const value = useMemo(
    () => ({
      session,
      user,
      status,
      supabaseConfigured: Boolean(supabase),
      async signIn(email, password) {
        if (!supabase) return { error: new Error('Supabase is not configured') }
        return supabase.auth.signInWithPassword({ email, password })
      },
      async signUp(email, password) {
        if (!supabase) return { error: new Error('Supabase is not configured') }
        return supabase.auth.signUp({ email, password })
      },
      async signOut() {
        if (!supabase) return
        await supabase.auth.signOut()
      },
    }),
    [session, user, status],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
