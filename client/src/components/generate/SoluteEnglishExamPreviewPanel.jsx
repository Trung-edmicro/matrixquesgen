import { useMemo } from "react"

export default function SoluteEnglishPreviewPanel({ examData }) {
  // Xử lý dữ liệu mảng lồng [[...]] từ data.json
  const blocks = useMemo(() => {
    if (Array.isArray(examData?.results) && Array.isArray(examData.results[0])) {
      return examData.results[0];
    }
    // Trường hợp data đã được flatten sẵn
    if (Array.isArray(examData?.results)) return examData.results;
    return [];
  }, [examData]);

  if (!blocks.length) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 italic">
        Đang tải dữ liệu hoặc không có dữ liệu đề thi...
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto bg-gray-100 p-4 lg:p-8">
      <div className="max-w-4xl mx-auto bg-white shadow-xl border rounded-md p-8 lg:p-12 text-[15px] leading-7 font-[Times_New_Roman] text-gray-900">
        
        <h1 className="text-center text-2xl font-bold mb-10 uppercase border-b-2 border-gray-900 pb-4">
          CHI TIẾT LỜI GIẢI ĐỀ THI TIẾNG ANH
        </h1>

        {blocks.map((block, index) => {
          const type = block.type;
          const data = block.parsed;

          // Phân loại render dựa trên block.type
          switch (type) {
            case "GAP":
            case "RC":
            case "CLOZE":
              return <PassageBlock key={index} block={block} />
            
            case "ARRANGE":
              return <ArrangeBlock key={index} block={block} />

            case "SENTENCE_COMPLETION":
            case "SYNONYM_ANTONYM":
            case "ERROR_IDENTIFICATION":
            case "SENTENCE_TRANSFORMATION":
            case "WORD_REORDERING":
              return <QuestionListBlock key={index} block={block} />

            case "PRONUNCIATION_STRESS":
              return <PronunciationBlock key={index} block={block} />

            case "DIALOUGE_COMPLETION":
              return <DialogueBlock key={index} block={block} />

            case "LOGICAL_THINKING":
              return <LogicalThinkingBlock key={index} block={block} />

            default:
              return <QuestionListBlock key={index} block={block} />
          }
        })}
      </div>
    </div>
  )
}

/* ==========================================================================
   SUB-COMPONENTS (BLOCKS)
   ========================================================================== */

/**
 * 1. Khối Bài Đọc (GAP, RC, CLOZE)
 * Cấu trúc: titleQuestion -> Instruction -> Passage -> Questions
 */
function PassageBlock({ block }) {
  const { titleQuestion, text_type_en, parsed } = block;
  return (
    <div className="mb-14 border-b border-gray-200 pb-8 last:border-0">
      <div className="font-bold text-lg mb-2">{titleQuestion}</div>
      <p className="italic mb-6 text-gray-700">{text_type_en}</p>

      <div className="bg-gray-50 p-6 rounded-lg mb-8 border-l-4 border-blue-500">

         <h3
          className="text-center font-bold text-lg mb-4 uppercase"
          dangerouslySetInnerHTML={{ __html: parsed.passage_title }}
        />
        
            <div
      className="text-justify"
      dangerouslySetInnerHTML={{ __html: parsed.passage }}
    />
      </div>

      <div className="space-y-10">
        {parsed.questions?.map((q) => <SingleQuestion key={q.number} q={q} />)}
      </div>
    </div>
  )
}

/**
 * 2. Khối Danh sách câu hỏi rời (Sentence Completion, Synonym, Error, v.v.)
 * Cấu trúc: titleQuestion -> Instruction -> List of Questions
 */
