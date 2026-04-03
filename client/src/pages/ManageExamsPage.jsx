import { useState, useEffect } from 'react'
import { listSessions, deleteSession, exportToDocx, downloadDocx, getSessionDetail } from '../services/api'
import { captureAllChartImages } from '../services/chartExportService'
import ExamPreviewPanel from '../components/generate/ExamPreviewPanel'

export default function ManageExamsPage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedSession, setSelectedSession] = useState(null)
  const [viewingExam, setViewingExam] = useState(null)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const data = await listSessions({ limit: 100, status: 'completed' })
      setSessions(data.sessions)
      setError(null)
    } catch (err) {
      setError('Lỗi khi tải danh sách: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (sessionId) => {
    if (!confirm('Bạn có chắc muốn xóa session này?')) return

    try {
      await deleteSession(sessionId)
      await loadSessions() // Reload list
    } catch (err) {
      setError('Lỗi khi xóa: ' + err.message)
    }
  }

  const handleExport = async (sessionId) => {
    try {
      // ✨ NEW: Try to capture chart images from the preview (if rendered)
      const chartImages = await captureAllChartImages()
      console.log(`📸 Export: captured ${Object.keys(chartImages).length} charts`)
      
      const exportResult = await exportToDocx(sessionId, chartImages)
      if (exportResult && exportResult.file_path) {
        const downloadUrl = downloadDocx(sessionId)
        window.open(downloadUrl, '_blank')
      } else {
        setError('Lỗi khi export: ' + (exportResult?.error || 'Unknown error'))
      }
    } catch (err) {
      setError('Lỗi khi export: ' + err.message)
    }
  }

  const handleView = async (sessionId) => {
    try {
      setSelectedSession(sessionId)
      const examData = await getSessionDetail(sessionId)
      setViewingExam(examData)
    } catch (err) {
      setError('Lỗi khi tải chi tiết: ' + err.message)
    }
  }

  const handleCloseView = () => {
    setSelectedSession(null)
    setViewingExam(null)
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleString('vi-VN')
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-sm text-gray-500">Đang tải...</div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden p-2">
      <div className="mb-2 flex items-center justify-between flex-shrink-0">
        <h1 className="text-xl font-medium text-gray-900">Quản lý đề đã sinh</h1>
        <button 
          onClick={loadSessions}
          className="btn-secondary text-xs"
        >
          Làm mới
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 px-4 py-3 rounded flex-shrink-0">
          <span className="text-sm text-red-800">{error}</span>
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="panel p-6 text-center text-gray-500">
          Chưa có session nào
        </div>
      ) : (
        <div className="flex-1 panel overflow-hidden flex flex-col min-h-0">
          <div className="overflow-y-auto flex-1">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700">File ma trận</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700">Số câu</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700">Thời gian</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700">Trạng thái</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sessions.map((session) => (
                  <tr key={session.session_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{session.matrix_file}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {session.total_questions} ({session.tn_count} TN, {session.ds_count} DS, {session.tln_count || 0} TLN, {session.tl_count || 0} TL)
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDate(session.generated_at)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                        {session.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleView(session.session_id)}
                          className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                        >
                          Xem
                        </button>
                        <button 
                          onClick={() => handleExport(session.session_id)}
                          className="text-xs text-primary-600 hover:text-primary-700"
                        >
                          Xuất
                        </button>
                        <button 
                          onClick={() => handleDelete(session.session_id)}
                          className="text-xs text-red-600 hover:text-red-700"
                        >
                          Xóa
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* View Exam Modal */}
      {viewingExam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
              <h2 className="text-lg font-medium text-gray-900">Xem chi tiết đề thi</h2>
              <button 
                onClick={handleCloseView}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <ExamPreviewPanel 
                examData={viewingExam}
                isGenerating={false}
                sessionId={null}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
