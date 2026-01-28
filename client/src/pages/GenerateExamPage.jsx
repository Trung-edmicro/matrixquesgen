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
  const [generationProgress, setGenerationProgress] = useState({
    percentage: 0,
    phase: '',
    status: 'idle'
  })
  const generationConfig = {
    max_workers: 10,
    min_interval: 0.2,
    max_retries: 3,
    retry_delay: 2.0
  }

  const getPhaseDisplayName = (phase) => {
    const phaseNames = {
      'initializing': 'Khởi tạo...',
      'phase1_matrix_processing': 'Xử lý ma trận đề',
      'phase2_content_acquisition': 'Thu thập nội dung',
      'phase3_content_mapping': 'Xử lý nội dung liên quan',
      'phase4_question_generation': 'Sinh câu hỏi',
      'saving_results': 'Lưu kết quả',
      'completed': 'Hoàn thành',
      'failed': 'Lỗi',
      'error': 'Lỗi'
    }
    return phaseNames[phase] || 'Đang xử lý...'
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

  const handleExport = async () => {
    if (!generatedExam || !sessionId) {
      setError('Không có dữ liệu để xuất')
      return
    }

    try {
      setError(null)
      // Export to DOCX
      const exportResult = await exportToDocx(sessionId)
      
      if (exportResult && exportResult.file_path) {
        // Download the file
        const downloadUrl = downloadDocx(sessionId)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = exportResult.file_name || `questions_${sessionId}.docx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        setSuccessMessage('Đã xuất file DOCX thành công')
        setTimeout(() => setSuccessMessage(null), 3000)
      } else {
        setError('Lỗi khi xuất file: ' + (exportResult?.error || 'Unknown error'))
      }
    } catch (err) {
      setError('Lỗi khi xuất file: ' + err.message)
    }
  }

  const handleGenerate = async () => {
    if (!matrixData?.file) {
      setError('Vui lòng chọn file ma trận')
      return
    }

    setIsGenerating(true)
    setError(null)
    setGenerationProgress({
      percentage: 0,
      phase: 'initializing',
      status: 'processing'
    })
    
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
          
          // Cập nhật progress state
          setGenerationProgress({
            percentage: progress.progress || 0,
            phase: progress.current_phase || '',
            status: progress.status || 'processing'
          })
          
          if (progress.status === 'completed') {
            // Load generated questions
            const detail = await getSessionDetail(newSessionId)
            setGeneratedExam(detail)
            setIsGenerating(false)
            setIsDirty(false)
            setGenerationProgress({
              percentage: 0, // Reset to 0% to hide progress bar
              phase: 'completed',
              status: 'completed'
            })
          } else if (progress.status === 'failed') {
            setError(progress.error || 'Lỗi khi sinh câu hỏi')
            setIsGenerating(false)
            setGenerationProgress({
              percentage: 0,
              phase: 'failed',
              status: 'failed'
            })
          } else {
            // Tăng delay dần (exponential backoff)
            pollDelay = Math.min(pollDelay * 1.2, maxDelay)
            setTimeout(pollProgress, pollDelay)
          }
        } catch (err) {
          setError('Lỗi khi kiểm tra tiến độ: ' + err.message)
          setIsGenerating(false)
          setGenerationProgress({
            percentage: 0,
            phase: 'error',
            status: 'error'
          })
        }
      }
      
      // Bắt đầu polling
      setTimeout(pollProgress, pollDelay)

    } catch (err) {
      setError('Lỗi khi bắt đầu sinh câu hỏi: ' + err.message)
      setIsGenerating(false)
    }
  }

  const handleTestProgress = () => {
    // Removed mock progress simulation
  }

  return (
    <div className="h-full p-2 flex flex-col overflow-hidden">
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

      {isGenerating && (
        <div className="progress-bar w-full rounded-full h-1 bg-gray-200">
          <div 
            className="bg-[#0369a1] h-1 rounded-full transition-all duration-300 ease-out" 
            style={{width: `${generationProgress.percentage}%`}}
          ></div>
        </div>
      )}
      
      {isGenerating && (
        <div className="px-4 py-2 bg-blue-50 border-b border-blue-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-blue-800">
              Đang xử lý: {getPhaseDisplayName(generationProgress.phase)}
            </span>
            <span className="text-blue-600 font-medium">
              {generationProgress.percentage}%
            </span>
          </div>
        </div>
      )}

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
