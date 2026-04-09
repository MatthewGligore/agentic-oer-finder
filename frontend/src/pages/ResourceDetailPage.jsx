import React, { useMemo } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { useAppState } from '../context/AppState'
import DetailHeaderSection from '../sections/detail/DetailHeaderSection'
import DetailBodySection from '../sections/detail/DetailBodySection'

function ResourceDetailPage() {
  const { resourceId } = useParams()
  const { normalizedResources, selectedResource } = useAppState()

  const routeResource = useMemo(() => {
    const decodedId = decodeURIComponent(resourceId || '')
    return normalizedResources.find((item) => item.id === decodedId) || null
  }, [normalizedResources, resourceId])

  const resource = routeResource || selectedResource

  if (!resource) {
    return <Navigate to="/results" replace />
  }

  const scorePercent = Math.max(55, Math.min(98, Math.round((resource.score / 100) * 100) || 90))

  return (
    <main className="canvas with-side-nav">
      <DetailHeaderSection title={resource.title} />
      <DetailBodySection resource={resource} scorePercent={scorePercent} />
    </main>
  )
}

export default ResourceDetailPage
