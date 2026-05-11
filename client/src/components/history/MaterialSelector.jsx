import { useState, useEffect } from 'react'

const MATERIALS_PER_PAGE = 3

export default function MaterialSelector({ sessionId, enrichedMatrix, onComplete, onSkip }) {
  const [selections, setSelections] = useState({})
  const [initialized, setInitialized] = useState(false)
  const [expandedQuestions, setExpandedQuestions] = useState({})
  const [customMaterials, setCustomMaterials] = useState({})
  const [materialPages, setMaterialPages] = useState({})
  const [validationErrors, setValidationErrors] = useState([])

  useEffect(() => {
    if (!enrichedMatrix?.lessons) return

    const initial = {}
    enrichedMatrix.lessons.forEach((lesson, lessonIndex) => {
      const dsQuestions = lesson.DS || []
      dsQuestions.forEach((q, qIndex) => {
        const materials = q.materials
        if (!Array.isArray(materials) || materials.length === 0) return

        const code = q.question_code || `DS_${lessonIndex}_${qIndex}`
        const key = `${lessonIndex}-DS-${qIndex}-${code}`
        initial[key] = {
          lesson_index: lessonIndex,
          question_index: qIndex,
          question_code: code,
          selected_material: null,
          is_custom: false,
          is_random: false,
          materials_list: materials
        }
      })
    })

    setSelections(initial)
    setInitialized(true)

    if (Object.keys(initial).length === 0) {
      onComplete([])
    }
  // onComplete intentionally excluded to avoid stale closure re-runs
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enrichedMatrix])

  const totalQuestions = Object.keys(selections).length
  const selectedCount = Object.values(selections).filter(s => s.selected_material !== null).length

  const handleSelect = (key, material, isCustom = false) => {
    setSelections(prev => ({
      ...prev,
      [key]: { ...prev[key], selected_material: material, is_custom: isCustom, is_random: false }
    }))
    setValidationErrors(prev => prev.filter(e => e !== key))
  }

  const handleRandomSelect = (key) => {
    const sel = selections[key]
    if (!sel) return
    const list = sel.materials_list
    const random = list[Math.floor(Math.random() * list.length)]
    setSelections(prev => ({
      ...prev,
      [key]: { ...prev[key], selected_material: random, is_custom: false, is_random: true }
    }))
    setValidationErrors(prev => prev.filter(e => e !== key))
  }

  const handleCustomMaterialChange = (key, value) => {
    setCustomMaterials(prev => ({ ...prev, [key]: value }))
  }

  const handleCustomMaterialApply = (key) => {
    const value = customMaterials[key]
    if (!value || !value.trim()) return
    handleSelect(key, value.trim(), true)
    setCustomMaterials(prev => ({ ...prev, [key]: '' }))
  }

  const toggleExpanded = (key) => {
    setExpandedQuestions(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const getCurrentPage = (key) => materialPages[key] || 0

  const goToNextPage = (key, maxPage) => {
    const cur = getCurrentPage(key)
    if (cur < maxPage) setMaterialPages(prev => ({ ...prev, [key]: cur + 1 }))
  }

  const goToPreviousPage = (key) => {
    const cur = getCurrentPage(key)
    if (cur > 0) setMaterialPages(prev => ({ ...prev, [key]: cur - 1 }))
  }

  const validateSelections = () => {
    const errors = Object.keys(selections).filter(key => selections[key].selected_material === null)
    setValidationErrors(errors)
    return errors.length === 0
  }

  const buildSelectionsArray = (sels) =>
    Object.values(sels).map(s => ({
      lesson_index: s.lesson_index,
      question_index: s.question_index,
      question_code: s.question_code,
      selected_material: s.selected_material
    }))

  const handleSubmit = () => {
    if (!validateSelections()) return
    onComplete(buildSelectionsArray(selections))
  }

  const handleSkipAll = () => {
    const newSelections = { ...selections }
    Object.keys(newSelections).forEach(key => {
      if (newSelections[key].selected_material === null) {
        const list = newSelections[key].materials_list
        newSelections[key] = { ...newSelections[key], selected_material: list[0] || null, is_random: true, is_custom: false }
      }
    })
    setSelections(newSelections)
    setTimeout(() => onComplete(buildSelectionsArray(newSelections)), 300)
  }

  if (!enrichedMatrix?.lessons || !initialized) {
    return (
      <div className="p-8 text-center text-gray-500">Đang tải dữ liệu tư liệu...</div>
    )
  }

  if (totalQuestions === 0) {
    return null
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col relative">

        {/* Close button */}
        <button
          onClick={onSkip}
          className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors z-10"
          title="Đóng"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Chọn tư liệu cho câu hỏi Đúng/Sai</h2>
          <p className="text-sm text-gray-500 mt-1">
            AI đã lọc sẵn các tư liệu phù hợp. Vui lòng chọn 1 tư liệu cho mỗi câu hỏi, hoặc tự nhập.
          </p>

          {/* Progress bar */}
          <div className="flex items-center gap-4 mt-3">
            <div className="text-sm text-gray-700">
              <span className="font-medium">{selectedCount}</span> / {totalQuestions} câu đã chọn
            </div>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-amber-500 h-2 rounded-full transition-all duration-300"
                style={{ width: totalQuestions > 0 ? `${(selectedCount / totalQuestions) * 100}%` : '0%' }}
              />
            </div>
          </div>

          {validationErrors.length > 0 && (
            <div className="mt-2 text-sm text-red-600 font-medium">
              Vui lòng chọn tư liệu cho {validationErrors.length} câu hỏi còn lại
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {enrichedMatrix.lessons.map((lesson, lessonIndex) => {
              const dsQuestions = (lesson.DS || []).filter(
                q => Array.isArray(q.materials) && q.materials.length > 0
              )
              if (dsQuestions.length === 0) return null

              return (
                <div key={lessonIndex} className="border border-gray-300 rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 text-sm font-medium text-gray-700 border-b border-gray-200">
                    {lesson.lesson_name || `Bài ${lesson.lesson_number || lessonIndex + 1}`}
                  </div>

                  <div className="divide-y divide-gray-100">
                    {dsQuestions.map((q, qIndex) => {
                      const code = q.question_code || `DS_${lessonIndex}_${qIndex}`
                      const key = `${lessonIndex}-DS-${qIndex}-${code}`
                      const sel = selections[key]
                      if (!sel) return null

                      return (
                        <MaterialSelectorItem
                          key={key}
                          questionKey={key}
                          question={q}
                          questionCode={code}
                          selection={sel}
                          isExpanded={!!expandedQuestions[key]}
                          hasError={validationErrors.includes(key)}
                          customMaterial={customMaterials[key] || ''}
                          currentPage={getCurrentPage(key)}
                          onSelect={handleSelect}
                          onRandomSelect={handleRandomSelect}
                          onToggleExpand={toggleExpanded}
                          onCustomMaterialChange={handleCustomMaterialChange}
                          onCustomMaterialApply={handleCustomMaterialApply}
                          onNextPage={goToNextPage}
                          onPreviousPage={goToPreviousPage}
                        />
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
          <button
            onClick={handleSkipAll}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Bỏ qua (Tự động chọn tư liệu đầu tiên)
          </button>
          <button
            onClick={handleSubmit}
            disabled={selectedCount === 0}
            className="px-6 py-2 text-sm font-medium text-white bg-amber-500 rounded hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Xác nhận và tiếp tục sinh đề ({selectedCount}/{totalQuestions})
          </button>
        </div>
      </div>
    </div>
  )
}

function MaterialSelectorItem({
  questionKey,
  question,
  questionCode,
  selection,
  isExpanded,
  hasError,
  customMaterial,
  currentPage = 0,
  onSelect,
  onRandomSelect,
  onToggleExpand,
  onCustomMaterialChange,
  onCustomMaterialApply,
  onNextPage,
  onPreviousPage
}) {
  const materials = selection.materials_list || []
  const totalPages = Math.ceil(materials.length / MATERIALS_PER_PAGE)
  const startIdx = currentPage * MATERIALS_PER_PAGE
  const visibleMaterials = materials.slice(startIdx, startIdx + MATERIALS_PER_PAGE)

  return (
    <div className={`p-4 ${hasError ? 'bg-red-50' : 'bg-white'}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium">Mã câu: {questionCode || 'N/A'}</span>
            <span className="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-medium">
              {materials.length} tư liệu
            </span>
            {hasError && (
              <span className="text-xs text-red-600 font-medium">Chưa chọn</span>
            )}
          </div>

          {/* Selected indicator */}
          {selection.selected_material && (
            <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded">
              <div className="text-xs text-green-700 font-medium mb-1 flex items-center gap-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Đã chọn {selection.is_custom ? '(Tự nhập)' : selection.is_random ? '(Ngẫu nhiên)' : ''}
              </div>
              <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                {selection.selected_material}
              </div>
            </div>
          )}

          {/* Statements preview when nothing selected yet */}
          {!selection.selected_material && question.statements && question.statements.length > 0 && (
            <div className="text-xs text-gray-500 mt-1">
              {question.statements.slice(0, 2).map((s, i) => (
                <span key={i} className="mr-3">
                  {s.label}: {s.learning_outcome?.slice(0, 60)}{s.learning_outcome?.length > 60 ? '...' : ''}
                </span>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={() => onToggleExpand(questionKey)}
          className="px-3 py-1 text-sm text-amber-600 hover:text-amber-800 font-medium whitespace-nowrap"
        >
          {isExpanded ? 'Thu gọn' : 'Chọn tư liệu'}
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          {/* Material radio list with pagination */}
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-600">
                {totalPages > 1
                  ? `Trang ${currentPage + 1} / ${totalPages} (${materials.length} tư liệu)`
                  : `${materials.length} tư liệu`}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2">
              {visibleMaterials.map((material, idx) => (
                <label
                  key={startIdx + idx}
                  className={`flex items-start gap-3 p-3 border rounded cursor-pointer transition-colors ${
                    selection.selected_material === material && !selection.is_custom
                      ? 'border-amber-400 bg-amber-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="radio"
                    name={questionKey}
                    checked={selection.selected_material === material && !selection.is_custom}
                    onChange={() => onSelect(questionKey, material, false)}
                    className="mt-1 flex-shrink-0 accent-amber-500"
                  />
                  <span className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                    {material}
                  </span>
                </label>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between gap-2 mt-3 pt-2 border-t border-gray-200">
                <button
                  onClick={() => onPreviousPage(questionKey)}
                  disabled={currentPage === 0}
                  className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ← Trang trước
                </button>
                <span className="text-xs text-gray-600">
                  {startIdx + 1} – {Math.min(startIdx + MATERIALS_PER_PAGE, materials.length)} / {materials.length}
                </span>
                <button
                  onClick={() => onNextPage(questionKey, totalPages - 1)}
                  disabled={currentPage >= totalPages - 1}
                  className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Trang sau →
                </button>
              </div>
            )}
          </div>

          {/* Custom text input */}
          <div className="border border-gray-300 rounded p-3 bg-gray-50">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hoặc nhập tư liệu khác:
            </label>
            <textarea
              value={customMaterial}
              onChange={(e) => onCustomMaterialChange(questionKey, e.target.value)}
              placeholder="Nhập tư liệu của bạn..."
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <button
              onClick={() => onCustomMaterialApply(questionKey)}
              disabled={!customMaterial || !customMaterial.trim()}
              className="mt-2 px-4 py-1.5 text-sm font-medium text-white bg-amber-500 rounded hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Áp dụng tư liệu tự nhập
            </button>
          </div>

          {/* Random button */}
          <button
            onClick={() => onRandomSelect(questionKey)}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Chọn ngẫu nhiên
          </button>
        </div>
      )}
    </div>
  )
}
