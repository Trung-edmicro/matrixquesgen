import axios from 'axios'
import testdata from '../components/generate/testdata.json'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Generate questions from matrix file
export const generateQuestions = async (file, config = {}, templateDocx = null, pdfFiles = null) => {
  // const USE_MOCK = true;

  //   if (USE_MOCK) {
  //   console.log("🚀 USING MOCK DATA - SKIP API");

  //   // giả lập delay giống AI (optional)
  //   await new Promise(res => setTimeout(res, 800));

  //   return testdata;
  // }

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
      // formData.append('pdf_files', pdf)
    }
  }
  
  if (config.max_workers) formData.append('max_workers', config.max_workers)
  if (config.min_interval) formData.append('min_interval', config.min_interval)
  if (config.max_retries) formData.append('max_retries', config.max_retries)
  if (config.retry_delay) formData.append('retry_delay', config.retry_delay)


  const response = await api.post('/api/generate', formData,{
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
  console.log(">>>>>> debug response", response.data);
  return response.data
  }catch(error) {
    console.log(error);
    console.log(">>>>>> error", error);
    throw error;
  }

}

export const handleRegenerateEnglishQuestion = async (block, q, userFeedback) => {
  const payload = {
    type: block.type,
    topic: block.title,
    spec: block.spec,      
    level: block.level,      
    diff: block.diff,      
    text_type: block.text_type,
    question_number: q ? (q.number || (q.parsed && q.parsed.question_number)) : null,
    user_feedback: userFeedback || "Sinh lại nội dung câu hỏi này",
    passage: block.parsed?.passage || block.passage || "",
    passage_title: block.parsed?.passage_title || block.passage_title || "",
    current_question_data: q || block.parsed
  };
  console.log(">>>>>> debug payload ", payload);

  const response =  await api.post('/api/regenerate-english/regenerate-one-question', payload);

  return response.data;
};


export const handleGenerateArrangeEnglishQuestion = async (
  block,
  userFeedback
) => {
  const parsed = block?.parsed || {}

  const payload = {
    type: block.type,
    topic: block.title,
    spec: block.spec,
    level: block.level,
    diff: block.diff,
    text_type: block.text_type,
    text_type_en: block.text_type_en,
    question_number: parsed.question_number,
    user_feedback:
      userFeedback || "Sinh lại câu hỏi sắp xếp hội thoại này",
    current_question_data: {
      question_number: parsed.question_number,
      question_stem: parsed.question_stem,
      option_a: parsed.option_a,
      option_b: parsed.option_b,
      option_c: parsed.option_c,
      option_d: parsed.option_d,
      answer: parsed.answer,
      solution_lines: parsed.solution_lines || [],
      translation_lines: parsed.translation_lines || [],
    },
  }

  console.log(
    ">>>>> debug arrange payload",
    payload
  )

  const response = await api.post(
    "/api/regenerate-english/regenerate-one-question",
    payload
  )

  console.log(
    ">>>>> debug arrange response",
    response
  )

  return response.data
}

