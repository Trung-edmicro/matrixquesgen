import { useState } from 'react'
import MatrixInputPanel from '../components/generate/MatrixInputPanel'
import ExamPreviewPanel from '../components/generate/ExamPreviewPanel'
import ActionBar from '../components/generate/ActionBar'
import { 
  generateQuestions, 
  getGenerationProgress, 
  getSessionDetail,
  exportToDocx,
  downloadDocx 
} from '../services/api'

export default function GenerateExamPage() {
  const [matrixData, setMatrixData] = useState(null)
  const [templateDocx, setTemplateDocx] = useState(null)
  const [pdfFiles, setPdfFiles] = useState(null)
  const [generatedExam, setGeneratedExam] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [error, setError] = useState(null)
  const [isDirty, setIsDirty] = useState(false)
  const [successMessage, setSuccessMessage] = useState(null)
  const generationConfig = {
    max_workers: 10,
    min_interval: 0.2,
    max_retries: 3,
    retry_delay: 2.0
  }

  const handleMatrixUpload = (file) => {
    setMatrixData({ file, filename: file.name })
    setGeneratedExam(null)
    setError(null)
    setIsDirty(false)
  }

  const handleTemplateUpload = (file) => {
    setTemplateDocx({ file, filename: file.name })
    setError(null)
  }

  const handlePdfUpload = (files) => {
    if (files && files.length > 0) {
      setPdfFiles({ files, count: files.length })
    } else {
      setPdfFiles(null)
    }
    setError(null)
  }

  const handleDataChange = (newData) => {
    setGeneratedExam(newData)
    setIsDirty(false)
    setSuccessMessage('Đã lưu thay đổi thành công')
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  const handleGenerate = async () => {
    if (!matrixData?.file) {
      setError('Vui lòng chọn file ma trận')
      return
    }

    setIsGenerating(true)
    setError(null)
    
    try {
      // Upload file và bắt đầu generate
      const result = await generateQuestions(matrixData.file, generationConfig, templateDocx?.file, pdfFiles?.files)
      const newSessionId = result.session_id
      setSessionId(newSessionId)

      // Poll progress với exponential backoff
      let pollDelay = 2000 // Bắt đầu với 2s
      const maxDelay = 10000 // Tối đa 10s
      
      const pollProgress = async () => {
        try {
          const progress = await getGenerationProgress(newSessionId)
          
          console.log('Progress response:', progress) // Debug log
          
          if (progress.status === 'completed') {
            // Load generated questions
            const detail = await getSessionDetail(newSessionId)
            setGeneratedExam(detail)
            setIsGenerating(false)
            setIsDirty(false)
          } else if (progress.status === 'failed') {
            setError(progress.error || 'Lỗi khi sinh câu hỏi')
            setIsGenerating(false)
          } else {
            // Tăng delay dần (exponential backoff)
            pollDelay = Math.min(pollDelay * 1.2, maxDelay)
            setTimeout(pollProgress, pollDelay)
          }
        } catch (err) {
          setError('Lỗi khi kiểm tra tiến độ: ' + err.message)
          setIsGenerating(false)
        }
      }
      
      // Bắt đầu polling
      setTimeout(pollProgress, pollDelay)

    } catch (err) {
      setError('Lỗi khi bắt đầu sinh câu hỏi: ' + err.message)
      setIsGenerating(false)
    }
  }

  const handleExport = async () => {
    if (!sessionId) {
      setError('Không có session để export')
      return
    }

    if (isDirty) {
      setError('Vui lòng lưu thay đổi trước khi xuất file')
      return
    }

    try {
      await exportToDocx(sessionId)
      
      // Download file
      const downloadUrl = downloadDocx(sessionId)
      window.open(downloadUrl, '_blank')
      
      setSuccessMessage('File DOCX đã được tạo và đang tải xuống')
      setTimeout(() => setSuccessMessage(null), 3000)
      
    } catch (err) {
      setError('Lỗi khi export DOCX: ' + err.message)
    }
  }

  return (
    <div className="h-full p-2 flex flex-col">
      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3 flex items-center justify-between">
          <span className="text-sm text-red-800">{error}</span>
          <button 
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Success banner */}
      {successMessage && (
        <div className="bg-green-50 border-b border-green-200 px-4 py-3 flex items-center justify-between">
          <span className="text-sm text-green-800">✓ {successMessage}</span>
          <button 
            onClick={() => setSuccessMessage(null)}
            className="text-green-600 hover:text-green-800"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-200 bg-white">
        <MatrixInputPanel 
          onMatrixUpload={handleMatrixUpload}
          matrixData={matrixData}
          onTemplateUpload={handleTemplateUpload}
          templateDocx={templateDocx}
          onPdfUpload={handlePdfUpload}
          pdfFiles={pdfFiles}
        />
        
        <ActionBar
          onGenerate={handleGenerate}
          onExport={handleExport}
          isGenerating={isGenerating}
          canGenerate={!!matrixData}
          canExport={!!generatedExam && !isDirty}
        />
      </div>

      <div className="flex-1 overflow-hidden">
        <ExamPreviewPanel 
          examData={generatedExam}
          isGenerating={isGenerating}
          sessionId={sessionId}
          onDataChange={handleDataChange}
        />
      </div>
    </div>
  )
}
