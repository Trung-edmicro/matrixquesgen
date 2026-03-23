import { useState, useEffect, useRef } from 'react'
import { updateQuestion, regenerateQuestion, regenerateBulkQuestions, editQuestion } from '../../services/api'
import LaTeXRenderer from '../common/LaTeXRenderer'
import RichContentRenderer from '../common/RichContentRenderer'

export default function ExamPreviewPanel({ examData, isGenerating, sessionId, onDataChange }) {
  const [activeTab, setActiveTab] = useState('questions')
  const [editedData, setEditedData] = useState(null)
  const [isDirty, setIsDirty] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [selectedQuestions, setSelectedQuestions] = useState(new Set())
  const [regeneratingQuestions, setRegeneratingQuestions] = useState(new Set())
  const [editingQuestions, setEditingQuestions] = useState(new Set())
  const [regenerateQueue, setRegenerateQueue] = useState([])
  const [activeRegenerations, setActiveRegenerations] = useState(0)
  const MAX_CONCURRENT_REGENERATIONS = 3 // Giới hạn 3 requests song song
  const saveTimerRef = useRef(null) // Timer cho auto-save sau regenerate
  const needsAutoSaveRef = useRef(false) // Flag để track khi cần auto-save
  const needsAutoSaveEditRef = useRef(false) // Flag để track khi cần auto-save sau edit

  const tabs = [
    { id: 'questions', label: 'Đề' },
    { id: 'answers', label: 'Đáp án' }
  ]

  // Get questions from examData structure
  const questions = editedData?.questions || examData?.questions || { TN: [], DS: [], TLN: [], TL: [] }
  const metadata = examData?.metadata || {}
  
  // Kiểm tra môn học có cần hiển thị source không
  const shouldDisplaySource = () => {
    const subject = metadata?.subject?.toUpperCase() || ''
    const subjectsWithSource = ['LICHSU'] // Danh sách môn hiển thị source
    return subjectsWithSource.includes(subject)
  }

  // Reset edited data when examData changes
  useEffect(() => {
    if (examData) {
      setEditedData(JSON.parse(JSON.stringify(examData)))
      setIsDirty(false)
      setSelectedQuestions(new Set())
      setRegeneratingQuestions(new Set())
      setEditingQuestions(new Set())
    }
  }, [examData])

  // Auto-save sau khi regenerate xong (debounced)
  useEffect(() => {
    // Chỉ auto-save khi không còn regeneration nào đang chạy VÀ có flag cần save
    if (regeneratingQuestions.size === 0 && activeRegenerations === 0 && needsAutoSaveRef.current) {
      // Clear timer cũ nếu có
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
      
      // Đợi 1 giây sau khi tất cả regenerations hoàn thành rồi mới save
      saveTimerRef.current = setTimeout(() => {
        if (editedData && onDataChange) {
          console.log('Auto-saving after regeneration...')
          onDataChange(editedData, false) // false = không hiển thị thông báo
          needsAutoSaveRef.current = false // Reset flag sau khi save
        }
      }, 1000)
    }
    
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
    }
  }, [regeneratingQuestions.size, activeRegenerations, onDataChange])

  // Auto-save sau khi edit xong (debounced)
  useEffect(() => {
    // Chỉ auto-save khi không còn editing nào đang chạy VÀ có flag cần save
    if (editingQuestions.size === 0 && needsAutoSaveEditRef.current) {
      // Clear timer cũ nếu có
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
      
      // Đợi 1 giây sau khi edit hoàn thành rồi mới save
      saveTimerRef.current = setTimeout(() => {
        if (editedData && onDataChange) {
          console.log('Auto-saving after edit...')
          onDataChange(editedData, false) // false = không hiển thị thông báo
          needsAutoSaveEditRef.current = false // Reset flag sau khi save
        }
      }, 1000)
    }
    
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
    }
  }, [editingQuestions.size, onDataChange])

  const handleSave = async () => {
    if (!sessionId || !isDirty) return

    setIsSaving(true)
    try {
      // Update all TN questions
      for (const q of editedData.questions.TN) {
        await updateQuestion(sessionId, 'TN', q.question_code, q)
      }
      
      // Update all DS questions
      for (const q of editedData.questions.DS) {
        await updateQuestion(sessionId, 'DS', q.question_code, q)
      }
      
      // Update all TLN questions
      for (const q of editedData.questions.TLN || []) {
        await updateQuestion(sessionId, 'TLN', q.question_code, q)
      }
      
      // Update all TL questions
      for (const q of editedData.questions.TL || []) {
        await updateQuestion(sessionId, 'TL', q.question_code, q)
      }
      
      setIsDirty(false)
      if (onDataChange) {
        onDataChange(editedData)
      }
    } catch (err) {
      alert('Lỗi khi lưu: ' + err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleFieldChange = (type, code, field, value) => {
    setEditedData(prev => {
      const newData = JSON.parse(JSON.stringify(prev))
      const questionList = newData.questions[type]
      const question = questionList.find(q => q.question_code === code)
      if (question) {
        if (field.includes('.')) {
          const parts = field.split('.')
          if (parts.length === 2) {
            const [parent, child] = parts
            if (!question[parent]) question[parent] = {}
            question[parent][child] = value
          } else if (parts.length === 3) {
            // Handle nested like statements.a.text
            const [parent, key, prop] = parts
            if (!question[parent]) question[parent] = {}
            if (!question[parent][key]) question[parent][key] = {}
            question[parent][key][prop] = value
          }
        } else {
          question[field] = value
        }
      }
      return newData
    })
    setIsDirty(true)
  }

  const handleToggleQuestion = (type, code) => {
    setSelectedQuestions(prev => {
      const newSet = new Set(prev)
      const key = `${type}:${code}`
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return newSet
    })
  }

  const handleRegenerateQuestion = async (type, code) => {
    if (!sessionId) return
    
    const key = `${type}:${code}`
    
    // Kiểm tra xem câu này đã trong queue hoặc đang regenerate chưa
    if (regeneratingQuestions.has(key)) {
      console.log(`Question ${key} is already regenerating`)
      return
    }
    
    // Đánh dấu cần auto-save khi regeneration hoàn thành
    needsAutoSaveRef.current = true
    
    // Đánh dấu là đang regenerate
    setRegeneratingQuestions(prev => new Set(prev).add(key))
    
    // Nếu đã đạt giới hạn concurrent, đợi
    const executeRegeneration = async () => {
      try {
        setActiveRegenerations(prev => prev + 1)
        
        const result = await regenerateQuestion(sessionId, type, code)
        
        // Update the question in editedData
        setEditedData(prev => {
          const newData = JSON.parse(JSON.stringify(prev))
          const questionList = newData.questions[type]
          const questionIdx = questionList.findIndex(q => q.question_code === code)
          if (questionIdx !== -1) {
            questionList[questionIdx] = result.question
          }
          return newData
        })
        
        // Data đã được update trong editedData
        // Auto-save sẽ được trigger bởi useEffect sau khi regeneration hoàn thành
      } catch (err) {
        console.error(`Error regenerating ${key}:`, err)
        alert('Lỗi khi sinh lại câu hỏi: ' + err.message)
      } finally {
        setActiveRegenerations(prev => prev - 1)
        setRegeneratingQuestions(prev => {
          const newSet = new Set(prev)
          newSet.delete(key)
          return newSet
        })
      }
    }
    
    // Thực thi ngay không cần queue - browser sẽ tự handle concurrent
    executeRegeneration()
  }

  const handleEditDialogClose = (type, code) => {
    // This will be passed to QuestionsList to close the edit dialog
    // The actual closing logic is handled in QuestionsList component
  }

  const handleEditQuestion = async (type, code, comment, onEditDialogClose) => {
    if (!sessionId) return

    const questionKey = `${type}:${code}`;
    if (editingQuestions.has(questionKey)) {
      return
    }

    setEditingQuestions(prev => {
      const next = new Set(prev)
      next.add(questionKey)
      return next
    })
    
    try {
      if (document.activeElement) {
        document.activeElement.blur()
      }
      
      const result = await editQuestion(sessionId, type, code, comment)
      
      const updatedData = (() => {
        const newData = { ...editedData }
        if (!newData.questions) newData.questions = {}
        if (!newData.questions[type]) newData.questions[type] = []
        
        const qIndex = newData.questions[type].findIndex(q => q.question_code === code)
        if (qIndex !== -1) {
          newData.questions[type][qIndex] = {
            ...newData.questions[type][qIndex],
            ...result.question
          }
        }
        return newData
      })()
      
      setEditedData(updatedData)
      
      // Đánh dấu cần auto-save
      needsAutoSaveEditRef.current = true
      
      // Update localStorage via parent callback
      if (onDataChange) {
        onDataChange(updatedData, false)
      }
      
      toast.success(result.message || 'Đã sửa lại câu ' + code)
      // Close dialog after success
      if (onEditDialogClose) onEditDialogClose(type, code)
    } catch (err) {
      console.error('Error editing question:', err)
      toast.error(err.response?.data?.detail || 'Lỗi khi sửa lại câu hỏi')
      // Close dialog even on error
      if (onEditDialogClose) onEditDialogClose(type, code)
    } finally {
      setEditingQuestions(prev => {
        const next = new Set(prev)
        next.delete(questionKey)
        return next
      })
    }
  }

const handleRegenerateBulk = async () => {
    if (!sessionId || selectedQuestions.size === 0) return
    
    const questionsToRegenerate = Array.from(selectedQuestions).map(key => {
      const [type, code] = key.split(':')
      return { type, code }
    })
    
    // Đánh dấu cần auto-save khi regeneration hoàn thành
    needsAutoSaveRef.current = true
    
    // Add all to regenerating set
    setRegeneratingQuestions(prev => new Set([...prev, ...selectedQuestions]))
    
    try {
      const result = await regenerateBulkQuestions(sessionId, questionsToRegenerate)
      
      // Update all regenerated questions
      setEditedData(prev => {
        const newData = JSON.parse(JSON.stringify(prev))
        
        for (const item of result.results) {
          if (item.status === 'success') {
            const questionList = newData.questions[item.type]
            const questionIdx = questionList.findIndex(q => q.question_code === item.code)
            if (questionIdx !== -1) {
              questionList[questionIdx] = item.question
            }
          }
        }
        
        return newData
      })
      
      // Clear selections
      setSelectedQuestions(new Set())
      
      // Auto-save sẽ được trigger bởi useEffect sau khi regeneration hoàn thành
      
      // Show result
      if (result.errors && result.errors.length > 0) {
        alert(`Sinh lại hoàn tất với ${result.succeeded} thành công và ${result.failed} lỗi`)
      }
    } catch (err) {
      alert('Lỗi khi sinh lại câu hỏi: ' + err.message)
    } finally {
      setRegeneratingQuestions(new Set())
    }
  }

  return (
    <div className="h-full panel flex flex-col">
      {/* Tabs and Save Button */}
      <div className="border-b border-gray-200 flex items-center justify-between flex-shrink-0">
        <div className="flex">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-base border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-700'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        
        {isDirty && examData && (
          <div className="px-4 flex items-center gap-3">
            <span className="text-sm text-orange-600">● Có thay đổi chưa lưu</span>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="btn-primary text-sm px-4 py-1.5 disabled:opacity-50"
            >
              {isSaving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        {isGenerating ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin mb-2"></div>
              <div className="text-base text-gray-600">Đang sinh câu hỏi...</div>
              {sessionId && (
                <div className="text-sm text-gray-500 mt-2">Session: {sessionId.slice(0, 8)}</div>
              )}
            </div>
          </div>
        ) : examData ? (
          <>
            {/* Metadata info */}
            {metadata.total_questions > 0 && (
              <div className="bg-gray-50 p-3 rounded text-sm text-gray-600 mb-4">
                <div>Tổng: {metadata.total_questions} câu ({metadata.tn_count || 0} TN, {metadata.ds_count || 0} DS, {metadata.tln_count || 0} TLN, {metadata.tl_count || 0} TL)</div>
                {metadata.generated_at && (
                  <div className="text-gray-500 mt-1">
                    Thời gian: {new Date(metadata.generated_at).toLocaleString('vi-VN')}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'questions' && (
              <QuestionsList 
                questions={questions} 
                onFieldChange={handleFieldChange}
                sessionId={sessionId}
                shouldDisplaySource={shouldDisplaySource()}
                metadata={metadata}
                selectedQuestions={selectedQuestions}
                onToggleQuestion={handleToggleQuestion}
                regeneratingQuestions={regeneratingQuestions}
                editingQuestions={editingQuestions}
                onRegenerateQuestion={handleRegenerateQuestion}
                onRegenerateBulk={handleRegenerateBulk}
                onEditQuestion={handleEditQuestion}
              />
            )}
            {activeTab === 'answers' && (
              <AnswersList questions={questions} />
            )}
          </>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-sm text-gray-500">
              Chọn file ma trận và nhấn "Sinh đề" để bắt đầu
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function QuestionsList({ questions, onFieldChange, sessionId, shouldDisplaySource, metadata, selectedQuestions, onToggleQuestion, regeneratingQuestions, editingQuestions, onRegenerateQuestion, onRegenerateBulk, onEditQuestion }) {

  const [editStates, setEditStates] = useState({})

  const toggleEditComment = (type, code) => {
    const key = type + '_' + code
    setEditStates(prev => ({
      ...prev,
      [key]: { isOpen: !prev[key]?.isOpen, comment: '' }
    }))
  }

  const handleCommentChange = (type, code, val) => {
    const key = type + '_' + code
    setEditStates(prev => ({
      ...prev,
      [key]: { ...prev[key], comment: val }
    }))
  }

  const closeEditDialog = (type, code) => {
    const key = type + '_' + code
    setEditStates(prev => ({
      ...prev,
      [key]: { ...prev[key], isOpen: false }
    }))
  }

  const submitEdit = (type, code) => {
    const key = type + '_' + code
    const comment = editStates[key]?.comment
    if (!comment) return
    onEditQuestion(type, code, comment, closeEditDialog)
    // Dialog will be closed by handleEditQuestion via closeEditDialog callback
  }

  const getLevelColor = (level) => {
    switch(level) {
      case 'NB': return 'bg-green-100 text-green-800'
      case 'TH': return 'bg-primary-100 text-primary-800'
      case 'VD': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  // Sort function cho question_code (C1, C2, ..., C10, C11, ...)
  const sortByQuestionCode = (a, b) => {
    const getNumber = (code) => parseInt(code.replace('C', ''))
    return getNumber(a.question_code) - getNumber(b.question_code)
  }

  // Sort all question types
  const sortedTN = [...(questions.TN || [])].sort(sortByQuestionCode)
  const sortedDS = [...(questions.DS || [])].sort(sortByQuestionCode)
  const sortedTLN = [...(questions.TLN || [])].sort(sortByQuestionCode)
  const sortedTL = [...(questions.TL || [])].sort(sortByQuestionCode)

  const handleBlur = (type, code, field, e) => {
    const newValue = e.target.textContent
    
    // Lấy giá trị cũ để so sánh
    const oldValue = (() => {
      const questionList = editedData?.questions?.[type] || []
      const question = questionList.find(q => q.question_code === code)
      if (!question) return ''
      
      if (field.includes('.')) {
        const parts = field.split('.')
        if (parts.length === 2) {
          const [parent, child] = parts
          return question[parent]?.[child] || ''
        } else if (parts.length === 3) {
          const [parent, key, prop] = parts
          return question[parent]?.[key]?.[prop] || ''
        }
      }
      return question[field] || ''
    })()
    
    // Chỉ update nếu giá trị thực sự thay đổi
    if (newValue !== oldValue) {
      handleFieldChange(type, code, field, newValue)
    }
  }

  const handleLevelChange = (type, code, field, newLevel) => {
    if (onFieldChange) {
      onFieldChange(type, code, field, newLevel)
    }
  }

  const handleCorrectAnswerToggle = (type, code, field, value) => {
    if (onFieldChange) {
      onFieldChange(type, code, field, value)
    }
  }

  return (
    <div>
      {/* Header with bulk regenerate button */}
      {sessionId && selectedQuestions && selectedQuestions.size > 0 && (
        <div className="mb-4 p-3 bg-primary-50 border border-primary-200 rounded flex items-center justify-between">
          <span className="text-sm text-primary-800">
            Đã chọn {selectedQuestions.size} câu hỏi
          </span>
          <button
            onClick={onRegenerateBulk}
            disabled={regeneratingQuestions && regeneratingQuestions.size > 0}
            className="btn-primary text-sm px-4 py-1.5 disabled:opacity-50"
          >
            {regeneratingQuestions && regeneratingQuestions.size > 0 ? 'Đang sinh lại...' : 'Sinh lại các câu đã chọn'}
          </button>
        </div>
      )}

      {/* TN Questions */}
      {sortedTN.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3">Phần I: Trắc nghiệm</h3>
          {sortedTN.map((q, idx) => {
            const questionKey = `TN:${q.question_code}`
            const isSelected = selectedQuestions && selectedQuestions.has(questionKey)
            const isRegenerating = regeneratingQuestions && regeneratingQuestions.has(questionKey)
            const isEditing = editingQuestions && editingQuestions.has(questionKey)
            
            return (
              <div key={q.question_code} className="mb-5 text-base border-b border-gray-100 pb-5">
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-medium">Câu {idx + 1}:</span>
                  {sessionId ? (
                    <select
                    value={q.level}
                    onChange={(e) => handleLevelChange('TN', q.question_code, 'level', e.target.value)}
                    className={`px-2 py-0.5 text-sm rounded border-0 cursor-pointer ${getLevelColor(q.level)}`}
                    >
                      <option value="NB">NB</option>
                      <option value="TH">TH</option>
                      <option value="VD">VD</option>
                    </select>
                  ) : (
                    <span className={`px-2 py-0.5 text-sm rounded ${getLevelColor(q.level)}`}>
                      {q.level}
                    </span>
                  )}
                  <span className="text-sm text-gray-500">[{q.question_code}]</span>
                  
                  {/* Edit with AI button */}
                  {sessionId && (
                    <button
                      onClick={() => toggleEditComment('TN', q.question_code)}
                      disabled={isEditing || isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sửa câu hỏi bằng AI"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  )}

                  {/* Regenerate button */}
                  {sessionId && (
                    <button
                      onClick={() => onRegenerateQuestion('TN', q.question_code)}
                      disabled={isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sinh lại câu hỏi này"
                    >
                      {isRegenerating ? (
                        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      )}
                    </button>
                  )}

                  {/* Checkbox for selection */}
                  {sessionId && (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleQuestion('TN', q.question_code)}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                      disabled={isRegenerating}
                    />
                  )}
                </div>
                  {/* Edit box */}
                  {editStates['TN_' + q.question_code]?.isOpen && (
                    <div className="mt-3 mb-4 p-4 border border-primary-200 bg-primary-50 rounded-lg">
                      <h4 className="text-sm font-semibold text-primary-800 mb-2">Yêu cầu sửa câu hỏi</h4>
                      <textarea
                        className="w-full p-2 border border-primary-300 rounded text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        rows="3"
                        placeholder="Nhập nhận xét / comment để sửa câu hỏi này..."
                        value={editStates['TN_' + q.question_code]?.comment || ''}
                        onChange={(e) => handleCommentChange('TN', q.question_code, e.target.value)}
                        disabled={isRegenerating}
                      ></textarea>
                      <div className="mt-2 flex justify-end space-x-2">
                        <button
                          onClick={() => toggleEditComment('TN', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50"
                          disabled={isEditing}
                        >
                          Hủy
                        </button>
                        <button
                          onClick={() => submitEdit('TN', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-white bg-primary-600 rounded hover:bg-primary-700 flex items-center shadow-sm"
                          disabled={!editStates['TN_' + q.question_code]?.comment || isEditing}
                        >
                          {isEditing ? (
                            <><svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Đang sửa...</>
                          ) : (
                            'Gửi'
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                <div className="mb-2 text-gray-700">
                  <RichContentRenderer
                    content={q.question_stem}
                    contentEditable={!!sessionId}
                    onBlur={(e) => handleBlur('TN', q.question_code, 'question_stem', e)}
                    className="focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-1"
                  />
                </div>
                <div className="space-y-1 pl-4">
                  {Object.entries(q.options || {}).map(([key, value]) => (
                    <div 
                      key={key} 
                      className="flex items-start gap-2"
                    >
                      {sessionId && (
                        <input
                          type="radio"
                          name={`correct-${q.question_code}`}
                          checked={q.correct_answer === key}
                          onChange={() => handleCorrectAnswerToggle('TN', q.question_code, 'correct_answer', key)}
                          className="mt-1 w-4 h-4 text-red-600 cursor-pointer"
                        />
                      )}
                      <div className={q.correct_answer === key ? 'text-red-600 font-medium flex-1' : 'text-gray-600 flex-1'}>
                        <span>{key}. </span>
                        <LaTeXRenderer
                          contentEditable={!!sessionId}
                          onBlur={(e) => handleBlur('TN', q.question_code, `options.${key}`, e)}
                          className="focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-1 inline"
                        >
                          {value}
                        </LaTeXRenderer>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* DS Questions */}
      {sortedDS.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3 mt-6">Phần II: Đúng/Sai</h3>
          {sortedDS.map((q, idx) => {
            const questionKey = `DS:${q.question_code}`
            const isSelected = selectedQuestions && selectedQuestions.has(questionKey)
            const isRegenerating = regeneratingQuestions && regeneratingQuestions.has(questionKey)
            const isEditing = editingQuestions && editingQuestions.has(questionKey)
            
            return (
              <div key={q.question_code} className="mb-6 text-base border-b border-gray-100 pb-5">
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-medium">Câu {idx + 1}:</span>
                  <span className="ml-2 text-sm text-gray-500">[{q.question_code}]</span>
                  
                  {/* Edit with AI button */}
                  {sessionId && (
                    <button
                      onClick={() => toggleEditComment('DS', q.question_code)}
                      disabled={isEditing || isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sửa câu hỏi bằng AI"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  )}

                  {/* Regenerate button */}
                  {sessionId && (
                    <button
                      onClick={() => onRegenerateQuestion('DS', q.question_code)}
                      disabled={isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sinh lại câu hỏi này"
                    >
                      {isRegenerating ? (
                        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      )}
                    </button>
                  )}

                  {/* Checkbox for selection */}
                  {sessionId && (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleQuestion('DS', q.question_code)}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                      disabled={isRegenerating}
                    />
                  )}
                </div>
                  {/* Edit box */}
                  {editStates['DS_' + q.question_code]?.isOpen && (
                    <div className="mt-3 mb-4 p-4 border border-primary-200 bg-primary-50 rounded-lg">
                      <h4 className="text-sm font-semibold text-primary-800 mb-2">Yêu cầu sửa câu hỏi</h4>
                      <textarea
                        className="w-full p-2 border border-primary-300 rounded text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        rows="3"
                        placeholder="Nhập nhận xét / comment để sửa câu hỏi này..."
                        value={editStates['DS_' + q.question_code]?.comment || ''}
                        onChange={(e) => handleCommentChange('DS', q.question_code, e.target.value)}
                        disabled={isRegenerating}
                      ></textarea>
                      <div className="mt-2 flex justify-end space-x-2">
                        <button
                          onClick={() => toggleEditComment('DS', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50"
                          disabled={isEditing}
                        >
                          Hủy
                        </button>
                        <button
                          onClick={() => submitEdit('DS', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-white bg-primary-600 rounded hover:bg-primary-700 flex items-center shadow-sm"
                          disabled={!editStates['DS_' + q.question_code]?.comment || isEditing}
                        >
                          {isEditing ? (
                            <><svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Đang sửa...</>
                          ) : (
                            'Gửi'
                          )}
                        </button>
                      </div>
                    </div>
                  )}
              
              {/* Always display source_text.content for DS questions */}
              {q.source_text && (
                <div className="mb-3 text-gray-600 italic text-sm bg-gray-50 p-3 rounded">
                  <RichContentRenderer
                    content={q.source_text}
                    contentEditable={!!sessionId}
                    onBlur={(e) => handleBlur('DS', q.question_code, 'source_text', e)}
                    className="focus:outline-none focus:ring-2 focus:ring-primary-300"
                  />
                  
                  {/* Source Citation - Only show if subject needs source display */}
                  {shouldDisplaySource && (q.source_citation || q.source_text?.metadata?.source) && (
                    <div className="mt-2 text-right">
                      <span
                        className="text-xs text-gray-500 italic focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-1"
                        contentEditable={!!sessionId}
                        onBlur={(e) => handleBlur('DS', q.question_code, 'source_citation', e)}
                        suppressContentEditableWarning={true}
                      >
                        ({q.source_citation || q.source_text?.metadata?.source})
                      </span>
                    </div>
                  )}
                  
                  {/* Source Origin Badge - Only show if subject needs source display */}
                  {shouldDisplaySource && q.source_origin && (
                    <div className="mt-1">
                      <span className={`inline-block px-2 py-0.5 text-xs rounded ${
                        q.source_origin === 'academic_journal' ? 'bg-purple-100 text-purple-700' :
                        q.source_origin === 'scholarly_book' ? 'bg-primary-100 text-primary-700' :
                        q.source_origin === 'official_document' ? 'bg-green-100 text-green-700' :
                        'bg-orange-100 text-orange-700'
                      }`}>
                        {q.source_origin === 'academic_journal' ? '📚 Tạp chí học thuật' :
                         q.source_origin === 'scholarly_book' ? '📖 Sách chuyên khảo' :
                         q.source_origin === 'official_document' ? '📜 Văn kiện chính thức' :
                         '📰 Báo chí uy tín'}
                      </span>
                    </div>
                  )}
                </div>
              )}
              <div className="space-y-2 pl-4">
                {Object.entries(q.statements || {}).map(([key, stmt]) => (
                  <div key={key} className="flex items-start gap-2">
                    {sessionId && (
                      <input
                        type="checkbox"
                        checked={stmt.correct_answer}
                        onChange={() => handleCorrectAnswerToggle('DS', q.question_code, `statements.${key}.correct_answer`, !stmt.correct_answer)}
                        className="mt-1 w-4 h-4 text-red-600 cursor-pointer"
                      />
                    )}
                    {sessionId ? (
                      <select
                        value={stmt.level}
                        onChange={(e) => handleLevelChange('DS', q.question_code, `statements.${key}.level`, e.target.value)}
                        className={`px-2 py-0.5 text-sm rounded border-0 cursor-pointer ${getLevelColor(stmt.level)}`}
                      >
                        <option value="NB">NB</option>
                        <option value="TH">TH</option>
                        <option value="VD">VD</option>
                      </select>
                    ) : (
                      <span className={`px-2 py-0.5 text-sm rounded ${getLevelColor(stmt.level)}`}>
                        {stmt.level}
                      </span>
                    )}
                    <div className="flex-1">
                      <span>{key}. </span>
                      <LaTeXRenderer
                        contentEditable={!!sessionId}
                        onBlur={(e) => handleBlur('DS', q.question_code, `statements.${key}.text`, e)}
                        className={`focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-1 inline ${stmt.correct_answer ? 'text-red-600 font-medium' : 'text-gray-600'}`}
                      >
                        {stmt.text}
                      </LaTeXRenderer>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            )
          })}
        </div>
      )}

      {/* TLN Questions */}
      {sortedTLN.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3 mt-6">Phần III: Trả lời ngắn</h3>
          {sortedTLN.map((q, idx) => {
            const questionKey = `TLN:${q.question_code}`
            const isSelected = selectedQuestions && selectedQuestions.has(questionKey)
            const isRegenerating = regeneratingQuestions && regeneratingQuestions.has(questionKey)
            const isEditing = editingQuestions && editingQuestions.has(questionKey)
            
            return (
              <div key={q.question_code} className="mb-6 text-base border-b border-gray-100 pb-5">
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-medium">Câu {idx + 1}:</span>
                  <span className={`px-2 py-0.5 text-sm rounded ${getLevelColor(q.level)}`}>
                    {q.level}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">[{q.question_code}]</span>
                  
                  {/* Edit with AI button */}
                  {sessionId && (
                    <button
                      onClick={() => toggleEditComment('TLN', q.question_code)}
                      disabled={isEditing || isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sửa câu hỏi bằng AI"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  )}

                  {sessionId && (
                    <button
                      onClick={() => onRegenerateQuestion('TLN', q.question_code)}
                      disabled={isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sinh lại câu hỏi này"
                    >
                      {isRegenerating ? (
                        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      )}
                    </button>
                  )}
                  {sessionId && (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleQuestion('TLN', q.question_code)}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                      disabled={isRegenerating}
                    />
                  )}
                </div>
                  {/* Edit box */}
                  {editStates['TLN_' + q.question_code]?.isOpen && (
                    <div className="mt-3 mb-4 p-4 border border-primary-200 bg-primary-50 rounded-lg">
                      <h4 className="text-sm font-semibold text-primary-800 mb-2">Yêu cầu sửa câu hỏi</h4>
                      <textarea
                        className="w-full p-2 border border-primary-300 rounded text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        rows="3"
                        placeholder="Nhập nhận xét / comment để sửa câu hỏi này..."
                        value={editStates['TLN_' + q.question_code]?.comment || ''}
                        onChange={(e) => handleCommentChange('TLN', q.question_code, e.target.value)}
                        disabled={isRegenerating}
                      ></textarea>
                      <div className="mt-2 flex justify-end space-x-2">
                        <button
                          onClick={() => toggleEditComment('TLN', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50"
                          disabled={isEditing}
                        >
                          Hủy
                        </button>
                        <button
                          onClick={() => submitEdit('TLN', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-white bg-primary-600 rounded hover:bg-primary-700 flex items-center shadow-sm"
                          disabled={!editStates['TLN_' + q.question_code]?.comment || isEditing}
                        >
                          {isEditing ? (
                            <><svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Đang sửa...</>
                          ) : (
                            'Gửi'
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                <div className="text-gray-700">
                  <RichContentRenderer
                    content={q.question_stem}
                    contentEditable={!!sessionId}
                    onBlur={(e) => handleBlur('TLN', q.question_code, 'question_stem', e)}
                    className="focus:outline-none focus:ring-2 focus:ring-primary-300"
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* TL Questions */}
      {sortedTL.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3 mt-6">Phần IV: Tự luận</h3>
          {sortedTL.map((q, idx) => {
            const questionKey = `TL:${q.question_code}`
            const isSelected = selectedQuestions && selectedQuestions.has(questionKey)
            const isRegenerating = regeneratingQuestions && regeneratingQuestions.has(questionKey)
            const isEditing = editingQuestions && editingQuestions.has(questionKey)
            
            return (
              <div key={q.question_code} className="mb-6 text-base border-b border-gray-100 pb-5">
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-medium">Câu {idx + 1}:</span>
                  <span className={`px-2 py-0.5 text-sm rounded ${getLevelColor(q.level)}`}>
                    {q.level}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">[{q.question_code}]</span>
                  
                  {/* Edit with AI button */}
                  {sessionId && (
                    <button
                      onClick={() => toggleEditComment('TL', q.question_code)}
                      disabled={isEditing || isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sửa câu hỏi bằng AI"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  )}

                  {sessionId && (
                    <button
                      onClick={() => onRegenerateQuestion('TL', q.question_code)}
                      disabled={isRegenerating}
                      className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
                      title="Sinh lại câu hỏi này"
                    >
                      {isRegenerating ? (
                        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      )}
                    </button>
                  )}
                  {sessionId && (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleQuestion('TL', q.question_code)}
                      className="w-4 h-4 text-primary-600 cursor-pointer"
                      disabled={isRegenerating}
                    />
                  )}
                </div>
                  {/* Edit box */}
                  {editStates['TL_' + q.question_code]?.isOpen && (
                    <div className="mt-3 mb-4 p-4 border border-primary-200 bg-primary-50 rounded-lg">
                      <h4 className="text-sm font-semibold text-primary-800 mb-2">Yêu cầu sửa câu hỏi</h4>
                      <textarea
                        className="w-full p-2 border border-primary-300 rounded text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        rows="3"
                        placeholder="Nhập nhận xét / comment để sửa câu hỏi này..."
                        value={editStates['TL_' + q.question_code]?.comment || ''}
                        onChange={(e) => handleCommentChange('TL', q.question_code, e.target.value)}
                        disabled={isRegenerating}
                      ></textarea>
                      <div className="mt-2 flex justify-end space-x-2">
                        <button
                          onClick={() => toggleEditComment('TL', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50"
                          disabled={isEditing}
                        >
                          Hủy
                        </button>
                        <button
                          onClick={() => submitEdit('TL', q.question_code)}
                          className="px-3 py-1.5 text-sm font-medium text-white bg-primary-600 rounded hover:bg-primary-700 flex items-center shadow-sm"
                          disabled={!editStates['TL_' + q.question_code]?.comment || isEditing}
                        >
                          {isEditing ? (
                            <><svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Đang sửa...</>
                          ) : (
                            'Gửi'
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                <div className="text-gray-700">
                  <RichContentRenderer
                    content={q.question_stem}
                    contentEditable={!!sessionId}
                    onBlur={(e) => handleBlur('TL', q.question_code, 'question_stem', e)}
                    className="focus:outline-none focus:ring-2 focus:ring-primary-300"
                  />
                  {/* Sub-questions (a, b, ...) */}
                  {Array.isArray(q.explanation?.sub_questions) && q.explanation.sub_questions.length > 0 && (
                    <div className="mt-3 space-y-2 pl-2">
                      {q.explanation.sub_questions.map((sub) => (
                        <div key={sub.label} className="flex gap-2">
                          <span className="font-medium shrink-0">{sub.label})</span>
                          <div className="flex-1">
                            <RichContentRenderer content={sub.question_stem} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function AnswersList({ questions }) {
  // Sort function cho question_code (C1, C2, ..., C10, C11, ...)
  const sortByQuestionCode = (a, b) => {
    const getNumber = (code) => parseInt(code.replace('C', ''))
    return getNumber(a.question_code) - getNumber(b.question_code)
  }

  // Sort all question types
  const sortedTN = [...(questions.TN || [])].sort(sortByQuestionCode)
  const sortedDS = [...(questions.DS || [])].sort(sortByQuestionCode)
  const sortedTLN = [...(questions.TLN || [])].sort(sortByQuestionCode)
  const sortedTL = [...(questions.TL || [])].sort(sortByQuestionCode)

  return (
    <div>
      {sortedTN.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3">Phần I: Trắc nghiệm</h3>
          <div className="text-base space-y-2">
            {sortedTN.map((q, idx) => (
              <div key={q.question_code} className="border-b border-gray-100 pb-2">
                <div className="flex items-start gap-2 mb-1">
                  <span className="font-medium">Câu {idx + 1}:</span>
                  <span className="text-red-600 font-medium">{q.correct_answer}</span>
                </div>
                {q.explanation && (
                  <div className="text-sm text-gray-600 pl-16">
                    <LaTeXRenderer>{q.explanation}</LaTeXRenderer>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {sortedDS.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3">Phần II: Đúng/Sai</h3>
          <div className="text-base space-y-3">
            {sortedDS.map((q, idx) => (
              <div key={q.question_code} className="border-b border-gray-100 pb-3">
                <div className="font-medium mb-2">Câu {idx + 1}:</div>
                <div className="pl-4 space-y-1">
                  {Object.entries(q.statements || {}).map(([key, stmt]) => (
                    <div key={key} className="text-sm">
                      <span className="font-medium">{key}.</span>{' '}
                      <span className="text-red-600">{stmt.correct_answer ? 'Đúng' : 'Sai'}</span>
                      {q.explanation?.[key] && (
                        <div className="text-gray-600 pl-4 mt-1">
                          <LaTeXRenderer>{q.explanation[key]}</LaTeXRenderer>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {sortedTLN.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3">Phần III: Trả lời ngắn</h3>
          <div className="text-base space-y-2">
            {sortedTLN.map((q, idx) => (
              <div key={q.question_code} className="border-b border-gray-100 pb-2">
                <div className="flex items-start gap-2 mb-1">
                  <span className="font-medium">Câu {idx + 1}:</span>
                  <span className="text-red-600 font-medium">{q.correct_answer}</span>
                </div>
                {q.explanation && (
                  <div className="text-sm text-gray-600 pl-16">
                    <LaTeXRenderer>{q.explanation}</LaTeXRenderer>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {sortedTL.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3">Phần IV: Tự luận</h3>
          <div className="text-base space-y-3">
            {sortedTL.map((q, idx) => {
              const exp = q.explanation
              const subQuestions = exp?.sub_questions
              const hasSubQuestions = Array.isArray(subQuestions) && subQuestions.length > 0
              return (
                <div key={q.question_code} className="border-b border-gray-100 pb-3">
                  <div className="font-medium mb-2">Câu {idx + 1}:</div>
                  <div className="pl-4">
                    {q.correct_answer && (
                      <div className="mb-2">
                        <span className="font-medium text-red-600">Đáp án mẫu:</span>
                        <div className="text-sm text-gray-700 mt-1">
                          <LaTeXRenderer>{q.correct_answer}</LaTeXRenderer>
                        </div>
                      </div>
                    )}
                    {hasSubQuestions ? (
                      <div className="space-y-3">
                        {subQuestions.map((sub) => {
                          const as = sub.answer_structure || {}
                          return (
                            <div key={sub.label}>
                              <span className="font-medium">{sub.label})</span>
                              {(as.intro || as.body || as.conclusion) && (
                                <div className="text-sm text-gray-600 mt-1 space-y-1">
                                  {as.intro && <div><span className="font-medium">Mở đầu:</span> <LaTeXRenderer>{as.intro}</LaTeXRenderer></div>}
                                  {as.body && <div><span className="font-medium">Nội dung:</span> <LaTeXRenderer>{as.body}</LaTeXRenderer></div>}
                                  {as.conclusion && <div><span className="font-medium">Kết luận:</span> <LaTeXRenderer>{as.conclusion}</LaTeXRenderer></div>}
                                </div>
                              )}
                              {sub.explanation && (
                                <div className="text-sm text-gray-500 italic mt-1">
                                  <LaTeXRenderer>{sub.explanation}</LaTeXRenderer>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    ) : exp && (
                      <div>
                        <span className="font-medium">Hướng dẫn chấm điểm:</span>
                        {typeof exp === 'string' ? (
                          <div className="text-sm text-gray-600 mt-1"><LaTeXRenderer>{exp}</LaTeXRenderer></div>
                        ) : (
                          <div className="text-sm text-gray-600 mt-1 space-y-1">
                            {exp.answer_structure?.intro && <div><span className="font-medium">Mở đầu:</span> <LaTeXRenderer>{exp.answer_structure.intro}</LaTeXRenderer></div>}
                            {exp.answer_structure?.body && <div><span className="font-medium">Nội dung:</span> <LaTeXRenderer>{exp.answer_structure.body}</LaTeXRenderer></div>}
                            {exp.answer_structure?.conclusion && <div><span className="font-medium">Kết luận:</span> <LaTeXRenderer>{exp.answer_structure.conclusion}</LaTeXRenderer></div>}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
