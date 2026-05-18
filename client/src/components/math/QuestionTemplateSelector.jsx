import { useState, useEffect } from 'react'
import LaTeXRenderer from '../common/LaTeXRenderer'

const TEMPLATES_PER_PAGE = 5

export default function QuestionTemplateSelector({ sessionId, enrichedMatrix, onComplete, onSkip }) {
  const [selections, setSelections] = useState({})
  const [expandedQuestions, setExpandedQuestions] = useState({})
  const [customTemplates, setCustomTemplates] = useState({})
  const [validationErrors, setValidationErrors] = useState([])
  const [templatePages, setTemplatePages] = useState({}) // Track current page per question
  const [selectedQuestionType, setSelectedQuestionType] = useState('TN') // Track selected question type tab

  // Initialize selections from enriched matrix
  useEffect(() => {
    if (!enrichedMatrix || !enrichedMatrix.lessons) return

    const initialSelections = {}
    enrichedMatrix.lessons.forEach((lesson, lessonIndex) => {
      // Helper function to process questions with multiple codes
      const processQuestions = (questionsArray, questionType, level, useQuestionCode = false) => {
        questionsArray.forEach((q, qIndex) => {
          // Extract codes - DS uses question_code, others use code
          let codes
          if (useQuestionCode) {
            // DS: use question_code (single value)
            codes = [q.question_code || 'unknown']
          } else {
            // TN/TLN/TL: use code (can be array or single value)
            codes = Array.isArray(q.code) ? q.code : [q.code || 'unknown']
          }
          
          // Create selection for each code
          codes.forEach(code => {
            const key = `${lessonIndex}-${questionType}-${level ? level + '-' : ''}${qIndex}-${code}`
            const hasTemplates = q.question_template && q.question_template.length > 0
            
            initialSelections[key] = {
              lesson_index: lessonIndex,
              question_type: questionType,
              level: level || null,
              question_index: qIndex,
              question_code: code,  // Track which code this selection is for
              selected_template: [],
              is_custom: false,
              is_random: false,
              has_templates: hasTemplates
            }
          })
        })
      }

      // Process TN questions
      if (lesson.TN) {
        ['NB', 'TH', 'VD'].forEach(level => {
          const questions = lesson.TN[level] || []
          processQuestions(questions, 'TN', level, false)
        })
      }

      // Process DS questions
      if (lesson.DS && Array.isArray(lesson.DS)) {
        processQuestions(lesson.DS, 'DS', null, true)
      }

      // Process TLN questions
      if (lesson.TLN) {
        ['NB', 'TH', 'VD'].forEach(level => {
          const questions = lesson.TLN[level] || []
          processQuestions(questions, 'TLN', level)
        })
      }

      // Process TL questions
      if (lesson.TL) {
        ['NB', 'TH', 'VD'].forEach(level => {
          const questions = lesson.TL[level] || []
          processQuestions(questions, 'TL', level)
        })
      }
    })

    setSelections(initialSelections)
  }, [enrichedMatrix])

  const handleTemplateSelect = (key, template, isCustom = false) => {
    setSelections(prev => {
      const current = prev[key]
      const currentTemplates = Array.isArray(current.selected_template) ? current.selected_template : []
      let newTemplates
      if (currentTemplates.includes(template)) {
        newTemplates = currentTemplates.filter(t => t !== template)
      } else {
        newTemplates = [...currentTemplates, template]
      }
      return {
        ...prev,
        [key]: {
          ...current,
          selected_template: newTemplates,
          is_custom: isCustom,
          is_random: false
        }
      }
    })
    setValidationErrors(prev => prev.filter(e => e !== key))
  }

  const handleRandomSelect = (key) => {
    const selection = selections[key]
    if (!selection) return

    const lesson = enrichedMatrix.lessons[selection.lesson_index]
    let question
    
    if (selection.question_type === 'DS') {
      question = lesson.DS[selection.question_index]
    } else if (selection.level) {
      question = lesson[selection.question_type][selection.level][selection.question_index]
    }

    if (question && question.question_template && question.question_template.length > 0) {
      const randomTemplate = question.question_template[
        Math.floor(Math.random() * question.question_template.length)
      ]
      
      setSelections(prev => ({
        ...prev,
        [key]: {
          ...prev[key],
          selected_template: [randomTemplate],
          is_custom: false,
          is_random: true
        }
      }))
      setValidationErrors(prev => prev.filter(e => e !== key))
    }
  }

  const handleCustomTemplateChange = (key, value) => {
    setCustomTemplates(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const handleCustomTemplateApply = (key) => {
    const customValue = customTemplates[key]
    if (customValue && customValue.trim()) {
      setSelections(prev => {
        const current = prev[key]
        const currentTemplates = Array.isArray(current.selected_template) ? current.selected_template : []
        return {
          ...prev,
          [key]: {
            ...current,
            selected_template: [...currentTemplates, customValue.trim()],
            is_custom: true,
            is_random: false
          }
        }
      })
      setValidationErrors(prev => prev.filter(e => e !== key))
      setCustomTemplates(prev => ({ ...prev, [key]: '' }))
    }
  }

  const handleClearTemplate = (key) => {
    setSelections(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        selected_template: [],
        is_custom: false,
        is_random: false
      }
    }))
  }

  const getCurrentPage = (key) => {
    return templatePages[key] || 0
  }

  const goToNextPage = (key, maxPage) => {
    const currentPage = getCurrentPage(key)
    if (currentPage < maxPage) {
      setTemplatePages(prev => ({
        ...prev,
        [key]: currentPage + 1
      }))
    }
  }

  const goToPreviousPage = (key) => {
    const currentPage = getCurrentPage(key)
    if (currentPage > 0) {
      setTemplatePages(prev => ({
        ...prev,
        [key]: currentPage - 1
      }))
    }
  }

  const toggleExpanded = (key) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const validateSelections = () => {
    const errors = []
    Object.keys(selections).forEach(key => {
      const selection = selections[key]
      // Only require template if question originally had templates
      if (selection.has_templates && (!selection.selected_template || selection.selected_template.length === 0)) {
        errors.push(key)
      }
    })
    setValidationErrors(errors)
    return errors.length === 0
  }

  const handleSubmit = () => {
    if (!validateSelections()) {
      alert('Vui lòng chọn câu hỏi mẫu cho các câu hỏi có mẫu hoặc chọn "Bỏ qua" để hệ thống tự chọn ngẫu nhiên')
      return
    }

    // Convert selections to array and filter out has_templates field
    // Keep all selections including those with null selected_template
    const selectionsArray = Object.values(selections).map(selection => ({
      lesson_index: selection.lesson_index,
      question_type: selection.question_type,
      level: selection.level,
      question_index: selection.question_index,
      question_code: selection.question_code,
      selected_template: selection.selected_template,
      is_custom: selection.is_custom,
      is_random: selection.is_random
    }))
    
    onComplete(selectionsArray)
  }

  const handleSkipAll = () => {
    // Auto-select random templates for all questions
    const newSelections = { ...selections }
    
    Object.keys(newSelections).forEach(key => {
      if (!newSelections[key].selected_template || newSelections[key].selected_template.length === 0) {
        const selection = newSelections[key]
        const lesson = enrichedMatrix.lessons[selection.lesson_index]
        let question
        
        if (selection.question_type === 'DS') {
          question = lesson.DS[selection.question_index]
        } else if (selection.level) {
          question = lesson[selection.question_type][selection.level][selection.question_index]
        }

        if (question && question.question_template && question.question_template.length > 0) {
          const randomTemplate = question.question_template[
            Math.floor(Math.random() * question.question_template.length)
          ]
          newSelections[key].selected_template = [randomTemplate]
          newSelections[key].is_random = true
        }
      }
    })

    setSelections(newSelections)
    setTimeout(() => {
      // Filter out has_templates field before sending
      // Keep all selections including those with null selected_template
      const selectionsArray = Object.values(newSelections).map(selection => ({
        lesson_index: selection.lesson_index,
        question_type: selection.question_type,
        level: selection.level,
        question_index: selection.question_index,
        question_code: selection.question_code,
        selected_template: selection.selected_template,
        is_custom: selection.is_custom,
        is_random: selection.is_random
      }))
      onComplete(selectionsArray)
    }, 500)
  }

  if (!enrichedMatrix || !enrichedMatrix.lessons) {
    return (
      <div className="p-8 text-center text-gray-500">
        Đang tải dữ liệu câu hỏi mẫu...
      </div>
    )
  }

  // Count questions by type
  const questionCountByType = {
    TN: Object.keys(selections).filter(k => selections[k].question_type === 'TN').length,
    DS: Object.keys(selections).filter(k => selections[k].question_type === 'DS').length,
    TLN: Object.keys(selections).filter(k => selections[k].question_type === 'TLN').length,
    TL: Object.keys(selections).filter(k => selections[k].question_type === 'TL').length
  }

  const questionCountByTypeSelected = {
    TN: Object.values(selections).filter(s => s.question_type === 'TN' && s.selected_template && s.selected_template.length > 0).length,
    DS: Object.values(selections).filter(s => s.question_type === 'DS' && s.selected_template && s.selected_template.length > 0).length,
    TLN: Object.values(selections).filter(s => s.question_type === 'TLN' && s.selected_template && s.selected_template.length > 0).length,
    TL: Object.values(selections).filter(s => s.question_type === 'TL' && s.selected_template && s.selected_template.length > 0).length
  }

  const totalQuestions = Object.keys(selections).length
  const selectedCount = Object.values(selections).filter(s => s.selected_template && s.selected_template.length > 0).length

  // Get available question types (only types with questions needing templates)
  const availableQuestionTypes = [
    { type: 'TN', label: 'Trắc nghiệm (TN)' },
    { type: 'DS', label: 'Đúng/Sai (DS)' },
    { type: 'TLN', label: 'Trả lời ngắn (TLN)' },
    { type: 'TL', label: 'Tự luận (TL)' }
  ].filter(tab => questionCountByType[tab.type] > 0)

  // Set initial selected type to first available type
  useEffect(() => {
    if (availableQuestionTypes.length > 0 && !availableQuestionTypes.find(t => t.type === selectedQuestionType)) {
      setSelectedQuestionType(availableQuestionTypes[0].type)
    }
  }, [availableQuestionTypes, selectedQuestionType])

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] flex flex-col relative">
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
          <h2 className="text-xl font-semibold text-gray-900">Chọn câu hỏi mẫu cho môn Toán</h2>
          <div className="flex items-center gap-4 mt-3">
            <div className="text-sm text-gray-700">
              <span className="font-medium">{selectedCount}</span> / {totalQuestions} câu đã chọn
            </div>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(selectedCount / totalQuestions) * 100}%` }}
              />
            </div>
          </div>

          {/* Question Type Tabs */}
          <div className="flex gap-2 mt-4 border-b border-gray-200">
            {availableQuestionTypes.map(tab => (
              <button
                key={tab.type}
                onClick={() => setSelectedQuestionType(tab.type)}
                className={`px-4 py-2 text-sm font-medium whitespace-nowrap ${
                  selectedQuestionType === tab.type
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
                <span className="ml-2 text-xs text-gray-500">
                  ({questionCountByTypeSelected[tab.type]}/{questionCountByType[tab.type]})
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {enrichedMatrix.lessons.map((lesson, lessonIndex) => {
              // Filter questions by selected type
              const hasQuestionsOfSelectedType = selectedQuestionType === 'TN'
                ? (lesson.TN && Object.values(lesson.TN).some(level => level && level.length > 0))
                : selectedQuestionType === 'DS'
                ? (lesson.DS && lesson.DS.length > 0)
                : selectedQuestionType === 'TLN'
                ? (lesson.TLN && Object.values(lesson.TLN).some(level => level && level.length > 0))
                : (lesson.TL && Object.values(lesson.TL).some(level => level && level.length > 0))

              if (!hasQuestionsOfSelectedType) return null

              return (
              <div key={lessonIndex} className="border border-gray-300 rounded-lg overflow-hidden">
                {/* <div className="bg-gray-50 px-4 py-2 font-medium text-gray-900">
                  Chương {lesson.chapter_number} - Bài {lesson.lesson_number}
                </div> */}
                
                <div className="divide-y divide-gray-200">
                  {/* Render TN questions */}
                  {selectedQuestionType === 'TN' && lesson.TN && ['NB', 'TH', 'VD'].map(level => {
                    const questions = lesson.TN[level] || []
                    return questions.flatMap((q, qIndex) => {
                      // Handle multiple codes in one question
                      const codes = Array.isArray(q.code) ? q.code : [q.code || 'unknown']
                      return codes.map(code => {
                        const key = `${lessonIndex}-TN-${level}-${qIndex}-${code}`
                        const selection = selections[key]
                        if (!selection) return null  // Skip if not in selections
                        const isExpanded = expandedQuestions[key]
                        const hasError = validationErrors.includes(key)

                        return (
                          <QuestionTemplateItem
                            key={key}
                            questionKey={key}
                            questionType="TN"
                            level={level}
                            question={q}
                            questionCode={code}
                            selection={selection}
                            isExpanded={isExpanded}
                            hasError={hasError}
                            customTemplate={customTemplates[key] || ''}
                            currentPage={getCurrentPage(key)}
                            onTemplateSelect={handleTemplateSelect}
                            onRandomSelect={handleRandomSelect}
                            onToggleExpand={toggleExpanded}
                            onCustomTemplateChange={handleCustomTemplateChange}
                            onCustomTemplateApply={handleCustomTemplateApply}
                            onClearTemplate={handleClearTemplate}
                            onNextPage={goToNextPage}
                            onPreviousPage={goToPreviousPage}
                          />
                        )
                      })
                    })
                  })}

                  {/* Render DS questions */}
                  {selectedQuestionType === 'DS' && lesson.DS && lesson.DS.flatMap((q, qIndex) => {
                    // DS uses question_code (single value)
                    const code = q.question_code || 'unknown'
                    const key = `${lessonIndex}-DS-${qIndex}-${code}`
                    const selection = selections[key]
                    if (!selection) return null  // Skip if not in selections
                    const isExpanded = expandedQuestions[key]
                    const hasError = validationErrors.includes(key)

                    return (
                      <QuestionTemplateItem
                        key={key}
                        questionKey={key}
                        questionType="DS"
                        level={null}
                        question={q}
                        questionCode={code}
                        selection={selection}
                        isExpanded={isExpanded}
                        hasError={hasError}
                        customTemplate={customTemplates[key] || ''}
                        currentPage={getCurrentPage(key)}
                        onTemplateSelect={handleTemplateSelect}
                        onRandomSelect={handleRandomSelect}
                        onToggleExpand={toggleExpanded}
                        onCustomTemplateChange={handleCustomTemplateChange}
                        onCustomTemplateApply={handleCustomTemplateApply}
                        onClearTemplate={handleClearTemplate}
                        onNextPage={goToNextPage}
                        onPreviousPage={goToPreviousPage}
                      />
                    )
                  })}

                  {/* Render TLN questions */}
                  {selectedQuestionType === 'TLN' && lesson.TLN && ['NB', 'TH', 'VD'].map(level => {
                    const questions = lesson.TLN[level] || []
                    return questions.flatMap((q, qIndex) => {
                      // Handle multiple codes in one question
                      const codes = Array.isArray(q.code) ? q.code : [q.code || 'unknown']
                      return codes.map(code => {
                        const key = `${lessonIndex}-TLN-${level}-${qIndex}-${code}`
                        const selection = selections[key]
                        if (!selection) return null  // Skip if not in selections
                        const isExpanded = expandedQuestions[key]
                        const hasError = validationErrors.includes(key)

                        return (
                          <QuestionTemplateItem
                            key={key}
                            questionKey={key}
                            questionType="TLN"
                            level={level}
                            question={q}
                            questionCode={code}
                            selection={selection}
                            isExpanded={isExpanded}
                            hasError={hasError}
                            customTemplate={customTemplates[key] || ''}
                            currentPage={getCurrentPage(key)}
                            onTemplateSelect={handleTemplateSelect}
                            onRandomSelect={handleRandomSelect}
                            onToggleExpand={toggleExpanded}
                            onCustomTemplateChange={handleCustomTemplateChange}
                            onCustomTemplateApply={handleCustomTemplateApply}
                            onClearTemplate={handleClearTemplate}
                            onNextPage={goToNextPage}
                            onPreviousPage={goToPreviousPage}
                          />
                        )
                      })
                    })
                  })}

                  {/* Render TL questions */}
                  {selectedQuestionType === 'TL' && lesson.TL && ['NB', 'TH', 'VD'].map(level => {
                    const questions = lesson.TL[level] || []
                    return questions.flatMap((q, qIndex) => {
                      // Handle multiple codes in one question
                      const codes = Array.isArray(q.code) ? q.code : [q.code || 'unknown']
                      return codes.map(code => {
                        const key = `${lessonIndex}-TL-${level}-${qIndex}-${code}`
                        const selection = selections[key]
                        if (!selection) return null  // Skip if not in selections
                        const isExpanded = expandedQuestions[key]
                        const hasError = validationErrors.includes(key)

                        return (
                          <QuestionTemplateItem
                            key={key}
                            questionKey={key}
                            questionType="TL"
                            level={level}
                            question={q}
                            questionCode={code}
                            selection={selection}
                            isExpanded={isExpanded}
                            hasError={hasError}
                            customTemplate={customTemplates[key] || ''}
                            currentPage={getCurrentPage(key)}
                            onTemplateSelect={handleTemplateSelect}
                            onRandomSelect={handleRandomSelect}
                            onToggleExpand={toggleExpanded}
                            onCustomTemplateChange={handleCustomTemplateChange}
                            onCustomTemplateApply={handleCustomTemplateApply}
                            onClearTemplate={handleClearTemplate}
                            onNextPage={goToNextPage}
                            onPreviousPage={goToPreviousPage}
                          />
                        )
                      })
                    })
                  })}
                </div>
              </div>
              )}
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
          <button
            onClick={handleSkipAll}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Bỏ qua (Chọn ngẫu nhiên tất cả)
          </button>
          <button
            onClick={handleSubmit}
            disabled={selectedCount === 0}
            className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Xác nhận và tiếp tục sinh đề ({selectedCount}/{totalQuestions})
          </button>
        </div>
      </div>
    </div>
  )
}

// Sub-component for individual question template item
function QuestionTemplateItem({
  questionKey,
  questionType,
  level,
  question,
  questionCode,
  selection,
  isExpanded,
  hasError,
  customTemplate,
  currentPage = 0,
  onTemplateSelect,
  onRandomSelect,
  onToggleExpand,
  onCustomTemplateChange,
  onCustomTemplateApply,
  onClearTemplate,
  onNextPage,
  onPreviousPage
}) {
  const levelNames = { NB: { code: 'NB', color: 'bg-green-100 text-green-800' }, TH: { code: 'TH', color: 'bg-blue-100 text-blue-800' }, VD: { code: 'VD', color: 'bg-yellow-100 text-yellow-800' } }
  
  // Check if question has templates or not
  const hasTemplates = question.question_template && question.question_template.length > 0

  return (
    <div className={`p-4 ${hasError ? 'bg-red-50' : 'bg-white'}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium">Mã câu: {questionCode || 'N/A'}</span>
            {level && (
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${levelNames[level].color}`}>
                {levelNames[level].code}
              </span>
            )}
            {hasError && (
              <span className="text-xs text-red-600 font-medium">Chưa chọn</span>
            )}
          </div>
          {selection && Array.isArray(selection.selected_template) && selection.selected_template.length > 0 && (
            <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded">
              <div className="text-xs text-green-700 font-medium mb-1 flex items-center gap-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Đã chọn {selection.selected_template.length} mẫu {selection.is_custom ? '(Tự nhập)' : selection.is_random ? '(Ngẫu nhiên)' : ''}
              </div>
              <div className="space-y-2">
                {selection.selected_template.map((t, i) => (
                  <div key={i} className={`text-sm text-gray-800 whitespace-pre-wrap ${i > 0 ? 'border-t border-green-100 pt-2' : ''}`}>
                    <LaTeXRenderer>{t}</LaTeXRenderer>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <button
          onClick={() => onToggleExpand(questionKey)}
          className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          {isExpanded ? 'Thu gọn' : 'Chọn mẫu'}
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          {/* If no templates available and none selected yet: show text input */}
          {!hasTemplates && !(selection && selection.selected_template && selection.selected_template.length > 0) && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-blue-900 mb-2">
                    Không có câu hỏi mẫu cho câu hỏi này
                  </h4>
                  <div className="space-y-2">
                    <textarea
                      value={customTemplate}
                      onChange={(e) => onCustomTemplateChange(questionKey, e.target.value)}
                      placeholder="Nhập câu hỏi mẫu của bạn (tùy chọn)..."
                      rows="3"
                      autoFocus
                      className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    />
                    <button
                      onClick={() => onCustomTemplateApply(questionKey)}
                      disabled={!customTemplate || !customTemplate.trim()}
                      className="w-full px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Áp dụng câu mẫu
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* If no templates and custom template was applied: show edit button */}
          {!hasTemplates && selection && selection.selected_template && selection.selected_template.length > 0 && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <button
                onClick={() => onClearTemplate(questionKey)}
                className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 font-medium border border-blue-300 rounded hover:bg-blue-50"
              >
                Sửa câu mẫu
              </button>
            </div>
          )}

          {/* If templates available: show selector with pagination */}
          {hasTemplates && (
            <>
          {/* Template options with pagination */}
          {(() => {
            const templates = question.question_template || []
            const totalPages = Math.ceil(templates.length / TEMPLATES_PER_PAGE)
            const startIdx = currentPage * TEMPLATES_PER_PAGE
            const endIdx = startIdx + TEMPLATES_PER_PAGE
            const visibleTemplates = templates.slice(startIdx, endIdx)

            return (
              <>
                <div className="space-y-2">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-gray-600">
                      Trang {currentPage + 1} / {totalPages} ({templates.length} mẫu)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-2">
                    {visibleTemplates.map((template, idx) => (
                      <label
                        key={startIdx + idx}
                        className="flex items-start gap-3 p-3 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selection && Array.isArray(selection.selected_template) && selection.selected_template.includes(template) && !selection.is_custom}
                          onChange={() => onTemplateSelect(questionKey, template, false)}
                          className="mt-1 flex-shrink-0 accent-blue-600"
                        />
                        <span className="text-sm text-gray-700 flex-1">
                          <LaTeXRenderer>{template}</LaTeXRenderer>
                        </span>
                      </label>
                    ))}
                  </div>

                  {/* Pagination controls */}
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
                        {startIdx + 1} - {Math.min(endIdx, templates.length)} / {templates.length}
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
              </>
            )
          })()}

          {/* Custom template input */}
          <div className="border border-gray-300 rounded p-3 bg-gray-50">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hoặc nhập câu hỏi mẫu khác:
            </label>
            <textarea
              value={customTemplate}
              onChange={(e) => onCustomTemplateChange(questionKey, e.target.value)}
              placeholder="Nhập câu hỏi mẫu của bạn..."
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={() => onCustomTemplateApply(questionKey)}
              disabled={!customTemplate || !customTemplate.trim()}
              className="mt-2 px-4 py-1.5 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Áp dụng câu tự nhập
            </button>
          </div>

          {/* Random button */}
          <button
            onClick={() => onRandomSelect(questionKey)}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Chọn ngẫu nhiên
          </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
