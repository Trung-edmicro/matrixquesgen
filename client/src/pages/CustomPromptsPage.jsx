import { useState } from 'react'
import PromptUploader from '../components/generate/PromptUploader'
import VariableInputForm from '../components/generate/VariableInputForm'

export default function CustomPromptsPage() {
  const [sessionData, setSessionData] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState(null)

  const handleUploadSuccess = (data) => {
    setSessionData(data)
    setSuccess(`Upload thành công! Phát hiện ${data.variables.length} biến trong ${data.prompt_count} prompts`)
    setError(null)
    setResult(null)
    
    // Auto clear success message after 3s
    setTimeout(() => setSuccess(null), 3000)
  }

  const handleUploadError = (errorMsg) => {
    setError(errorMsg)
    setSuccess(null)
  }

  const handleGenerate = async (variableValues) => {
    if (!sessionData) {
      setError('Không có session data')
      return
    }

    setGenerating(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/prompts/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionData.session_id,
          variable_values: variableValues,
          num_questions: 10
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Generation failed')
      }

      const data = await response.json()
      setResult(data)
      setSuccess('Generation thành công!')
      
      // Auto clear success message
      setTimeout(() => setSuccess(null), 3000)

    } catch (error) {
      console.error('Generation error:', error)
      setError(error.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleReset = () => {
    setSessionData(null)
    setResult(null)
    setError(null)
    setSuccess(null)
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sinh đề tùy chỉnh</h1>
          <p className="text-sm text-gray-600 mt-1">
            Upload prompts với biến {`{{VARIABLE}}`} và điền giá trị để generate
          </p>
        </div>
        {sessionData && (
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Bắt đầu lại
          </button>
        )}
      </div>

      {/* Alert messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">Lỗi</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-green-700 flex-1">{success}</p>
            <button onClick={() => setSuccess(null)} className="text-green-600 hover:text-green-800">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column: Upload */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            1. Upload Prompts
          </h2>
          
          {!sessionData ? (
            <PromptUploader 
              onUploadSuccess={handleUploadSuccess}
              onError={handleUploadError}
            />
          ) : (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm font-medium text-green-800">
                    Đã upload {sessionData.prompt_count} prompts
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Prompts đã upload:</h4>
                <div className="space-y-1">
                  {Object.keys(sessionData.prompts).map((name) => (
                    <div key={name} className="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {name}
                      <span className="text-xs text-gray-500">
                        ({sessionData.prompts[name].variable_count} biến)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right column: Variables */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            2. Điền Giá Trị Biến
          </h2>
          
          {sessionData ? (
            <VariableInputForm
              prompts={sessionData.prompts}
              variableContexts={sessionData.variable_contexts}
              onSubmit={handleGenerate}
            />
          ) : (
            <div className="text-center py-12 text-gray-500">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
              </svg>
              <p className="text-sm">Upload prompts để bắt đầu</p>
            </div>
          )}
        </div>
      </div>

      {/* Results section */}
      {result && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            3. Kết Quả
          </h2>
          
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">{result.message}</p>
            </div>

            {result.filled_prompts && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-700">Prompts đã fill:</h3>
                {Object.entries(result.filled_prompts).map(([name, content]) => (
                  <details key={name} className="bg-gray-50 rounded-lg">
                    <summary className="px-4 py-3 cursor-pointer hover:bg-gray-100 rounded-lg font-medium text-sm text-gray-700">
                      {name}
                    </summary>
                    <div className="px-4 pb-4 pt-2">
                      <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono bg-white p-3 rounded border border-gray-200">
                        {content}
                      </pre>
                    </div>
                  </details>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {generating && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex flex-col items-center gap-4">
            <svg className="animate-spin h-12 w-12 text-primary-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-700 font-medium">Đang generate...</p>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}