function QuestionListBlock({ block }) {
  const { titleQuestion, text_type_en, parsed } = block;
  return (
    <div className="mb-14 border-b border-gray-200 pb-8 last:border-0">
      <div className="text-blue-800 font-bold text-lg mb-2">{titleQuestion}</div>
      {text_type_en && <p className="italic mb-6 text-gray-700">{text_type_en}</p>}
      
      <div className="space-y-10">
        {parsed.questions?.map((q) => (
          <SingleQuestion key={q.number} q={q} isErrorType={block.type === "ERROR_IDENTIFICATION"} />
        ))}
      </div>
    </div>
  )
}

/**
 * 3. Khối Sắp xếp (ARRANGE) - Cấu trúc đặc thù theo data.json
 */
function ArrangeBlock({ block }) {
  const { titleQuestion, text_type_en, parsed } = block;
  return (
    <div className="mb-14 border-b border-gray-200 pb-8 last:border-0">
      <div className="font-bold text-lg mb-2">{titleQuestion}</div>
      <p className="italic mb-4 text-gray-700">{text_type_en}</p>
      
      <div className="pl-2">
        <p className="font-bold mb-3">Question {parsed.question_number}:</p>
        <div className="space-y-1 mb-4 pl-4">
          <p>A. {parsed.option_a}</p>
          <p>B. {parsed.option_b}</p>
          <p>C. {parsed.option_c}</p>
          <p>D. {parsed.option_d}</p>
        </div>

        <div className="bg-green-50 p-4 rounded border border-green-100">
          <p className="text-green-800 font-bold mb-2"> Chọn {parsed.answer}</p>
          <div className="space-y-3">
            <div>
              <p className="font-bold  text-sm">Thứ tự đúng:</p>
              {parsed.solution_lines?.map((l, i) => <p key={i} className="text-sm italic">{l}</p>)}
            </div>
            <div>
              <p className="font-bold text-sm">Tạm dịch:</p>
              {parsed.translation_lines?.map((l, i) => <p key={i} className="text-sm">{l}</p>)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * 4. Khối Phát âm / Trọng âm (PRONUNCIATION_STRESS)
 */
function PronunciationBlock({ block }) {
  return (
    <div className="mb-14 border-b border-gray-200 pb-8 last:border-0">
      <div className="text-blue-800 font-bold text-lg mb-2">{block.titleQuestion}</div>
      <div className="space-y-8">
        {block.parsed.questions?.map((q) => (
          <div key={q.number}>
            <p className="font-bold">Question {q.number}:</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pl-4 my-2">
               <p dangerouslySetInnerHTML={{ __html: "A. " + q.option_a }} />
               <p dangerouslySetInnerHTML={{ __html: "B. " + q.option_b }} />
               <p dangerouslySetInnerHTML={{ __html: "C. " + q.option_c }} />
               <p dangerouslySetInnerHTML={{ __html: "D. " + q.option_d }} />
            </div>
            <div className="bg-green-50 p-3 rounded">
               <p className="font-bold text-green-800">Chọn {q.answer}</p>
               <p className="text-sm">{q.explanation}</p>
               {q.details?.map((d, i) => (
                 <p key={i} className="text-xs text-gray-600 italic">
                   {d.word} {d.ipa} ({d.pos}): {d.meaning}
                 </p>
               ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * 5. Khối Hội thoại (DIALOUGE_COMPLETION)
 */
function DialogueBlock({ block }) {
  return (
    <div className="mb-14 border-b border-gray-200 pb-8 last:border-0">
      <div className="text-blue-800 font-bold text-lg mb-2">{block.titleQuestion}</div>
      <div className="space-y-8">
        {block.parsed.questions?.map((q) => (
          <div key={q.number}>
            <p className="font-bold">Question {q.number}:</p>
            <div className="bg-gray-50 p-3 rounded mb-2 italic">
              {q.speaker_a && <p><b>A:</b> {q.speaker_a}</p>}
              {q.speaker_b && <p><b>B:</b> {q.speaker_b}</p>}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-1 pl-4 mb-2">
              <p>A. {q.option_a}</p><p>B. {q.option_b}</p>
              <p>C. {q.option_c}</p><p>D. {q.option_d}</p>
            </div>
            <div className="bg-green-50 p-3 rounded text-sm">
              <p className="font-bold text-green-800">Chọn {q.answer}</p>
              <p>{q.explanation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * 6. Khối Tư duy logic (LOGICAL_THINKING)
 */
function LogicalThinkingBlock({ block }) {
  return (
    <div className="mb-14 border-b border-gray-200 pb-8 last:border-0">
      <div className="text-blue-800 font-bold text-lg mb-4 uppercase">{block.titleQuestion}</div>
      <div className="space-y-12">
        {block.parsed.questions?.map((q) => (
          <div key={q.number} className="border-l-2 border-gray-100 pl-4">
            <p className="font-bold text-gray-800 mb-2 text-base">Question {q.number}:</p>
            {q.scenario && <p className="mb-2 text-gray-700 leading-relaxed">{q.scenario}</p>}
            {q.question && <p className="font-semibold mb-3">{q.question}</p>}
            
            <div className="grid grid-cols-1 gap-1 mb-4 pl-4 italic">
              <p>A. {q.option_a}</p><p>B. {q.option_b}</p>
              <p>C. {q.option_c}</p><p>D. {q.option_d}</p>
            </div>

            <div className="bg-green-50 p-4 rounded border border-green-100">
              <p className="text-green-800 font-bold mb-1"> Chọn {q.answer}</p>
              <p className="text-gray-700 mb-3">{q.explanation}</p>
              {q.translation && (
                <div className="text-xs text-gray-500 border-t border-green-200 pt-2">
                  <p className="font-bold uppercase">Bản dịch tình huống:</p>
                  <p>{q.translation.scenario || q.translation}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ==========================================================================
   UI HELPER COMPONENTS
   ========================================================================== */

/**
 * Hiển thị một câu hỏi Multiple Choice tiêu chuẩn (Dùng cho hầu hết các block)
 */
function SingleQuestion({ q, isErrorType = false }) {
  return (
    <div className="group">
      <p className="font-bold mb-2 text-gray-800">
        Question {q.number}: {q.question_content && <span>{q.question_content}</span>}
      </p>

      {/* Nội dung câu hỏi chính (nếu có, ví dụ trong Sentence Transformation) */}
      {q.question && (
        <p className="mb-3 pl-2 leading-relaxed" dangerouslySetInnerHTML={{ __html: q.question }} />
      )}

      {/* Word list (cho loại Word Reordering) */}
      {q.word_list && <p className="italic mb-3 text-blue-700">({q.word_list})</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 mb-4 pl-4">
        <p><span className="font-semibold">A.</span> {q.option_a}</p>
        <p><span className="font-semibold">B.</span> {q.option_b}</p>
        <p><span className="font-semibold">C.</span> {q.option_c}</p>
        <p><span className="font-semibold">D.</span> {q.option_d}</p>
      </div>

      <div className="bg-green-50 p-4 rounded border border-green-100 transition-colors group-hover:border-green-300">
        <p className="text-green-800 font-bold mb-1"> Chọn {q.answer}</p>
        
        <div className="text-gray-700 text-[14px] space-y-2">
         <p>
          <span className="font-bold">Giải thích:</span>{" "}
          <span
            dangerouslySetInnerHTML={{ __html: q.explanation }}
          />
        </p>
          
          {isErrorType && q.correction && (
            <p className="text-blue-700 font-bold">Sửa lỗi: {q.correction}</p>
          )}

          {q.quote && (
            <p className="italic bg-white p-2 rounded border border-green-200 text-sm">
              <span className="font-bold ">Trích bài:</span>{" "}
              <span dangerouslySetInnerHTML={{ __html: q.quote }} />
            </p>
          )}

          {q.translation && (
            <p className="text-gray-600 italic">
              <span className="font-bold not-italic">Tạm dịch:</span> {q.translation}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}