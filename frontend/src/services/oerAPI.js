import axios from 'axios'
import { supabase } from '../lib/supabaseClient'

/** Empty in dev (Vite proxies /api). Set VITE_API_BASE_URL on Netlify to your Cloudflare tunnel API origin, no trailing slash. */
const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const API_BASE = API_ORIGIN ? `${API_ORIGIN}/api` : '/api'

function isApiRequestUrl(url) {
  if (typeof url !== 'string') return false
  if (url.startsWith('/api')) return true
  if (API_ORIGIN && url.startsWith(`${API_ORIGIN}/api`)) return true
  return false
}

async function authHeaders() {
  if (!supabase) return {}
  const {
    data: { session },
  } = await supabase.auth.getSession()
  if (!session?.access_token) return {}
  return { Authorization: `Bearer ${session.access_token}` }
}

axios.interceptors.request.use(async (config) => {
  const url = config.url || ''
  if (isApiRequestUrl(url)) {
    Object.assign(config.headers, await authHeaders())
  }
  return config
})

const oerAPI = {
  search: async (courseCode, term = '') => {
    try {
      const response = await axios.post(`${API_BASE}/search`, {
        course_code: courseCode,
        term: term,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || {
        error: 'Failed to search OER resources',
      }
    }
  },

  searchStream: async (courseCode, term = '', handlers = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...(await authHeaders()),
    }

    const response = await fetch(`${API_BASE}/search/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        course_code: courseCode,
        term,
      }),
    })

    if (!response.ok) {
      let payload = null
      try {
        payload = await response.json()
      } catch {
        payload = null
      }
      throw payload || { error: 'Failed to search OER resources' }
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw { error: 'Streaming is not supported in this browser.' }
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        break
      }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) {
          continue
        }

        let event
        try {
          event = JSON.parse(trimmed)
        } catch {
          continue
        }

        if (event.type === 'resource' && handlers.onResource) {
          handlers.onResource(event)
        } else if (event.type === 'complete' && handlers.onComplete) {
          handlers.onComplete(event)
        } else if (event.type === 'not_found' && handlers.onNotFound) {
          handlers.onNotFound(event)
        } else if (event.type === 'error' && handlers.onError) {
          handlers.onError(event)
        }
      }
    }
  },

  getStats: async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`)
      return response.data
    } catch (error) {
      throw error.response?.data || {
        error: 'Failed to fetch statistics',
      }
    }
  },

  scrapeSyllabi: async (courseCode, term = '') => {
    try {
      const response = await axios.post(`${API_BASE}/scrape-syllabi`, {
        course_code: courseCode,
        term,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || {
        error: 'Failed to scrape syllabi',
      }
    }
  },

  listSavedResources: async (courseCode = '') => {
    try {
      const response = await axios.get(`${API_BASE}/saved-resources`, {
        params: courseCode ? { course_code: courseCode } : {},
      })
      return response.data
    } catch (error) {
      throw error.response?.data || { error: 'Failed to load saved resources' }
    }
  },

  saveResource: async (payload) => {
    try {
      const response = await axios.post(`${API_BASE}/saved-resources`, payload)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: 'Failed to save resource' }
    }
  },

  deleteSavedResource: async (id) => {
    try {
      const response = await axios.delete(`${API_BASE}/saved-resources/${id}`)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: 'Failed to remove saved resource' }
    }
  },

  postFeedbackEvent: async (payload) => {
    try {
      const response = await axios.post(`${API_BASE}/feedback/event`, payload)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: 'Failed to submit feedback event' }
    }
  },

  disputeRating: async (payload) => {
    try {
      const response = await axios.post(`${API_BASE}/feedback/dispute`, payload)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: 'Failed to submit dispute' }
    }
  },
}

export default oerAPI
