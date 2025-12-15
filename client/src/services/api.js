import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Generate questions from matrix file
export const generateQuestions = async (file, config = {}) => {
  const formData = new FormData()
  formData.append('file', file)
  
  if (config.max_workers) formData.append('max_workers', config.max_workers)
  if (config.min_interval) formData.append('min_interval', config.min_interval)
  if (config.max_retries) formData.append('max_retries', config.max_retries)
  if (config.retry_delay) formData.append('retry_delay', config.retry_delay)

  const response = await api.post('/api/generate', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// Get generation progress
export const getGenerationProgress = async (sessionId) => {
  const response = await api.get(`/api/generate/${sessionId}/progress`)
  return response.data
}

// List all sessions
export const listSessions = async (params = {}) => {
  const response = await api.get('/api/questions', { params })
  return response.data
}

// Get session detail
export const getSessionDetail = async (sessionId) => {
  const response = await api.get(`/api/questions/${sessionId}`)
  return response.data
}

// Update question
export const updateQuestion = async (sessionId, questionType, questionCode, data) => {
  const response = await api.put(
    `/api/questions/${sessionId}/questions/${questionType}/${questionCode}`,
    data
  )
  return response.data
}

// Export to DOCX
export const exportToDocx = async (sessionId) => {
  const response = await api.post(`/api/export/${sessionId}`)
  return response.data
}

// Download DOCX
export const downloadDocx = (sessionId) => {
  return `${API_BASE_URL}/api/export/${sessionId}/download`
}

// Delete session
export const deleteSession = async (sessionId) => {
  const response = await api.delete(`/api/questions/${sessionId}`)
  return response.data
}

export default api
