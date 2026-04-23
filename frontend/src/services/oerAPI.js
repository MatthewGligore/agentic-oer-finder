import axios from 'axios'

const API_BASE = '/api'

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
        error: 'Failed to search OER resources'
      }
    }
  },

  searchStream: async (courseCode, term = '', handlers = {}) => {
    const response = await fetch(`${API_BASE}/search/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
        error: 'Failed to fetch statistics'
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
        error: 'Failed to scrape syllabi'
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
}

export default oerAPI
