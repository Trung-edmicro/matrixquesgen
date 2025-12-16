export default function ActionBar({ 
  onGenerate, 
  onExport, 
  isGenerating, 
  canGenerate, 
  canExport 
}) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onGenerate}
        disabled={!canGenerate || isGenerating}
        className="btn-primary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGenerating ? 'Đang sinh...' : 'Sinh đề'}
      </button>

      <button
        onClick={onExport}
        disabled={!canExport || isGenerating}
        className="btn-secondary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
        title={!canExport && "Vui lòng lưu thay đổi trước khi xuất"}
      >
        Xuất DOCX
      </button>
    </div>
  )
}
