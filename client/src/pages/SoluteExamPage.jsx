import { useState, useEffect, useCallback } from 'react'
import ActionBar from '../components/generate/ActionBar'
import ExamPreviewPanel from '../components/generate/ExamPreviewPanel'
import EnglishExamPreviewPanel from '../components/generate/EnglishExamPreviewPanel'
import {
  generateQuestions, // hoặc đổi thành solveExam nếu backend tách riêng
  getGenerationProgress,
  getSessionDetail,
  exportToDocx,
  downloadDocx
} from '../services/api'
import SoluteActionBar from '../components/generate/SoluteActionBar'

// Storage
const STORAGE_KEY = 'matrixquesgen_solute_page_state'
const STORAGE_EXPIRY_HOURS = 5

export default function SoluteExamPage() {
  const [examPdf, setExamPdf] = useState(null)
  const [generatedExam, setGeneratedExam] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const [isDirty, setIsDirty] = useState(false)

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

  // =========================
  // Restore state
  // =========================
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (!saved) return

      const parsed = JSON.parse(saved)

      if (parsed.timestamp) {
        const expiry = parsed.timestamp + STORAGE_EXPIRY_HOURS * 3600 * 1000
        if (Date.now() > expiry) {
          localStorage.removeItem(STORAGE_KEY)
          return
        }
      }

      if (parsed.generatedExam) setGeneratedExam(parsed.generatedExam)
      if (parsed.sessionId) setSessionId(parsed.sessionId)
      if (parsed.examPdf) setExamPdf(parsed.examPdf)

    } catch (err) {
      console.error('Restore error:', err)
    }
  }, [])

  // =========================
  // Save state
  // =========================
  useEffect(() => {
    if (generatedExam || sessionId || examPdf) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          generatedExam,
          sessionId,
          // examPdf,
          timestamp: Date.now()
        }))
      } catch (err) {
        console.error('Save error:', err)
      }
    }
  }, [generatedExam, sessionId, examPdf])

  // =========================
  // Upload PDF
  // =========================
  const handlePdfUpload = (files) => {
    if (files && files.length > 0) {
      setExamPdf({ files, count: files.length })
    } else {
      setExamPdf(null)
    }

    setGeneratedExam(null)
    setSessionId(null)
    setError(null)
    setIsDirty(false)
  }

  const handleExportEnglishDocx = async() => {

  }
  
  // =========================
  // Solve Exam
  // =========================
  const handleSolve = async () => {
    
    if (!examPdf?.files) {
      setError('Vui lòng chọn file PDF đề bài')
      return
    }

    const isEnglishPdf = examPdf.file.name.startsWith("ENGLISH_PDF_");

    if(isEnglishPdf) {
      return;
    }

    setGeneratedExam(null)
    setSessionId(null)
    setIsGenerating(true)
    setError(null)

    try {
      setGenerationProgress({
        percentage: 0,
        phase: 'initializing',
        status: 'processing'
      })

      if(isEnglishPdf) {
        
      }

      const result = await generateQuestions(
        null, // không dùng matrix
        generationConfig,
        null,
        examPdf.files
      )

      const newSessionId = result.session_id
      setSessionId(newSessionId)

      let delay = 2000
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
            setError(progress.error || 'Lỗi khi giải đề')
            setIsGenerating(false)
          } else {
            delay = Math.min(delay * 1.2, maxDelay)
            setTimeout(pollProgress, delay)
          }

        } catch (err) {
          setError('Lỗi khi kiểm tra tiến độ: ' + err.message)
          setIsGenerating(false)
        }
      }

      setTimeout(pollProgress, delay)

    } catch (err) {
      setError('Lỗi khi bắt đầu giải đề: ' + err.message)
      setIsGenerating(false)
    }
  }

  // =========================
  // Export DOCX
  // =========================
  const handleExport = async () => {
    if (!sessionId) {
      setError('Không có dữ liệu để xuất')
      return
    }

    try {
      setIsExporting(true)
      setError(null)

      const exportResult = await exportToDocx(sessionId)

      if (exportResult && exportResult.file_path) {
        const url = downloadDocx(sessionId)

        const link = document.createElement('a')
        link.href = url
        link.download = exportResult.file_name || `solution_${sessionId}.docx`

        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        setSuccessMessage('Đã xuất file DOCX thành công')
        setTimeout(() => setSuccessMessage(null), 3000)
      } else {
        setError('Lỗi khi xuất file')
      }

    } catch (err) {
      setError('Lỗi khi xuất file: ' + err.message)
    } finally {
      setIsExporting(false)
    }
  }

  const handleDataChange = useCallback((data) => {
    setGeneratedExam(data)
    setIsDirty(false)
  }, [])

  // =========================
  // UI
  // =========================
  return (
    <div className="h-full p-2 flex flex-col overflow-hidden">

      {/* Error */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <span className="text-sm text-red-800">{error}</span>
        </div>
      )}

      {/* Success */}
      {successMessage && (
        <div className="bg-green-50 border-b border-green-200 px-4 py-3">
          <span className="text-sm text-green-800">✓ {successMessage}</span>
        </div>
      )}

      {/* Top bar (INPUT + BUTTON cùng hàng) */}
      <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-200 bg-white">

        {/* Upload PDF */}
        <div className="flex items-center gap-3">
          <input
            type="file"
            accept="application/pdf"
            multiple
            onChange={(e) => handlePdfUpload(e.target.files)}
            className="text-sm"
          />

          {examPdf && (
            <span className="text-xs text-gray-500">
              {examPdf.count} file đã chọn
            </span>
          )}
        </div>

        {/* Action buttons */}
        <SoluteActionBar
          onSolve={handleSolve}
          onExport={handleExport}
          isGenerating={isGenerating}
          isExporting={isExporting}
          examPdf={examPdf}
          generatedExam={generatedExam}
          isDirty={isDirty}
        />

      </div>

      {/* Progress bar */}
      {isGenerating && (
        <div className="w-full h-1 bg-gray-200">
          <div
            className="bg-[#0369a1] h-1 transition-all"
            style={{ width: `${generationProgress.percentage}%` }}
          />
        </div>
      )}

      {/* Progress text */}
      {isGenerating && (
        <div className="px-4 py-2 bg-blue-50 text-sm text-blue-800">
          Đang xử lý: {generationProgress.phase} ({generationProgress.percentage}%)
        </div>
      )}

      {/* Preview */}
      <div className="flex-1 overflow-hidden">
        {examPdf?.files?.[0]?.name?.startsWith("ENGLISH_") ? (
          <EnglishExamPreviewPanel examData={generatedExam} />
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