import { useState, useEffect, useCallback } from 'react'
import MatrixInputPanel from '../components/generate/MatrixInputPanel'
import ExamPreviewPanel from '../components/generate/ExamPreviewPanel'
import ActionBar from '../components/generate/ActionBar'
import {
  generateQuestions,
  getGenerationProgress,
  getSessionDetail,
  exportToDocx,
  downloadDocx,
  exportToEnglishExamDocx,
  exportToEnglishStandardDocx,
} from '../services/api'
import { captureAllChartImages } from '../services/chartExportService'
import EnglishExamPreviewPanel from '../components/generate/EnglishExamPreviewPanel'

// Key để lưu state vào localStorage
const STORAGE_KEY = 'matrixquesgen_generate_page_state'
const STORAGE_EXPIRY_HOURS = 5 // Lưu tối đa 5 tiếng

export default function GenerateExamPage() {
  const [matrixData, setMatrixData] = useState(null)
  const [templateDocx, setTemplateDocx] = useState(null)
  const [pdfFiles, setPdfFiles] = useState(null)
  const [generatedExam, setGeneratedExam] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
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

  // Khôi phục state từ localStorage khi component mount
  useEffect(() => {
    try {
      const savedState = localStorage.getItem(STORAGE_KEY)
      if (savedState) {
        const parsed = JSON.parse(savedState)

        // Kiểm tra expiry time
        if (parsed.timestamp) {
          const now = Date.now()
          const expiryTime = parsed.timestamp + (STORAGE_EXPIRY_HOURS * 60 * 60 * 1000)

          if (now > expiryTime) {
            console.log('localStorage data expired, clearing...')
            localStorage.removeItem(STORAGE_KEY)
            return
          }
        }

        if (parsed.generatedExam) {
          setGeneratedExam(parsed.generatedExam)
        }
        if (parsed.sessionId) {
          setSessionId(parsed.sessionId)
        }
        if (parsed.matrixData) {
          setMatrixData(parsed.matrixData)
        }
      }
    } catch (err) {
      console.error('Lỗi khi khôi phục state:', err)
    }
  }, [])

  // Lưu state vào localStorage khi có thay đổi
  useEffect(() => {
    if (generatedExam || sessionId || matrixData) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          generatedExam,
          sessionId,
          matrixData,
          timestamp: Date.now() // Thêm timestamp để kiểm tra expiry
        }))
      } catch (err) {
        console.error('Lỗi khi lưu state:', err)
      }
    }
  }, [generatedExam, sessionId, matrixData])

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

  const handleDataChange = useCallback((newData, showMessage = true) => {
    setGeneratedExam(newData)
    setIsDirty(false)
    if (showMessage) {
      setSuccessMessage('Đã lưu thay đổi thành công')
      setTimeout(() => setSuccessMessage(null), 3000)
    }
  }, [])

  const handleExportEnglishDocx = async () => {

    const storedExam = localStorage.getItem("generatedEnglishExam");

    if (!storedExam) {
      setError("Không có dữ liệu đề tiếng Anh để xuất file")
      return
    }

    const generatedExam = JSON.parse(storedExam)

    try {
      setIsExporting(true)
      setError(null)

      const res1 = await exportToEnglishExamDocx(generatedExam, {
        responseType: "blob"
      })

      downloadFile(res1.data, "English_Exam.docx")

      const res2 = await exportToEnglishStandardDocx(generatedExam, {
        responseType: "blob"
      })

      downloadFile(res2.data, "English_Standard_Exam.docx")

      setSuccessMessage("Đã xuất 2 file DOCX thành công")

    } catch (err) {
      setError("Lỗi khi xuất file: " + err.message)
    } finally {
      setIsExporting(false)
    }
  }

  const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement("a")

    link.href = url
    link.download = filename

    document.body.appendChild(link)
    link.click()

    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  const handleExport = async () => {
    // if (!generatedExam || !sessionId) {
    //   setError('Không có dữ liệu để xuất')
    //   return
    // }

    const isEnglishMatrix = matrixData?.file?.name?.startsWith("MATRIX_ENGLISH_");

    if (isEnglishMatrix) {
      await handleExportEnglishDocx()
      return
    }

    try {
      setIsExporting(true)
      setError(null)
      
      // ✨ NEW: Capture all chart images from the preview
      console.log('📸 Capturing chart images...')
      const chartImages = await captureAllChartImages()
      console.log(`✅ Captured ${Object.keys(chartImages).length} charts`)
      
      // Export to DOCX with chart images
      const exportResult = await exportToDocx(sessionId, chartImages)

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
    } finally {
      setIsExporting(false)
    }
  }

  const handleGenerate = async () => {
    if (!matrixData?.file) {
      setError('Vui lòng chọn file ma trận')
      return;
    }

    const isEnglishMatrix = matrixData.file.name.startsWith("MATRIX_ENGLISH_");
    const isHSKMatrix = matrixData.file.name.startsWith("MATRIX_HSK_");

    // Clear data cũ trước khi sinh đề mới
    setGeneratedExam(null)
    setSessionId(null)
    setIsDirty(false)

    setIsGenerating(true)
    setError(null)

    try {
      // ================================
      // 🟢 FLOW MATRIX_ENGLISH_ OR MATRIX_HSK_
      // ================================
      if (isEnglishMatrix || isHSKMatrix) {
        console.log("English/HSK matrix detected → wait for full response")

        const result = await generateQuestions(
          matrixData.file,
          generationConfig,
          templateDocx?.file,
          pdfFiles?.files
        )


        if (result) {
          console.log(">>>>>>> d123 123 debug", result);
          if (isHSKMatrix) {
            setSuccessMessage("Đã sinh đề HSK thành công! File đã được lưu ở thư mục exports.");
            setGeneratedExam(result);
          } else {
            setGeneratedExam(result)
            localStorage.setItem("generatedEnglishExam", JSON.stringify(result))
            console.log("Saved English exam to localStorage")
          }
        } else {
          setError(result?.error || "Không nhận được phản hồi từ server")
        }
        setIsGenerating(false)
        return
      }

      setGenerationProgress({
        percentage: 0,
        phase: 'initializing',
        status: 'processing'
      })

      const result = await generateQuestions(
        matrixData.file,
        generationConfig,
        templateDocx?.file,
        pdfFiles?.files
      )

      const newSessionId = result.session_id
      setSessionId(newSessionId)

      let pollDelay = 2000
      const maxDelay = 10000

      const pollProgress = async () => {
        try {
          const progress = await getGenerationProgress(newSessionId)

          setGenerationProgress({
            percentage: progress.progress || 0,
            phase: progress.current_phase || '',
            status: progress.status || 'processing'
          })

          if (progress.status === 'completed') {
            const detail = await getSessionDetail(newSessionId)
            setGeneratedExam(detail)
            setIsGenerating(false)
            setIsDirty(false)
          } else if (progress.status === 'failed') {
            setError(progress.error || 'Lỗi khi sinh câu hỏi')
            setIsGenerating(false)
          } else {
            pollDelay = Math.min(pollDelay * 1.2, maxDelay)
            setTimeout(pollProgress, pollDelay)
          }

        } catch (err) {
          setError('Lỗi khi kiểm tra tiến độ: ' + err.message)
          setIsGenerating(false)
        }
      }

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
          <div className="flex items-center gap-4">
            <span className="text-sm text-green-800">✓ {successMessage}</span>
            {successMessage.includes("HSK") && (
              <button
                onClick={() => {
                  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                  fetch(`${API_BASE}/api/generate/open-exports`).catch(err => console.error(err));
                }}
                className="text-xs bg-green-200 text-green-800 px-3 py-1 rounded hover:bg-green-300 font-medium transition"
              >
                Mở thư mục exports
              </button>
            )}
          </div>
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
          isExporting={isExporting}
          canGenerate={!!matrixData}
          canExport={!!generatedExam && !isDirty}
        />
      </div>

      {isGenerating && (
        <div className="progress-bar w-full rounded-full h-1 bg-gray-200">
          <div
            className="bg-[#0369a1] h-1 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${generationProgress.percentage}%` }}
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
        {matrixData?.file?.name?.startsWith("MATRIX_HSK_") && generatedExam ? (
          <div className="h-full flex flex-col items-center justify-center p-8 bg-white m-4 rounded-xl border border-gray-200 shadow-sm">
            <svg className="w-16 h-16 text-green-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-xl font-medium text-gray-900 mb-2">Đã sinh đề HSK thành công!</h3>
            <p className="text-gray-500 mb-6 text-center max-w-md">
              File Excel kết quả đã được lưu trữ trong thư mục exports của hệ thống.
            </p>
            <button
              onClick={() => {
                const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                fetch(`${API_BASE}/api/generate/open-exports`).catch(err => console.error(err));
              }}
              className="px-6 py-2.5 bg-[#0369a1] text-white rounded-lg hover:bg-[#0284c7] transition-colors font-medium flex items-center gap-2 shadow-sm"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
              Mở thư mục chứa file Excel
            </button>
          </div>
        ) : matrixData?.file?.name?.startsWith("MATRIX_ENGLISH_") && generatedExam ? (
          <EnglishExamPreviewPanel examData={generatedExam} />
        ) : matrixData?.file?.name?.startsWith("MATRIX_ENGLISH_") ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            Đang sinh đề tiếng Anh...
          </div>
        ) : (
          <ExamPreviewPanel
            examData={generatedExam}
            isGenerating={isGenerating}
            sessionId={sessionId}
            onDataChange={handleDataChange}
          />
        )}
      </div>
    </div>
  )
}
