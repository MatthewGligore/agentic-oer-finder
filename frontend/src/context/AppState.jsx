import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import oerAPI from '../services/oerAPI'

const AppStateContext = createContext(null)

export function AppStateProvider({ children }) {
  const [courseCode, setCourseCode] = useState('')
  const [term, setTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)
  const [selectedResource, setSelectedResource] = useState(null)
  const [analysisProgress, setAnalysisProgress] = useState(18)
  const [isDarkMode, setIsDarkMode] = useState(false)

  useEffect(() => {
    const storedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const useDark = storedTheme ? storedTheme === 'dark' : prefersDark
    setIsDarkMode(useDark)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode)
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light')
  }, [isDarkMode])

  useEffect(() => {
    if (!isLoading) {
      return
    }

    const timer = setInterval(() => {
      setAnalysisProgress((prev) => {
        if (prev >= 92) {
          return prev
        }

        const bump = Math.floor(Math.random() * 8) + 2
        return Math.min(92, prev + bump)
      })
    }, 900)

    return () => clearInterval(timer)
  }, [isLoading])

  const normalizedResources = useMemo(() => {
    const raw = results?.evaluated_resources || []

    return raw.map((item, index) => {
      const resource = item.resource || item
      const score = Number(item?.rubric_evaluation?.overall_score || 0)
      const criteria = item?.rubric_evaluation?.criteria_evaluations || {}
      const criterionLinks = item?.criterion_links || {}

      return {
        id: item.id || resource.id || `${index}-${resource.url || resource.title || 'resource'}`,
        title: resource.title || resource.name || 'Untitled Resource',
        url: resource.url || resource.link || '#',
        description: resource.description || 'No description available.',
        license: item?.license_check?.license_type || resource.license || 'Unknown license',
        source: resource.source || resource.source_platform || 'Unknown source',
        sourceSearchUrl: resource.source_search_url || '',
        score,
        criteria,
        criterionLinks,
        guidance: item?.integration_guidance || 'No integration notes available yet.',
      }
    })
  }, [results])

  const featuredResource = normalizedResources[0] || null

  const searchResources = async (code, searchTerm) => {
    if (!code.trim()) {
      return false
    }

    setIsLoading(true)
    setError(null)
    setResults(null)
    setSelectedResource(null)
    setAnalysisProgress(22)

    try {
      const data = await oerAPI.search(code, searchTerm)
      setResults(data)
      setAnalysisProgress(100)
      return true
    } catch (err) {
      setError(err.error || 'An error occurred while searching for OER resources. Please try again.')
      console.error('Search error:', err)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const value = {
    analysisProgress,
    courseCode,
    error,
    featuredResource,
    isDarkMode,
    isLoading,
    normalizedResources,
    results,
    selectedResource,
    setCourseCode,
    setError,
    setIsDarkMode,
    setSelectedResource,
    setTerm,
    term,
    searchResources,
  }

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>
}

export function useAppState() {
  const value = useContext(AppStateContext)

  if (!value) {
    throw new Error('useAppState must be used within AppStateProvider')
  }

  return value
}
