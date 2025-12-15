import { useState } from 'react'

export default function ExamPreviewPanel({ examData, isGenerating, sessionId }) {
  const [activeTab, setActiveTab] = useState('questions')

  const tabs = [
    { id: 'questions', label: 'Đề' },
    { id: 'answers', label: 'Đáp án' }
  ]

  // Get questions from examData structure
  const questions = examData?.questions || { TN: [], DS: [] }
  const metadata = examData?.metadata || {}

  return (
    <div className="h-full panel flex flex-col overflow-hidden">
      {/* Tabs */}
      <div className="border-b border-gray-200 flex">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary-600 text-primary-700'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {isGenerating ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin mb-2"></div>
              <div className="text-sm text-gray-600">Đang sinh câu hỏi...</div>
              {sessionId && (
                <div className="text-xs text-gray-500 mt-2">Session: {sessionId.slice(0, 8)}</div>
              )}
            </div>
          </div>
        ) : examData ? (
          <div className="space-y-4">
            {/* Metadata info */}
            {metadata.total_questions > 0 && (
              <div className="bg-gray-50 p-3 rounded text-xs text-gray-600">
                <div>Tổng: {metadata.total_questions} câu ({metadata.tn_count} TN, {metadata.ds_count} DS)</div>
                {metadata.generated_at && (
                  <div className="text-gray-500 mt-1">
                    Thời gian: {new Date(metadata.generated_at).toLocaleString('vi-VN')}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'questions' && (
              <QuestionsList questions={questions} />
            )}
            {activeTab === 'answers' && (
              <AnswersList questions={questions} />
            )}
          </div>
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

function QuestionsList({ questions }) {
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

  // Sort TN và DS questions
  const sortedTN = [...(questions.TN || [])].sort(sortByQuestionCode)
  const sortedDS = [...(questions.DS || [])].sort(sortByQuestionCode)

  return (
    <div className="space-y-6">
      {/* TN Questions */}
      {sortedTN.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">Phần I: Trắc nghiệm</h3>
          {sortedTN.map((q, idx) => (
            <div key={q.question_code} className="mb-4 text-sm border-b border-gray-100 pb-4">
              <div className="mb-2">
                <span className="font-medium">Câu {idx + 1}</span>
                <span className={`ml-2 px-2 py-0.5 text-xs rounded ${getLevelColor(q.level)}`}>
                  {q.level}
                </span>
                <span className="ml-2 text-xs text-gray-500">[{q.question_code}]</span>
              </div>
              <div className="mb-2 text-gray-700">{q.question_stem}</div>
              <div className="space-y-1 pl-4">
                {Object.entries(q.options || {}).map(([key, value]) => (
                  <div 
                    key={key} 
                    className={q.correct_answer === key ? 'text-red-600 font-medium' : 'text-gray-600'}
                  >
                    {key}. {value}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* DS Questions */}
      {sortedDS.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">Phần II: Đúng/Sai</h3>
          {sortedDS.map((q, idx) => (
            <div key={q.question_code} className="mb-6 text-sm border-b border-gray-100 pb-4">
              <div className="mb-2">
                <span className="font-medium">Câu {idx + 1}</span>
                <span className="ml-2 text-xs text-gray-500">[{q.question_code}]</span>
              </div>
              <div className="mb-3 text-gray-600 italic text-xs bg-gray-50 p-2 rounded">
                {q.source_text}
              </div>
              <div className="space-y-2 pl-4">
                {Object.entries(q.statements || {}).map(([key, stmt]) => (
                  <div key={key}>
                    <span className={`px-2 py-0.5 text-xs rounded ${getLevelColor(stmt.level)}`}>
                      {stmt.level}
                    </span>
                    <span className={`ml-2 ${stmt.correct_answer ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                      {key}. {stmt.text}
                    </span>
                  </div>
                ))}
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

  // Sort TN và DS questions
  const sortedTN = [...(questions.TN || [])].sort(sortByQuestionCode)
  const sortedDS = [...(questions.DS || [])].sort(sortByQuestionCode)

  return (
    <div className="space-y-6">
      {sortedTN.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">Phần I: Trắc nghiệm</h3>
          <div className="text-sm space-y-2">
            {sortedTN.map((q, idx) => (
              <div key={q.question_code} className="border-b border-gray-100 pb-2">
                <div className="flex items-start gap-2 mb-1">
                  <span className="font-medium">Câu {idx + 1}:</span>
                  <span className="text-red-600 font-medium">{q.correct_answer}</span>
                </div>
                {q.explanation && (
                  <div className="text-xs text-gray-600 pl-16">{q.explanation}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {sortedDS.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">Phần II: Đúng/Sai</h3>
          <div className="text-sm space-y-3">
            {sortedDS.map((q, idx) => (
              <div key={q.question_code} className="border-b border-gray-100 pb-3">
                <div className="font-medium mb-2">Câu {idx + 1}:</div>
                <div className="pl-4 space-y-1">
                  {Object.entries(q.statements || {}).map(([key, stmt]) => (
                    <div key={key} className="text-xs">
                      <span className="font-medium">{key}.</span>{' '}
                      <span className="text-red-600">{stmt.correct_answer ? 'Đúng' : 'Sai'}</span>
                      {q.explanation?.[key] && (
                        <div className="text-gray-600 pl-4 mt-1">{q.explanation[key]}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
