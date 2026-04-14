import React, { Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppStateProvider } from './context/AppState'
import AppLayout from './layout/AppLayout'
import DashboardLayout from './layout/DashboardLayout'
import HomePage from './pages/HomePage'
import ResultsPage from './pages/ResultsPage'
import AnalysisPage from './pages/AnalysisPage'
import ScrapeSyllabiPage from './pages/ScrapeSyllabiPage'
import ResourceDetailPage from './pages/ResourceDetailPage'
import AnalyticsPage from './pages/stub/AnalyticsPage'
import SavedResourcesPage from './pages/stub/SavedResourcesPage'
import CollaborationPage from './pages/stub/CollaborationPage'

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
          <Route element={<AppLayout />}>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/scrape" element={<ScrapeSyllabiPage />} />
              <Route path="/resource/:resourceId" element={<ResourceDetailPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/saved" element={<SavedResourcesPage />} />
              <Route path="/collaboration" element={<CollaborationPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AppStateProvider>
  )
}

export default App
