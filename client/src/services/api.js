import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Generate questions from matrix file
export const generateQuestions = async (file, config = {}, templateDocx = null, pdfFiles = null) => {
  try {
      const formData = new FormData()
  formData.append('file', file)
  
  // Thêm template DOCX nếu có
  if (templateDocx) {
    formData.append('template_docx', templateDocx)
  }
  
  // Thêm PDF files nếu có
  if (pdfFiles && pdfFiles.length > 0) {
    for (const pdf of pdfFiles) {
      formData.append('pdf_files', pdf)
    }
  }
  
  if (config.max_workers) formData.append('max_workers', config.max_workers)
  if (config.min_interval) formData.append('min_interval', config.min_interval)
  if (config.max_retries) formData.append('max_retries', config.max_retries)
  if (config.retry_delay) formData.append('retry_delay', config.retry_delay)

  const response = await api.post('/api/generate', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
    console.log(">>>>>> debug response", response.data);
  return response.data
  }catch(error) {
    console.log(">>>>>> error", error)
    throw error;
  }

}

export const generateSolutions = async (file, config = {}, templateDocx = null, pdfFiles = null) => {
  try {
      const formData = new FormData()
  formData.append('file', file)
  
  // Thêm template DOCX nếu có
  if (templateDocx) {
    formData.append('template_docx', templateDocx)
  }
  
  // Thêm PDF files nếu có
  if (pdfFiles && pdfFiles.length > 0) {
    for (const pdf of pdfFiles) {
      formData.append('pdf_files', pdf)
    }
  }
  
  if (config.max_workers) formData.append('max_workers', config.max_workers)
  if (config.min_interval) formData.append('min_interval', config.min_interval)
  if (config.max_retries) formData.append('max_retries', config.max_retries)
  if (config.retry_delay) formData.append('retry_delay', config.retry_delay)

  const response = await api.post('/api/solute-english-exam', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
   console.log(">>>>>> debug response", response.data);
  return response.data
  }catch(error) {
    console.log(">>>>>> error", error)
    throw error;
  }

}


export const generateQuestionsEnglish = async (file, config = {}, templateDocx = null, pdfFiles = null) => {
  const formData = new FormData()
  formData.append('file', file)
  
  // Thêm template DOCX nếu có
  if (templateDocx) {
    formData.append('template_docx', templateDocx)
  }
  
  // Thêm PDF files nếu có
  if (pdfFiles && pdfFiles.length > 0) {
    for (const pdf of pdfFiles) {
      formData.append('pdf_files', pdf)
    }
  }
  
  if (config.max_workers) formData.append('max_workers', config.max_workers)
  if (config.min_interval) formData.append('min_interval', config.min_interval)
  if (config.max_retries) formData.append('max_retries', config.max_retries)
  if (config.retry_delay) formData.append('retry_delay', config.retry_delay)

  const response = await api.post('/api/generate', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  console.log(">>>>>> debug response", response.data);
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
  const response = await api.get(`/api/generate/${sessionId}/result`)
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

// export const exportToEnglishDocx = async (
//   generatedExam,
//   config
// ) => {
//   const response = await api.post(
//     `/api/export-english/${sessionId}`,
//     {},
//     config
//   )

//   return response
// }

export const exportToEnglishDocx = async (generatedExam, config) => {
  const response = await api.post(
    `/api/export-english`,
    generatedExam,
    config
  )
  return response
}

export const exportToEnglishExamDocx = async (generatedExam, config) => {
  const response = await api.post(
    `/api/export-english-exam`,
    generatedExam,
    config
  )
  return response
}

export const exportToEnglishStandardDocx = async (generatedExam, config) => {
  const response = await api.post(
    `/api/export-english-standard`,
    generatedExam,
    config
  )
  return response
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

// Regenerate single question
export const regenerateQuestion = async (sessionId, questionType, questionCode) => {
  const response = await api.post('/api/regenerate/question', {
    session_id: sessionId,
    question_type: questionType,
    question_code: questionCode
  })
  return response.data
}

// Regenerate multiple questions
export const regenerateBulkQuestions = async (sessionId, questions) => {
  const response = await api.post('/api/regenerate/bulk', {
    session_id: sessionId,
    questions: questions  // [{ type: 'TN', code: 'C1' }, ...]
  })
  return response.data
}

export default api
export const editQuestion = async (sessionId, questionType, questionCode, comment) => {
  const response = await api.post('/api/regenerate/edit', {
    session_id: sessionId,
    question_type: questionType,
    question_code: questionCode,
    comment: comment
  })
  return response.data
}
