import React, { Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppStateProvider } from './context/AppState'

// Lazy-loaded pages
const HomePage = React.lazy(() => import('./pages/HomePage'))

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
          <Route path="/" element={<HomePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AppStateProvider>
  )
}

export default App
