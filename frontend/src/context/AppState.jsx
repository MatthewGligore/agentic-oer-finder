import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { isSupabaseConfigured } from '../lib/supabaseClient'
import oerAPI from '../services/oerAPI'

const AppStateContext = createContext(null)
const RUBRIC_CRITERIA = [
  'Open License',
  'Content Quality',
  'Accessibility',
  'Relevance to Course',
  'Currency/Up-to-date',
  'Pedagogical Value',
  'Technical Quality',
]

export function AppStateProvider({ children }) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [courseCode, setCourseCode] = useState('')
  const [term, setTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)
  const [selectedResource, setSelectedResource] = useState(null)
  const [missingSyllabus, setMissingSyllabus] = useState(null)
  const [savedResources, setSavedResources] = useState([])
  const [analysisProgress, setAnalysisProgress] = useState(18)
  const [analysisStage, setAnalysisStage] = useState('Ready')
  const [analysisDetail, setAnalysisDetail] = useState('Waiting for search.')
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [searchStartedAt, setSearchStartedAt] = useState(null)

  useEffect(() => {
    const storedTheme = localStorage.getItem('theme')
    setIsDarkMode(storedTheme === 'dark')
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode)
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light')
  }, [isDarkMode])

  useEffect(() => {
    if (!isLoading) {
      if (!results) {
        setAnalysisStage('Ready')
        setAnalysisDetail('Waiting for search.')
      }
      return
    }

    const stageForElapsed = (elapsedMs) => {
      if (elapsedMs < 5000) {
        return {
          stage: 'Preparing query',
          detail: 'Normalizing course input and loading syllabus context.',
          cap: 34,
        }
      }
      if (elapsedMs < 14000) {
        return {
          stage: 'Scraping sources',
          detail: 'Collecting candidate OER from connected source catalogs.',
          cap: 70,
        }
      }
      if (elapsedMs < 28000) {
        return {
          stage: 'Evaluating resources',
          detail: 'Scoring quality, alignment, and accessibility rubric criteria.',
          cap: 90,
        }
      }
      return {
        stage: 'Final ranking',
        detail: 'Finalizing ranked recommendations and response payload.',
        cap: 97,
      }
    }

    const timer = setInterval(() => {
      const elapsedMs = Date.now() - (searchStartedAt || Date.now())
      const { stage, detail, cap } = stageForElapsed(elapsedMs)
      setAnalysisStage(stage)
      setAnalysisDetail(detail)

      setAnalysisProgress((prev) => {
        if (prev >= cap) {
          return prev
        }

        const bump = Math.floor(Math.random() * 6) + 2
        return Math.min(cap, prev + bump)
      })
    }, 850)

    return () => clearInterval(timer)
  }, [isLoading, results, searchStartedAt])

  const normalizedResources = useMemo(() => {
    const raw = results?.results || []
    const savedByUrl = new Map(savedResources.map((item) => [item.resource_url, item]))
    return raw.map((item, index) => {
      const saved = savedByUrl.get(item.resource_url)
      const resourceUrl = item.resource_url || '#'
      let hostname = 'resource'

      try {
        hostname = new URL(resourceUrl).hostname.replace(/^www\./, '')
      } catch {
        hostname = (item.source || 'resource').toLowerCase()
      }

      const sourceLower = (item.source || '').toLowerCase()
      const visualType = sourceLower.includes('youtube')
        ? 'smart_display'
        : sourceLower.includes('openstax')
          ? 'menu_book'
          : sourceLower.includes('khan')
            ? 'school'
            : 'library_books'

      const thumbnailUrl = item.thumbnail_url
        || item.image_url
        || item.preview_image
        || item.evaluation_payload?.thumbnail_url
        || item.evaluation_payload?.image_url

      const rawScores = item.criteria_scores || {}
      const rawExplanations = item.criteria_explanations || {}
      const criteriaScores = {}
      const criteriaExplanations = {}
      RUBRIC_CRITERIA.forEach((criterion) => {
        criteriaScores[criterion] = Number(rawScores[criterion] ?? 0)
        criteriaExplanations[criterion] = rawExplanations[criterion] || 'No explanation available.'
      })

      return {
        id: item.id || item.resource_url || `${index}-${item.title || 'resource'}`,
        resultId: item.result_id || `${index}-${item.resource_url || 'result'}`,
        searchSessionId: item.search_session_id || results?.search_session_id || null,
        rank: item.rank || index + 1,
        title: item.title || 'Untitled Resource',
        url: resourceUrl,
        description: item.description || 'No description available.',
        license: item.license || 'Unknown license',
        source: item.source || 'Unknown source',
        finalRankScore: Number(item.final_rank_score || 0),
        reasoningSummary: item.reasoning_summary || 'No ranking rationale available.',
        criteriaScores,
        criteriaExplanations,
        evaluationPayload: item.evaluation_payload || {},
        hostname,
        visualType,
        thumbnailUrl: thumbnailUrl || `https://www.google.com/s2/favicons?sz=256&domain=${hostname}`,
        saved: Boolean(saved),
        savedId: saved?.id || null,
      }
    })
  }, [results, savedResources])

  const featuredResource = normalizedResources[0] || null

  const searchResources = async (code, searchTerm) => {
    if (!code.trim()) {
      return false
    }

    setIsLoading(true)
    setError(null)
    setResults(null)
    setMissingSyllabus(null)
    setSelectedResource(null)
    setAnalysisProgress(8)
    setAnalysisStage('Preparing query')
    setAnalysisDetail('Normalizing course input and loading syllabus context.')
    setSearchStartedAt(Date.now())
    setResults({
      course_code: code,
      term: searchTerm,
      resources_found: 0,
      results: [],
      summary: '',
    })

    try {
      let streamError = null
      let streamNotFound = null
      let streamComplete = null

      await oerAPI.searchStream(code, searchTerm, {
        onResource: (event) => {
          const partial = event.resource
          if (!partial) {
            return
          }

          setAnalysisStage('Evaluating resources')
          const evaluatedCount = Number(event.progress?.evaluated_count || 0)
          const totalCandidates = Number(event.progress?.total_candidates || evaluatedCount || 1)
          const pct = Math.min(97, Math.max(25, Math.round((evaluatedCount / Math.max(1, totalCandidates)) * 70 + 20)))
          setAnalysisProgress(pct)
          setAnalysisDetail(`Evaluated ${evaluatedCount} of ${totalCandidates} resources...`)

          setResults((prev) => {
            const current = prev || {
              course_code: code,
              term: searchTerm,
              resources_found: 0,
              results: [],
              summary: '',
            }
            const existing = current.results || []
            const deduped = existing.filter((item) => item.resource_url !== partial.resource_url)
            return {
              ...current,
              course_code: event.course_code || current.course_code || code,
              term: event.term || current.term || searchTerm,
              resources_found: Math.max(current.resources_found || 0, deduped.length + 1),
              results: [...deduped, partial],
            }
          })
        },
        onComplete: (event) => {
          streamComplete = event
        },
        onNotFound: (event) => {
          streamNotFound = event
        },
        onError: (event) => {
          streamError = event
        },
      })

      if (streamError) {
        throw streamError
      }
      if (streamNotFound || streamComplete?.course_not_found || streamComplete?.scrape_required) {
        const payload = streamNotFound || streamComplete
        setMissingSyllabus({
          courseCode: code,
          term: searchTerm,
          message: payload?.error || payload?.summary || 'No stored syllabus found for this course.',
          scrapeUiPath: payload?.scrape_ui_path || '/scrape',
        })
        setError(payload?.error || payload?.summary || 'No stored syllabus found for this course.')
        setAnalysisStage('Search failed')
        setAnalysisDetail('Syllabus data is missing for this course.')
        return false
      }

      if (streamComplete) {
        setResults(streamComplete)
      }

      if (isSupabaseConfigured() && user) {
        try {
          const saved = await oerAPI.listSavedResources(code)
          setSavedResources(saved.saved_resources || [])
        } catch {
          setSavedResources([])
        }
      } else {
        setSavedResources([])
      }
      setAnalysisProgress(100)
      setAnalysisStage('Complete')
      setAnalysisDetail('Search complete. Ranked resources are ready.')
      return true
    } catch (err) {
      if (err?.scrape_required) {
        setMissingSyllabus({
          courseCode: code,
          term: searchTerm,
          message: err.error || 'No stored syllabus found for this course.',
          scrapeUiPath: err.scrape_ui_path || '/scrape',
        })
      }
      setError(err.error || 'An error occurred while searching for OER resources. Please try again.')
      setAnalysisStage('Search failed')
      setAnalysisDetail('Request failed before ranking completed.')
      console.error('Search error:', err)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const refreshSavedResources = useCallback(async (code = '') => {
    if (isSupabaseConfigured() && !user) {
      setSavedResources([])
      return
    }
    try {
      const payload = await oerAPI.listSavedResources(code)
      setSavedResources(payload.saved_resources || [])
    } catch {
      setSavedResources([])
    }
  }, [user])

  const toggleSavedResource = async (resource) => {
    if (isSupabaseConfigured() && !user) {
      navigate('/login')
      return
    }
    try {
      if (resource.saved && resource.savedId) {
        await oerAPI.deleteSavedResource(resource.savedId)
      } else {
        await oerAPI.saveResource({
          course_code: courseCode,
          resource_url: resource.url,
          title: resource.title,
          description: resource.description,
          source: resource.source,
          license: resource.license,
          final_rank_score: resource.finalRankScore,
          reasoning_summary: resource.reasoningSummary,
          evaluation_payload: resource.evaluationPayload,
        })
        await oerAPI.postFeedbackEvent({
          search_session_id: resource.searchSessionId,
          result_id: resource.resultId,
          event_type: 'save',
          course_code: courseCode,
          resource_url: resource.url,
          metadata: { from: 'save_button' },
        })
      }
      await refreshSavedResources(courseCode)
    } catch (err) {
      const message = err?.error || ''
      if (message.toLowerCase().includes('authentication required')) {
        navigate('/login')
        return
      }
      throw err
    }
  }

  const logFeedbackEvent = useCallback(async (payload) => {
    try {
      await oerAPI.postFeedbackEvent(payload)
    } catch (err) {
      console.error('Feedback event failed:', err)
    }
  }, [])

  const submitDispute = useCallback(async (payload) => {
    return oerAPI.disputeRating(payload)
  }, [])

  const value = {
    analysisProgress,
    analysisStage,
    analysisDetail,
    courseCode,
    error,
    featuredResource,
    isDarkMode,
    isLoading,
    missingSyllabus,
    normalizedResources,
    results,
    selectedResource,
    setCourseCode,
    setError,
    setIsDarkMode,
    setMissingSyllabus,
    setSelectedResource,
    setTerm,
    term,
    searchResources,
    savedResources,
    refreshSavedResources,
    logFeedbackEvent,
    submitDispute,
    toggleSavedResource,
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
