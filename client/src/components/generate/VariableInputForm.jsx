import { useState, useMemo } from 'react'

export default function VariableInputForm({ prompts = {}, variableContexts = {}, onSubmit }) {
  const [values, setValues] = useState({})
  const [expandedVars, setExpandedVars] = useState({})
  const [errors, setErrors] = useState({})
  const [selectedPrompt, setSelectedPrompt] = useState(null)

  // Auto-select first prompt
  useMemo(() => {
    if (!selectedPrompt && Object.keys(prompts).length > 0) {
      setSelectedPrompt(Object.keys(prompts)[0])
    }
  }, [prompts, selectedPrompt])

  // Get all unique variables across all prompts
  const allVariables = useMemo(() => {
    const vars = new Set()
    Object.values(prompts).forEach(prompt => {
      prompt.variables.forEach(v => vars.add(v))
    })
    return Array.from(vars)
  }, [prompts])

  // Get variables for selected prompt
  const currentPromptVariables = useMemo(() => {
    if (!selectedPrompt || !prompts[selectedPrompt]) return []
    return prompts[selectedPrompt].variables
  }, [selectedPrompt, prompts])

  const handleValueChange = (varName, value) => {
    setValues(prev => ({
      ...prev,
      [varName]: value
    }))
    // Clear error when user starts typing
    if (errors[varName]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[varName]
        return newErrors
      })
    }
  }

  const handleFileUpload = async (varName, file) => {
    try {
      const text = await file.text()
      handleValueChange(varName, text)
    } catch (error) {
      setErrors(prev => ({
        ...prev,
        [varName]: 'Không thể đọc file'
      }))
    }
  }

  const toggleExpanded = (varName) => {
    setExpandedVars(prev => ({
      ...prev,
      [varName]: !prev[varName]
    }))
  }

  const validateForm = () => {
    const newErrors = {}
    
    allVariables.forEach(varName => {
      if (!values[varName] || values[varName].trim() === '') {
        newErrors[varName] = 'Trường này bắt buộc'
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Count filled variables
  const filledCount = allVariables.filter(v => values[v] && values[v].trim()).length

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    // Convert to array format expected by API
    const variableValues = Object.entries(values).map(([name, value]) => ({
      name,
      value
    }))

    onSubmit?.(variableValues)
  }

  if (Object.keys(prompts).length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p>Chưa có biến nào được phát hiện</p>
        <p className="text-sm mt-2">Upload prompt files để bắt đầu</p>
      </div>
    )
  }

  const promptNames = Object.keys(prompts)

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Progress indicator */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-blue-800 font-medium">
            Đã điền {filledCount}/{allVariables.length} biến
          </span>
          {filledCount === allVariables.length && (
            <span className="flex items-center gap-1 text-green-600">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Hoàn tất
            </span>
          )}
        </div>
      </div>

      {/* Prompt tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-4 overflow-x-auto">
          {promptNames.map((name) => {
            const promptVarCount = prompts[name].variables.length
            const filledVars = prompts[name].variables.filter(v => values[v] && values[v].trim()).length
            const isComplete = filledVars === promptVarCount
            
            return (
              <button
                key={name}
                type="button"
                onClick={() => setSelectedPrompt(name)}
                className={`
                  flex items-center gap-2 py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap transition-colors
                  ${selectedPrompt === name
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span>{name}</span>
                <span className={`
                  text-xs px-2 py-0.5 rounded-full
                  ${isComplete 
                    ? 'bg-green-100 text-green-700' 
                    : filledVars > 0
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-600'
                  }
                `}>
                  {filledVars}/{promptVarCount}
                </span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Variables for selected prompt */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-gray-900">
          {currentPromptVariables.length} biến trong "{selectedPrompt}"
        </h3>

        {currentPromptVariables.map((varName) => {
          const contexts = variableContexts[varName] || []
          const isExpanded = expandedVars[varName]
          const error = errors[varName]

          return (
            <div key={varName} className="border border-gray-200 rounded-lg p-4 space-y-3">
              {/* Variable name */}
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700">
                  {`{{${varName}}}`}
                </label>
                {contexts.length > 0 && (
                  <button
                    type="button"
                    onClick={() => toggleExpanded(varName)}
                    className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    <svg 
                      className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                    {isExpanded ? 'Ẩn' : 'Xem'} context ({contexts.length})
                  </button>
                )}
              </div>

              {/* Context preview */}
              {isExpanded && contexts.length > 0 && (
                <div className="bg-gray-50 rounded p-3 space-y-2">
                  {contexts.map((ctx, idx) => (
                    <div key={idx} className="text-xs">
                      <div className="font-medium text-gray-700 mb-1">
                        Trong prompt: {ctx.prompt}
                      </div>
                      <div className="text-gray-600 font-mono whitespace-pre-wrap">
                        {ctx.context}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Textarea input */}
              <textarea
                value={values[varName] || ''}
                onChange={(e) => handleValueChange(varName, e.target.value)}
                placeholder={`Nhập giá trị cho ${varName}...`}
                rows={4}
                className={`
                  w-full px-3 py-2 border rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                  ${error ? 'border-red-500' : 'border-gray-300'}
                `}
              />

              {/* Error message */}
              {error && (
                <p className="text-sm text-red-600">{error}</p>
              )}

              {/* File upload alternative */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">hoặc</span>
                <label className="text-xs text-primary-600 hover:text-primary-700 cursor-pointer">
                  tải từ file .txt
                  <input
                    type="file"
                    accept=".txt"
                    className="sr-only"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) {
                        handleFileUpload(varName, file)
                      }
                    }}
                  />
                </label>
              </div>
            </div>
          )
        })}
      </div>

      {/* Submit button */}
      <button
        type="submit"
        className="w-full py-2 px-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
      >
        Generate với prompts đã fill
      </button>
    </form>
  )
}
