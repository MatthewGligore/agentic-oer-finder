import React, { Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppStateProvider } from './context/AppState'
import RequireAuth from './components/RequireAuth'
import AppLayout from './layout/AppLayout'
import DashboardLayout from './layout/DashboardLayout'
import AuthPage from './pages/AuthPage'
import RegisterPage from './pages/RegisterPage'
import HomePage from './pages/HomePage'
import ScrapeSyllabiPage from './pages/ScrapeSyllabiPage'
import SavedResourcesPage from './pages/stub/SavedResourcesPage'

function LoadingFallback() {
  return (
    <main className="app-shell">
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="spinner" style={{ display: 'inline-block', width: '2rem', height: '2rem' }} />
      </div>
    </main>
  )
}

function App() {
  return (
    <AppStateProvider>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<AppLayout />}>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/scrape" element={<ScrapeSyllabiPage />} />
              <Route
                path="/saved"
                element={
                  <RequireAuth>
                    <SavedResourcesPage />
                  </RequireAuth>
                }
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AppStateProvider>
  )
}

export default App
