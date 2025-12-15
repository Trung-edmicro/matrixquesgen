import { useState, useEffect } from 'react'
import { listSessions, deleteSession, exportToDocx, downloadDocx } from '../services/api'

export default function ManageExamsPage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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
      await exportToDocx(sessionId)
      const downloadUrl = downloadDocx(sessionId)
      window.open(downloadUrl, '_blank')
    } catch (err) {
      setError('Lỗi khi export: ' + err.message)
    }
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
    <div className="p-2">
      <div className="mb-2 flex items-center justify-between">
        <h1 className="text-xl font-medium text-gray-900">Quản lý đề đã sinh</h1>
        <button 
          onClick={loadSessions}
          className="btn-secondary text-xs"
        >
          Làm mới
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 px-4 py-3 rounded">
          <span className="text-sm text-red-800">{error}</span>
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="panel p-6 text-center text-gray-500">
          Chưa có session nào
        </div>
      ) : (
        <div className="panel overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
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
                    {session.total_questions} ({session.tn_count} TN, {session.ds_count} DS)
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
      )}
    </div>
  )
}
