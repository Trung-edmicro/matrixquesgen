import { useState, useEffect, useCallback } from 'react'

const API_BASE = 'http://localhost:8000'

const STATUS_LABELS = {
  idle: '',
  checking: 'Đang kiểm tra…',
  available: 'Có bản cập nhật mới!',
  downloading: 'Đang tải xuống…',
  installing: 'Đang cài đặt…',
  up_to_date: 'Đang dùng phiên bản mới nhất.',
  error: 'Lỗi khi kiểm tra cập nhật.',
  unavailable: 'Chức năng cập nhật chỉ khả dụng khi chạy từ bản cài đặt.',
}

const STATUS_COLORS = {
  available: 'text-green-600',
  downloading: 'text-blue-600',
  installing: 'text-blue-600',
  up_to_date: 'text-green-600',
  error: 'text-red-600',
  checking: 'text-gray-500',
  unavailable: 'text-gray-400',
}

const AI_PROVIDER_LABELS = {
  gemini: 'Google Gemini',
  openai: 'OpenAI (GPT)',
}

const AI_PROVIDER_DESCRIPTIONS = {
  gemini: 'Sử dụng Google Gemini (Vertex AI) — mặc định',
  openai: 'Sử dụng OpenAI',
}

export default function SettingsPage() {
  const [versionInfo, setVersionInfo] = useState({ version: '…', app_name: 'MatrixQuesGen' })
  const [updateState, setUpdateState] = useState({
    status: 'idle',
    progress: 0,
    message: '',
    latest_version: null,
    changelog: '',
    error: null,
    current_version: null,
  })
  const [polling, setPolling] = useState(false)

  // AI provider state
  const [aiProvider, setAiProvider] = useState('gemini')
  const [aiProviderLoading, setAiProviderLoading] = useState(false)
  const [aiProviderMessage, setAiProviderMessage] = useState('')

  // Fetch current version on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/update/version`)
      .then(r => r.json())
      .then(data => setVersionInfo(data))
      .catch(() => {})

    // Also load last known status
    fetch(`${API_BASE}/api/update/status`)
      .then(r => r.json())
      .then(data => setUpdateState(s => ({ ...s, ...data })))
      .catch(() => {})

    // Load current AI provider
    fetch(`${API_BASE}/api/ai-settings`)
      .then(r => r.json())
      .then(data => setAiProvider(data.ai_provider || 'gemini'))
      .catch(() => {})
  }, [])

  // Poll /status while a job is running
  const pollStatus = useCallback(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/update/status`)
        const data = await res.json()
        setUpdateState(s => ({ ...s, ...data }))

        const done = ['available', 'up_to_date', 'error', 'idle', 'unavailable', 'installing'].includes(data.status)
        if (done) {
          clearInterval(interval)
          setPolling(false)
        }
      } catch {
        clearInterval(interval)
        setPolling(false)
      }
    }, 800)
    return () => clearInterval(interval)
  }, [])

  // Check for update
  const handleCheckUpdate = async () => {
    setUpdateState(s => ({ ...s, status: 'checking', progress: 0, message: 'Đang kiểm tra…', error: null }))
    setPolling(true)
    try {
      await fetch(`${API_BASE}/api/update/check`, { method: 'POST' })
    } catch (e) {
      setUpdateState(s => ({ ...s, status: 'error', message: 'Không kết nối được server.' }))
      setPolling(false)
      return
    }
    pollStatus()
  }

  // Download & install
  const handleDownloadUpdate = async () => {
    setUpdateState(s => ({ ...s, status: 'downloading', progress: 0, message: 'Đang bắt đầu tải…' }))
    setPolling(true)
    try {
      await fetch(`${API_BASE}/api/update/download`, { method: 'POST' })
    } catch (e) {
      setUpdateState(s => ({ ...s, status: 'error', message: 'Không kết nối được server.' }))
      setPolling(false)
      return
    }
    pollStatus()
  }

  // Switch AI provider
  const handleSwitchAiProvider = async (provider) => {
    if (provider === aiProvider || aiProviderLoading) return
    setAiProviderLoading(true)
    setAiProviderMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/ai-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ai_provider: provider }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Lỗi không xác định')
      }
      const data = await res.json()
      setAiProvider(data.ai_provider)
      setAiProviderMessage(`Đã chuyển sang ${AI_PROVIDER_LABELS[data.ai_provider]}.`)
    } catch (e) {
      setAiProviderMessage(`Lỗi: ${e.message}`)
    } finally {
      setAiProviderLoading(false)
    }
  }

  const isRunning = ['checking', 'downloading', 'installing'].includes(updateState.status)
  const showDownloadBtn = updateState.status === 'available'
  const showProgress = ['downloading', 'installing'].includes(updateState.status)

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Cài đặt</h1>

      {/* ── AI Provider card ── */}
      <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h2 className="text-base font-semibold text-gray-700">Nhà cung cấp AI</h2>
        </div>
        <div className="px-6 py-5 space-y-4">
          <p className="text-sm text-gray-500">
            Chọn AI sẽ được sử dụng để sinh câu hỏi. Thay đổi có hiệu lực ngay từ lần sinh tiếp theo.
          </p>

          <div className="flex gap-3">
            {['gemini', 'openai'].map((provider) => {
              const active = aiProvider === provider
              return (
                <button
                  key={provider}
                  onClick={() => handleSwitchAiProvider(provider)}
                  disabled={aiProviderLoading}
                  className={`flex-1 flex flex-col items-start gap-1 px-4 py-3 rounded-lg border-2 text-left transition-colors
                    ${active
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'}
                    ${aiProviderLoading ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <span className={`text-sm font-semibold ${active ? 'text-primary-700' : 'text-gray-700'}`}>
                    {AI_PROVIDER_LABELS[provider]}
                    {active && <span className="ml-2 text-xs font-medium bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded">Đang dùng</span>}
                  </span>
                  <span className="text-xs text-gray-500">{AI_PROVIDER_DESCRIPTIONS[provider]}</span>
                </button>
              )
            })}
          </div>

          {aiProviderLoading && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Spinner /> Đang lưu cài đặt…
            </div>
          )}
          {aiProviderMessage && !aiProviderLoading && (
            <p className={`text-sm ${aiProviderMessage.startsWith('Lỗi') ? 'text-red-600' : 'text-green-600'}`}>
              {aiProviderMessage}
            </p>
          )}
        </div>
      </section>

      {/* ── Version & Update card ── */}
      <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h2 className="text-base font-semibold text-gray-700">Phiên bản & Cập nhật</h2>
        </div>

        <div className="px-6 py-5 space-y-4">
          {/* Version row */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">{versionInfo.app_name}</p>
              <p className="text-sm text-gray-500">
                Phiên bản hiện tại:&nbsp;
                <span className="font-mono font-semibold text-gray-800">
                  v{updateState.current_version || versionInfo.version}
                </span>
                {updateState.latest_version && updateState.latest_version !== (updateState.current_version || versionInfo.version) && (
                  <span className="ml-2 text-green-600 font-semibold">
                    → v{updateState.latest_version} có sẵn
                  </span>
                )}
              </p>
            </div>

            {/* Check button */}
            <button
              onClick={handleCheckUpdate}
              disabled={isRunning || polling}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning && updateState.status === 'checking' ? (
                <Spinner />
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              )}
              Kiểm tra cập nhật
            </button>
          </div>

          {/* Status message */}
          {updateState.status !== 'idle' && (
            <div className={`text-sm ${STATUS_COLORS[updateState.status] || 'text-gray-600'}`}>
              {STATUS_LABELS[updateState.status] || updateState.message}
              {updateState.message &&
                updateState.message !== STATUS_LABELS[updateState.status] && (
                  <span className="ml-1 text-gray-500">— {updateState.message}</span>
              )}
            </div>
          )}

          {/* Progress bar */}
          {showProgress && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-500">
                <span>{updateState.message}</span>
                <span>{updateState.progress}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 transition-all duration-300"
                  style={{ width: `${updateState.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Download button */}
          {showDownloadBtn && (
            <div className="pt-2 space-y-3">
              {updateState.changelog && (
                <details className="text-sm">
                  <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
                    Xem thay đổi
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-50 rounded-lg text-xs text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto border">
                    {updateState.changelog}
                  </pre>
                </details>
              )}
              <button
                onClick={handleDownloadUpdate}
                disabled={isRunning || polling}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isRunning ? <Spinner /> : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                )}
                Tải &amp; cài đặt v{updateState.latest_version}
              </button>
              <p className="text-xs text-gray-400">
                Ứng dụng sẽ tự động khởi động lại sau khi cài đặt hoàn tất.
              </p>
            </div>
          )}

          {/* Installing notice */}
          {updateState.status === 'installing' && (
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <Spinner />
              Trình cài đặt đang chạy. Ứng dụng sẽ tự khởi động lại…
            </div>
          )}
        </div>
      </section>

      {/* ── About card ── */}
      {/* <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h2 className="text-base font-semibold text-gray-700">Thông tin ứng dụng</h2>
        </div>
        <div className="px-6 py-5 space-y-2 text-sm text-gray-600">
          <p><span className="font-medium text-gray-700">Tên:</span> {versionInfo.app_name}</p>
          <p><span className="font-medium text-gray-700">Phiên bản:</span> v{versionInfo.version}</p>
          <p>
            <span className="font-medium text-gray-700">Nguồn mở:</span>{' '}
            <a
              href="https://github.com/your-org/matrixquesgen"
              target="_blank"
              rel="noreferrer"
              className="text-primary-600 hover:underline"
            >
              github.com/your-org/matrixquesgen
            </a>
          </p>
        </div>
      </section> */}
    </div>
  )
}

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}
