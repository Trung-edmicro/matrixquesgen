import { useState, useCallback } from 'react'

export default function PromptUploader({ onUploadSuccess, onError }) {
  const [files, setFiles] = useState([])
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const validateFiles = (fileList) => {
    const validFiles = []
    const errors = []

    if (fileList.length > 10) {
      errors.push('Chỉ được upload tối đa 10 files')
      return { validFiles: [], errors }
    }

    for (let file of fileList) {
      if (!file.name.endsWith('.txt')) {
        errors.push(`${file.name} không phải file .txt`)
      } else if (validFiles.find(f => f.name === file.name)) {
        errors.push(`${file.name} đã tồn tại`)
      } else {
        validFiles.push(file)
      }
    }

    return { validFiles, errors }
  }

  const handleFileSelect = (e) => {
    const fileList = Array.from(e.target.files)
    const { validFiles, errors } = validateFiles([...files, ...fileList])

    if (errors.length > 0) {
      onError?.(errors.join(', '))
      return
    }

    setFiles(prev => [...prev, ...validFiles])
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)

    const fileList = Array.from(e.dataTransfer.files)
    const { validFiles, errors } = validateFiles([...files, ...fileList])

    if (errors.length > 0) {
      onError?.(errors.join(', '))
      return
    }

    setFiles(prev => [...prev, ...validFiles])
  }, [files, onError])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) {
      onError?.('Chưa có file nào được chọn')
      return
    }

    setIsUploading(true)

    try {
      const formData = new FormData()
      files.forEach(file => {
        formData.append('files', file)
      })

      const response = await fetch('http://localhost:8000/api/prompts/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }

      const data = await response.json()
      onUploadSuccess?.(data)
      setFiles([]) // Clear files after success

    } catch (error) {
      console.error('Upload error:', error)
      onError?.(error.message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div className="mt-4">
          <label htmlFor="file-upload" className="cursor-pointer">
            <span className="text-primary-600 hover:text-primary-700 font-medium">
              Chọn files
            </span>
            <span className="text-gray-600"> hoặc kéo thả vào đây</span>
            <input
              id="file-upload"
              type="file"
              className="sr-only"
              multiple
              accept=".txt"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
          </label>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          File .txt, tối đa 10 files
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">
            Đã chọn {files.length} file(s)
          </h4>
          <div className="space-y-1">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-sm text-gray-700 truncate">{file.name}</span>
                  <span className="text-xs text-gray-500 flex-shrink-0">
                    ({Math.round(file.size / 1024)} KB)
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  disabled={isUploading}
                  className="ml-2 p-1 text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={files.length === 0 || isUploading}
        className="w-full py-2 px-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isUploading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Đang upload...
          </span>
        ) : (
          'Upload prompts'
        )}
      </button>
    </div>
  )
}
