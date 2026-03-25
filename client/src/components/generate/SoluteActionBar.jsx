import React from 'react'

export default function SoluteActionBar({
  onSolve,
  onExport,
  isGenerating,
  isExporting,
  examPdf,
  generatedExam,
  isDirty
}) {
  // ✅ derive state tại đây (clean hơn)
  const canSolve = !!examPdf?.files?.length
  const canExport = !!generatedExam && !isDirty

  return (
    <div className="flex items-center gap-3">

      {/* Solve button */}
      <button
        onClick={onSolve}
        disabled={!canSolve || isGenerating}
        className="btn-primary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGenerating ? 'Đang giải...' : 'Giải đề'}
      </button>

      {/* Export button */}
      <button
        onClick={onExport}
        disabled={!canExport || isGenerating || isExporting}
        className="btn-secondary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        title={!canExport ? "Vui lòng lưu thay đổi trước khi xuất" : ""}
      >
        {isExporting && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 
              0 0 5.373 0 12h4zm2 5.291A7.962 
              7.962 0 014 12H0c0 3.042 1.135 
              5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {isExporting ? 'Đang xuất...' : 'Xuất DOCX'}
      </button>

    </div>
  )
}