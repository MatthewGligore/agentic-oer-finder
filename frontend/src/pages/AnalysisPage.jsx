import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppState } from '../context/AppState'
import AnalysisHeaderSection from '../sections/analysis/AnalysisHeaderSection'
import AnalysisDashboardSection from '../sections/analysis/AnalysisDashboardSection'

function AnalysisPage() {
  const navigate = useNavigate()
  const { analysisProgress, isLoading, results } = useAppState()

  useEffect(() => {
    if (!isLoading && results) {
      navigate('/results')
    }
  }, [isLoading, navigate, results])

  return (
    <main className="canvas with-side-nav">
      <AnalysisHeaderSection />
      <AnalysisDashboardSection analysisProgress={analysisProgress} />
    </main>
  )
}

export default AnalysisPage
