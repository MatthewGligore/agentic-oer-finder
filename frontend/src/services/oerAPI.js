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
}

export default oerAPI
