import { useState, useEffect } from 'react'

export default function QuestionTemplateSelector({ sessionId, enrichedMatrix, onComplete, onSkip }) {
  const [selections, setSelections] = useState({})
  const [expandedQuestions, setExpandedQuestions] = useState({})
  const [customTemplates, setCustomTemplates] = useState({})
  const [validationErrors, setValidationErrors] = useState([])

  // Initialize selections from enriched matrix
  useEffect(() => {
    if (!enrichedMatrix || !enrichedMatrix.lessons) return

    const initialSelections = {}
    enrichedMatrix.lessons.forEach((lesson, lessonIndex) => {
      // Process TN questions
      if (lesson.TN) {
        ['NB', 'TH', 'VD'].forEach(level => {
          const questions = lesson.TN[level] || []
          questions.forEach((q, qIndex) => {
            if (q.question_template && q.question_template.length > 0) {
              const key = `${lessonIndex}-TN-${level}-${qIndex}`
              initialSelections[key] = {
                lesson_index: lessonIndex,
                question_type: 'TN',
                level: level,
                question_index: qIndex,
                selected_template: null,
                is_custom: false,
                is_random: false
              }
            }
          })
        })
      }

      // Process DS questions
      if (lesson.DS && Array.isArray(lesson.DS)) {
        lesson.DS.forEach((q, qIndex) => {
          if (q.question_template && q.question_template.length > 0) {
            const key = `${lessonIndex}-DS-${qIndex}`
            initialSelections[key] = {
              lesson_index: lessonIndex,
              question_type: 'DS',
              level: null,
              question_index: qIndex,
              selected_template: null,
              is_custom: false,
              is_random: false
            }
          }
        })
      }

      // Process TLN questions
      if (lesson.TLN) {
        ['NB', 'TH', 'VD'].forEach(level => {
          const questions = lesson.TLN[level] || []
          questions.forEach((q, qIndex) => {
            if (q.question_template && q.question_template.length > 0) {
              const key = `${lessonIndex}-TLN-${level}-${qIndex}`
              initialSelections[key] = {
                lesson_index: lessonIndex,
                question_type: 'TLN',
                level: level,
                question_index: qIndex,
                selected_template: null,
                is_custom: false,
                is_random: false
              }
            }
          })
        })
      }

      // Process TL questions
      if (lesson.TL) {
        ['NB', 'TH', 'VD'].forEach(level => {
          const questions = lesson.TL[level] || []
          questions.forEach((q, qIndex) => {
            if (q.question_template && q.question_template.length > 0) {
              const key = `${lessonIndex}-TL-${level}-${qIndex}`
              initialSelections[key] = {
                lesson_index: lessonIndex,
                question_type: 'TL',
                level: level,
                question_index: qIndex,
                selected_template: null,
                is_custom: false,
                is_random: false
              }
            }
          })
        })
      }
    })

    setSelections(initialSelections)
  }, [enrichedMatrix])

  const handleTemplateSelect = (key, template, isCustom = false) => {
    setSelections(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        selected_template: template,
        is_custom: isCustom,
        is_random: false
      }
    }))
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
          selected_template: randomTemplate,
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
      handleTemplateSelect(key, customValue.trim(), true)
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
      if (!selections[key].selected_template) {
        errors.push(key)
      }
    })
    setValidationErrors(errors)
    return errors.length === 0
  }

  const handleSubmit = () => {
    if (!validateSelections()) {
      alert('Vui lòng chọn câu hỏi mẫu cho tất cả các câu hỏi hoặc chọn "Bỏ qua" để hệ thống tự chọn ngẫu nhiên')
      return
    }

    const selectionsArray = Object.values(selections)
    onComplete(selectionsArray)
  }

  const handleSkipAll = () => {
    // Auto-select random templates for all questions
    const newSelections = { ...selections }
    
    Object.keys(newSelections).forEach(key => {
      if (!newSelections[key].selected_template) {
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
          newSelections[key].selected_template = randomTemplate
          newSelections[key].is_random = true
        }
      }
    })

    setSelections(newSelections)
    setTimeout(() => {
      onComplete(Object.values(newSelections))
    }, 500)
  }

  if (!enrichedMatrix || !enrichedMatrix.lessons) {
    return (
      <div className="p-8 text-center text-gray-500">
        Đang tải dữ liệu câu hỏi mẫu...
      </div>
    )
  }

  const totalQuestions = Object.keys(selections).length
  const selectedCount = Object.values(selections).filter(s => s.selected_template).length

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Chọn câu hỏi mẫu cho môn Toán</h2>
          <p className="text-sm text-gray-600 mt-1">
            Hệ thống cần bạn chọn 1 câu hỏi mẫu cho mỗi câu để AI sinh câu hỏi tương tự
          </p>
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
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {enrichedMatrix.lessons.map((lesson, lessonIndex) => (
              <div key={lessonIndex} className="border border-gray-300 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 font-medium text-gray-900">
                  Chương {lesson.chapter_number} - Bài {lesson.lesson_number}: {lesson.lesson_name || 'Bài học'}
                </div>
                
                <div className="divide-y divide-gray-200">
                  {/* Render TN questions */}
                  {lesson.TN && ['NB', 'TH', 'VD'].map(level => {
                    const questions = lesson.TN[level] || []
                    return questions.map((q, qIndex) => {
                      if (!q.question_template || q.question_template.length === 0) return null
                      
                      const key = `${lessonIndex}-TN-${level}-${qIndex}`
                      const selection = selections[key]
                      const isExpanded = expandedQuestions[key]
                      const hasError = validationErrors.includes(key)

                      return (
                        <QuestionTemplateItem
                          key={key}
                          questionKey={key}
                          questionType="TN"
                          level={level}
                          question={q}
                          selection={selection}
                          isExpanded={isExpanded}
                          hasError={hasError}
                          customTemplate={customTemplates[key] || ''}
                          onTemplateSelect={handleTemplateSelect}
                          onRandomSelect={handleRandomSelect}
                          onToggleExpand={toggleExpanded}
                          onCustomTemplateChange={handleCustomTemplateChange}
                          onCustomTemplateApply={handleCustomTemplateApply}
                        />
                      )
                    })
                  })}

                  {/* Render DS questions */}
                  {lesson.DS && lesson.DS.map((q, qIndex) => {
                    if (!q.question_template || q.question_template.length === 0) return null
                    
                    const key = `${lessonIndex}-DS-${qIndex}`
                    const selection = selections[key]
                    const isExpanded = expandedQuestions[key]
                    const hasError = validationErrors.includes(key)

                    return (
                      <QuestionTemplateItem
                        key={key}
                        questionKey={key}
                        questionType="DS"
                        level={null}
                        question={q}
                        selection={selection}
                        isExpanded={isExpanded}
                        hasError={hasError}
                        customTemplate={customTemplates[key] || ''}
                        onTemplateSelect={handleTemplateSelect}
                        onRandomSelect={handleRandomSelect}
                        onToggleExpand={toggleExpanded}
                        onCustomTemplateChange={handleCustomTemplateChange}
                        onCustomTemplateApply={handleCustomTemplateApply}
                      />
                    )
                  })}

                  {/* Render TLN questions */}
                  {lesson.TLN && ['NB', 'TH', 'VD'].map(level => {
                    const questions = lesson.TLN[level] || []
                    return questions.map((q, qIndex) => {
                      if (!q.question_template || q.question_template.length === 0) return null
                      
                      const key = `${lessonIndex}-TLN-${level}-${qIndex}`
                      const selection = selections[key]
                      const isExpanded = expandedQuestions[key]
                      const hasError = validationErrors.includes(key)

                      return (
                        <QuestionTemplateItem
                          key={key}
                          questionKey={key}
                          questionType="TLN"
                          level={level}
                          question={q}
                          selection={selection}
                          isExpanded={isExpanded}
                          hasError={hasError}
                          customTemplate={customTemplates[key] || ''}
                          onTemplateSelect={handleTemplateSelect}
                          onRandomSelect={handleRandomSelect}
                          onToggleExpand={toggleExpanded}
                          onCustomTemplateChange={handleCustomTemplateChange}
                          onCustomTemplateApply={handleCustomTemplateApply}
                        />
                      )
                    })
                  })}

                  {/* Render TL questions */}
                  {lesson.TL && ['NB', 'TH', 'VD'].map(level => {
                    const questions = lesson.TL[level] || []
                    return questions.map((q, qIndex) => {
                      if (!q.question_template || q.question_template.length === 0) return null
                      
                      const key = `${lessonIndex}-TL-${level}-${qIndex}`
                      const selection = selections[key]
                      const isExpanded = expandedQuestions[key]
                      const hasError = validationErrors.includes(key)

                      return (
                        <QuestionTemplateItem
                          key={key}
                          questionKey={key}
                          questionType="TL"
                          level={level}
                          question={q}
                          selection={selection}
                          isExpanded={isExpanded}
                          hasError={hasError}
                          customTemplate={customTemplates[key] || ''}
                          onTemplateSelect={handleTemplateSelect}
                          onRandomSelect={handleRandomSelect}
                          onToggleExpand={toggleExpanded}
                          onCustomTemplateChange={handleCustomTemplateChange}
                          onCustomTemplateApply={handleCustomTemplateApply}
                        />
                      )
                    })
                  })}
                </div>
              </div>
            ))}
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
  selection,
  isExpanded,
  hasError,
  customTemplate,
  onTemplateSelect,
  onRandomSelect,
  onToggleExpand,
  onCustomTemplateChange,
  onCustomTemplateApply
}) {
  const levelNames = { NB: 'Nhận biết', TH: 'Thông hiểu', VD: 'Vận dụng' }
  const typeNames = { TN: 'Trắc nghiệm', DS: 'Đúng/Sai', TLN: 'Trả lời ngắn', TL: 'Tự luận' }

  return (
    <div className={`p-4 ${hasError ? 'bg-red-50' : 'bg-white'}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
              {typeNames[questionType]}
            </span>
            {level && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                {levelNames[level]}
              </span>
            )}
            {hasError && (
              <span className="text-xs text-red-600 font-medium">Chưa chọn</span>
            )}
          </div>
          <div className="text-sm text-gray-700 mb-2">
            <span className="font-medium">Kết quả học tập:</span> {question.learning_outcome || 'N/A'}
          </div>
          {selection && selection.selected_template && (
            <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded">
              <div className="text-xs text-green-700 font-medium mb-1 flex items-center gap-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Đã chọn {selection.is_custom ? '(Tự nhập)' : selection.is_random ? '(Ngẫu nhiên)' : ''}
              </div>
              <div className="text-sm text-gray-800 whitespace-pre-wrap">{selection.selected_template}</div>
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
          {/* Template options */}
          <div className="grid grid-cols-1 gap-2">
            {question.question_template.map((template, idx) => (
              <label
                key={idx}
                className="flex items-start gap-3 p-3 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="radio"
                  name={questionKey}
                  checked={selection && selection.selected_template === template && !selection.is_custom}
                  onChange={() => onTemplateSelect(questionKey, template, false)}
                  className="mt-1 flex-shrink-0"
                />
                <span className="text-sm text-gray-700 flex-1">{template}</span>
              </label>
            ))}
          </div>

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
        </div>
      )}
    </div>
  )
}
