import { useState, useRef } from 'react'

export default function MatrixInputPanel({ onMatrixUpload, matrixData, onTemplateUpload, templateDocx, onPdfUpload, pdfFiles }) {
  const [file, setFile] = useState(null)
  const [templateFile, setTemplateFile] = useState(null)
  const [pdfs, setPdfs] = useState([])
  const fileInputRef = useRef(null)
  const templateInputRef = useRef(null)
  const pdfInputRef = useRef(null)

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

  const handlePdfChange = (e) => {
    const selectedFiles = Array.from(e.target.files)
    if (selectedFiles.length > 0) {
      setPdfs(selectedFiles)
      onPdfUpload(selectedFiles)
    }
  }

  const removePdf = (index) => {
    const newPdfs = pdfs.filter((_, i) => i !== index)
    setPdfs(newPdfs)
    onPdfUpload(newPdfs)
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
      {/* <div className="flex items-center gap-3">
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
      </div> */}

      {/* PDFs (tùy chọn) */}
      {/* <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-900">Tài liệu PDF:</span>
          
          {pdfs.length > 0 ? (
            <span className="text-sm text-gray-600">{pdfs.length} file</span>
          ) : (
            <span className="text-sm text-gray-400 italic">Không bắt buộc</span>
          )}
          
          <input
            ref={pdfInputRef}
            type="file"
            accept=".pdf"
            multiple
            onChange={handlePdfChange}
            className="hidden"
          />
          
          <button
            onClick={() => pdfInputRef.current?.click()}
            className="btn-secondary text-xs px-3 py-1.5"
          >
            Chọn PDFs
          </button>
        </div>

        {pdfs.length > 0 && (
          <div className="ml-[140px] flex flex-wrap gap-2">
            {pdfs.map((pdf, index) => (
              <div key={index} className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded px-2 py-1">
                <svg className="w-3.5 h-3.5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                </svg>
                <span className="text-xs text-gray-700 truncate max-w-[150px]" title={pdf.name}>
                  {pdf.name}
                </span>
                <span className="text-xs text-gray-400">({(pdf.size / 1024).toFixed(0)}KB)</span>
                <button
                  onClick={() => removePdf(index)}
                  className="ml-1 text-gray-400 hover:text-red-600"
                  title="Xóa"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div> */}
    </div>
  )
}
