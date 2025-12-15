import { useState, useRef } from 'react'

export default function MatrixInputPanel({ onMatrixUpload, matrixData }) {
  const [file, setFile] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      onMatrixUpload(selectedFile)
    }
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm font-medium text-gray-900">Ma trận đề:</span>
      
      {file ? (
        <div className="flex items-center gap-2 flex-1">
          <span className="text-sm text-gray-600 truncate max-w-md" title={file.name}>
            {file.name}
          </span>
          <span className="text-xs text-gray-400">({(file.size / 1024).toFixed(1)} KB)</span>
        </div>
      ) : (
        <span className="text-sm text-gray-400 italic">Chưa chọn file</span>
      )}
      
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx"
        onChange={handleFileChange}
        className="hidden"
      />
      
      <button
        onClick={() => fileInputRef.current?.click()}
        className="btn-secondary text-xs px-3 py-1.5"
      >
        Chọn file
      </button>
    </div>
  )
}
