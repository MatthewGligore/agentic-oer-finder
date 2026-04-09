import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppState } from '../context/AppState'
import ResultsHeaderSection from '../sections/results/ResultsHeaderSection'
import ResultsContentSection from '../sections/results/ResultsContentSection'

function ResultsPage() {
  const navigate = useNavigate()
  const {
    courseCode,
    error,
    featuredResource,
    normalizedResources,
    setSelectedResource,
  } = useAppState()

  const activeCourseLabel = courseCode || 'CHEM-101'

  return (
    <main className="canvas with-side-nav">
      <ResultsHeaderSection activeCourseLabel={activeCourseLabel} onImportNew={() => navigate('/')} />
      <ResultsContentSection
        error={error}
        activeCourseLabel={activeCourseLabel}
        featuredResource={featuredResource}
        resources={normalizedResources}
        onSelectResource={setSelectedResource}
      />
    </main>
  )
}

export default ResultsPage
