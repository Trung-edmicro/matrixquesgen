import { useState, useRef } from 'react'

export default function MatrixInputPanel({ onMatrixUpload, matrixData, onTemplateUpload, templateDocx }) {
  const [file, setFile] = useState(null)
  const [templateFile, setTemplateFile] = useState(null)
  const fileInputRef = useRef(null)
  const templateInputRef = useRef(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      onMatrixUpload(selectedFile)
    }
  }

  const handleTemplateChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setTemplateFile(selectedFile)
      onTemplateUpload(selectedFile)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Ma trận đề */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-gray-900">Ma trận đề (XLSX):</span>
        
        {file ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 truncate max-w-[200px]" title={file.name}>
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

      {/* Template DOCX (tùy chọn) */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-gray-900">Đề mẫu (DOCX):</span>
        
        {templateFile ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 truncate max-w-[200px]" title={templateFile.name}>
              {templateFile.name}
            </span>
            <span className="text-xs text-gray-400">({(templateFile.size / 1024).toFixed(1)} KB)</span>
          </div>
        ) : (
          <span className="text-sm text-gray-400 italic">Không bắt buộc</span>
        )}
        
        <input
          ref={templateInputRef}
          type="file"
          accept=".docx"
          onChange={handleTemplateChange}
          className="hidden"
        />
        
        <button
          onClick={() => templateInputRef.current?.click()}
          className="btn-secondary text-xs px-3 py-1.5"
        >
          Chọn file
        </button>
      </div>
    </div>
  )
}