export const generateQuestionsEnglishTHCS = async (file) => {
  try {
      const formData = new FormData()
      formData.append('file', file)
            
      const response = await api.post('/api/generate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
        // console.log(">>>>>> debug response", response.data);
      return response.data
      }catch(error) {
        console.log(">>>>>> error", error);
        throw error;
      }

}

export const generateSolutions = async (file, config = {}, pdfFiles = null) => {
  const formData = new FormData()

  try {
    formData.append('file', file)

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

    // console.log(">>>>>> debug response english", response.data)
    return response.data

  } catch (error) {
    console.log(">>>>>> error generate solutions", error)
    throw error
  } finally {
    // Cleanup file tạm
    try {
      if (file && file instanceof File) {
        // Nếu là object URL thì revoke
        if (file.preview) {
          URL.revokeObjectURL(file.preview)
        }
      }

      if (pdfFiles && pdfFiles.length > 0) {
        for (const pdf of pdfFiles) {
          if (pdf.preview) {
            URL.revokeObjectURL(pdf.preview)
          }
        }
      }

      console.log(">>>>>> cleaned up temp files")
    } catch (cleanupError) {
      console.log(">>>>>> error during cleanup", cleanupError)
      throw cleanupError;
    }
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
  // console.log(">>>>>> debug response", response.data);
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
export const exportToDocx = async (sessionId, chartImages = {}) => {
  const response = await api.post(`/api/export/${sessionId}`, {
    chart_images: chartImages
  })
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

export const exportToSolutedEnglishExamDocx = async (generatedExam, config) => {
  const response = await api.post(
    `/api/export-soluted-english-exam`,
    generatedExam,
    config
  )
  return response
}

export const exportToSolutedEnglishStandardDocx = async (generatedExam, config) => {
  const response = await api.post(
    `/api/export-soluted-standard-english-exam`,
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

export const exportToEnglishExamDocxTHCS = async (generatedExam, config) => {
  const response = await api.post(
    `/api/export-english-exam-thcs`,
    generatedExam,
    config
  )
  return response
}



export const exportToEnglishStandardDocxTHCS = async (generatedExam, config) => {
  const response = await api.post(
    `/api/export-english-standard-exam-thcs`,
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

export const editQuestion = async (sessionId, questionType, questionCode, comment) => {
  const response = await api.post('/api/regenerate/edit', {
    session_id: sessionId,
    question_type: questionType,
    question_code: questionCode,
    comment: comment
  })
  return response.data
}

// Update chart_raw_data, regenerate echarts, và save file JSON
export const updateChartData = async (sessionId, questionType, questionCode, chartRawData) => {
  const response = await api.put('/api/chart/update', {
    session_id: sessionId,
    question_type: questionType,
    question_code: questionCode,
    chart_raw_data: chartRawData
  })
  return response.data
}

// ===== Math Template Selection APIs =====

// Get enriched matrix for template selection
export const getEnrichedMatrix = async (sessionId) => {
  const response = await api.get(`/api/math-template/${sessionId}/enriched-matrix`)
  return response.data
}

// Save template selections
export const saveTemplateSelections = async (sessionId, selections) => {
  const payload = {
    session_id: sessionId,
    selections: selections
  }
  console.log('[API] All selections before filter:', selections.length)
  console.log('[API] Saving selections:', JSON.stringify(payload, null, 2))
  const response = await api.post(`/api/math-template/${sessionId}/save-selections`, payload)
  return response.data
}

// Continue to phase 4 after template selection
export const continueToPhase4 = async (sessionId) => {
  const response = await api.post(`/api/math-template/${sessionId}/continue-to-phase4`)
  return response.data
}

// ── History DS material selection ──────────────────────────────────────────────

// Get enriched matrix for DS material selection (LICHSU and similar subjects)
export const getEnrichedMatrixForMaterial = async (sessionId) => {
  const response = await api.get(`/api/history-material/${sessionId}/enriched-matrix`)
  return response.data
}

// Save DS material selections (user picks one material per DS question)
export const saveMaterialSelections = async (sessionId, selections) => {
  const payload = {
    session_id: sessionId,
    selections: selections
  }
  const response = await api.post(`/api/history-material/${sessionId}/save-selections`, payload)
  return response.data
}

// Continue to phase 4 after material selection
export const continueToPhase4AfterMaterial = async (sessionId) => {
  const response = await api.post(`/api/history-material/${sessionId}/continue-to-phase4`)
  return response.data
}

// Request more AI-filtered materials for a DS question
export const getMoreMaterials = async (sessionId, { lessonIndex, questionIndex, questionCode, alreadyShown }) => {
  const response = await api.post(`/api/history-material/${sessionId}/more-materials`, {
    lesson_index: lessonIndex,
    question_index: questionIndex,
    question_code: questionCode,
    already_shown: alreadyShown
  })
  return response.data
}

export default api
