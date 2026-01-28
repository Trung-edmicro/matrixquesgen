import { useState, useEffect } from 'react'
import { updateQuestion } from '../../services/api'
import LaTeXRenderer from '../common/LaTeXRenderer'

export default function ExamPreviewPanel({ examData, isGenerating, sessionId, onDataChange }) {
  const [activeTab, setActiveTab] = useState('questions')
  const [editedData, setEditedData] = useState(null)
  const [isDirty, setIsDirty] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const tabs = [
    { id: 'questions', label: 'Đề' },
    { id: 'answers', label: 'Đáp án' }
  ]

  // Get questions from examData structure
  const questions = editedData?.questions || examData?.questions || { TN: [], DS: [], TLN: [], TL: [] }
  const metadata = examData?.metadata || {}

  // Reset edited data when examData changes
  useEffect(() => {
    if (examData) {
      setEditedData(JSON.parse(JSON.stringify(examData)))
      setIsDirty(false)
    }
  }, [examData])

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

function QuestionsList({ questions, onFieldChange, sessionId }) {
  const getLevelColor = (level) => {
    switch(level) {
      case 'NB': return 'bg-green-100 text-green-800'
      case 'TH': return 'bg-blue-100 text-blue-800'
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
    if (onFieldChange) {
      onFieldChange(type, code, field, newValue)
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
      {/* TN Questions */}
      {sortedTN.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3">Phần I: Trắc nghiệm</h3>
          {sortedTN.map((q, idx) => (
            <div key={q.question_code} className="mb-5 text-base border-b border-gray-100 pb-5">
              <div className="mb-2 flex items-center gap-2">
                <span className="font-medium">Câu {idx + 1}</span>
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
              </div>
              <div className="mb-2 text-gray-700">
                <LaTeXRenderer
                  contentEditable={!!sessionId}
                  onBlur={(e) => handleBlur('TN', q.question_code, 'question_stem', e)}
                  className="focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-1 inline-block w-full"
                >
                  {q.question_stem}
                </LaTeXRenderer>
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
          ))}
        </div>
      )}

      {/* DS Questions */}
      {sortedDS.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3 mt-6">Phần II: Đúng/Sai</h3>
          {sortedDS.map((q, idx) => (
            <div key={q.question_code} className="mb-6 text-base border-b border-gray-100 pb-5">
              <div className="mb-2">
                <span className="font-medium">Câu {idx + 1}</span>
                <span className="ml-2 text-sm text-gray-500">[{q.question_code}]</span>
              </div>
              <div className="mb-3 text-gray-600 italic text-sm bg-gray-50 p-2 rounded">
                <LaTeXRenderer
                  contentEditable={!!sessionId}
                  onBlur={(e) => handleBlur('DS', q.question_code, 'source_text', e)}
                  className="focus:outline-none focus:ring-2 focus:ring-primary-300"
                >
                  {q.source_text}
                </LaTeXRenderer>
              </div>
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
          ))}
        </div>
      )}

      {/* TLN Questions */}
      {sortedTLN.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3 mt-6">Phần III: Trả lời ngắn</h3>
          {sortedTLN.map((q, idx) => (
            <div key={q.question_code} className="mb-6 text-base border-b border-gray-100 pb-5">
              <div className="mb-2 flex items-center gap-2">
                <span className="font-medium">Câu {idx + 1}</span>
                <span className={`px-2 py-0.5 text-sm rounded ${getLevelColor(q.level)}`}>
                  {q.level}
                </span>
                <span className="ml-2 text-sm text-gray-500">[{q.question_code}]</span>
              </div>
              <div className="text-gray-700">
                <LaTeXRenderer
                  contentEditable={!!sessionId}
                  onBlur={(e) => handleBlur('TLN', q.question_code, 'question_stem', e)}
                  className="focus:outline-none focus:ring-2 focus:ring-primary-300"
                >
                  {q.question_stem}
                </LaTeXRenderer>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TL Questions */}
      {sortedTL.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-medium text-gray-900 mb-3 mt-6">Phần IV: Tự luận</h3>
          {sortedTL.map((q, idx) => (
            <div key={q.question_code} className="mb-6 text-base border-b border-gray-100 pb-5">
              <div className="mb-2 flex items-center gap-2">
                <span className="font-medium">Câu {idx + 1}</span>
                <span className={`px-2 py-0.5 text-sm rounded ${getLevelColor(q.level)}`}>
                  {q.level}
                </span>
                <span className="ml-2 text-sm text-gray-500">[{q.question_code}]</span>
              </div>
              <div className="text-gray-700">
                <LaTeXRenderer
                  contentEditable={!!sessionId}
                  onBlur={(e) => handleBlur('TL', q.question_code, 'question_stem', e)}
                  className="focus:outline-none focus:ring-2 focus:ring-primary-300"
                >
                  {q.question_stem}
                </LaTeXRenderer>
              </div>
            </div>
          ))}
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
            {sortedTL.map((q, idx) => (
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
                  {q.explanation && (
                    <div>
                      <span className="font-medium">Hướng dẫn chấm điểm:</span>
                      <div className="text-sm text-gray-600 mt-1">
                        <LaTeXRenderer>{q.explanation}</LaTeXRenderer>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
