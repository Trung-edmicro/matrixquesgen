
import { useMemo } from "react"
import { ArrangeBlock, ClozeBlock, DialogueBlock, ErrorIdentificationBlock, LogicalThinkingBlock,
        PronunciationBlock, SentenceTransformationBlock, SentenceCompletionBlock, SynonymBlock, WordReorderingBlock } from "./EnglishExamPreviewPanel"
export default function EnglishExamTHCSPreviewPanel({ examData,onUpdateExam, selectedQuestions,onToggleQuestionSelection }) {

  const blocks = useMemo(() => {
    return examData?.results || []
  }, [examData])

  if (!blocks.length) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        Chưa có dữ liệu đề thi
      </div>
    )
  }

  const handleUpdateBlock = (blockIndex, updatedQuestion) => {
  // 1. Tạo bản sao của toàn bộ results
  const newResults = [...examData.results];
  
  // 2. Lấy ra block (nhóm câu hỏi) cần update
  const targetBlock = { ...newResults[blockIndex] };
//    if (!targetBlock.parsed) targetBlock.parsed = {};

 if (updatedQuestion.passage ) {
    targetBlock.parsed = {
      ...targetBlock.parsed,
      ...updatedQuestion // Ghi đè toàn bộ passage, passage_title và questions mới
    };
  } 
  // 3. Kiểm tra nếu block này có chứa mảng questions (đa số các block Tiếng Anh)
  if (targetBlock.parsed && Array.isArray(targetBlock.parsed.questions)) {
    const newQuestions = targetBlock.parsed.questions.map((q) => {
      // So sánh theo q.number (ví dụ: Câu 1, Câu 2...)
      return q.number === updatedQuestion.number ? updatedQuestion : q;
    });

    // Cập nhật lại mảng questions trong parsed
    targetBlock.parsed = {
      ...targetBlock.parsed,
      questions: newQuestions,
    };
  } else {
    // Trường hợp block đặc thù không có mảng questions (ví dụ: ARRANGE dạng đơn)
    targetBlock.parsed = {
      ...targetBlock.parsed,
      ...updatedQuestion
    };
  }

  // 4. Ghi lại block đã sửa vào mảng results
  newResults[blockIndex] = targetBlock;

  // 5. Cập nhật state tổng lên cha (GenerateExamPage)
  onUpdateExam({
    ...examData,
    results: newResults
  });
};


  return (
    <div className="h-full overflow-auto bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto bg-white shadow border rounded-lg p-10 text-[15px] leading-7 font-[Times_New_Roman]">

        {/* TITLE */}
        <h1 className="text-center text-xl font-bold mb-8">
          ĐỀ THI TIẾNG ANH
        </h1>

        {blocks.map((block, index) => {
          const data = block.parsed

          const prevType = blocks[index - 1]?.type
          const isFirstOfGroup = prevType !== block.type

          switch (block.type) {

            case "ARRANGE":
              return (
                <ArrangeBlock
                  key={index}
                  data={data}
                  onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "SENTENCE_COMPLETION":
              return (
                <SentenceCompletionBlock
                  key={index}
                  data={data}
                  onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }                  
                />
              )

            case "SYNONYM_ANTONYM":
              return (
                <SynonymBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "ERROR_IDENTIFICATION":
              return (
                <ErrorIdentificationBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "SENTENCE_TRANSFORMATION":
              return (
                <SentenceTransformationBlock
                  key={index}
                  data={data}
                  onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "PRONUNCIATION_STRESS":
              return (
                <PronunciationBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "DIALOUGE_COMPLETION":
              return (
                <DialogueBlock
                  key={index}
                  data={data}
                  onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "LOGICAL_THINKING":
              return (
                <LogicalThinkingBlock
                  key={index}
                  data={data}
                  onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "WORD_REORDERING":
              return (
                <WordReorderingBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "GAP":
            case "RC":
            case "CLOZE":
              return (
                <ClozeBlock
                  key={index}
                  data={data}
                  type={block.type}
                  onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )

            case "ORDER_OPENING":
              return (
                <OpeningAndOrderingBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )
           case "ORDER_CLOSING":
              return (
                <OrderingAndClosingBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )
            case "COMPLETE_SENTENCE_GIVEN_WORDS":
                return (
                  <CompleteSentenceGivenWordsMCQBlock
                    key={index}
                    data={data}
                    showInstruction={isFirstOfGroup}
                  />
                )
            case "ESSAY_REWRITING_SENTENCES":
              return (
                <EssaySentenceRewritingBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )
            case "ESSAY_COMBINE_SENTENCES":
              return (
                <EssayCombineSentencesBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )
            case "ESSAY_WORD_ORDERING":
              return (
                <EssayWordOrderingBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )
            case "ESSAY_WORD_FORM_SENTENCE_COMPLETION":
              return (
                <EssayWordFormCompletionBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )
            case "ESSAY_WORD_PROMPT_SENTENCE":
              return (
                <EssayWordPromptSentenceCompletionBlock
                  key={index}
                  data={data}
                                    onUpdate={handleUpdateBlock}
                  showInstruction={isFirstOfGroup}
                  selectedQuestions={selectedQuestions}
                  onToggleQuestionSelection={
                    onToggleQuestionSelection
                  }
                />
              )
           }
        })}

      </div>
    </div>
  )
 
}


export function CompleteSentenceGivenWordsMCQBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== "object") return null

  return (
    <div className="mb-10">

      {/* Title */}
      {showInstruction && (
        <>
          <p className="font-bold mb-6">
            Mark the letter A, B, C, or D on your answer sheet to indicate the sentence that is BEST written from the words/phrases given.
          </p>
        </>
      )}

      {data.questions.map((q) => (
        <div key={q.number} className="mb-8">

          {/* Given words */}
          <p className="mb-2">
              Question {q.number}. {q.given_words}
          </p>

          {/* Options */}
        <div className="pl-6 space-y-1">
          <p>A. {q.options.option_A}</p>
          <p>B. {q.options.option_B}</p>
          <p>C. {q.options.option_C}</p>
          <p>D. {q.options.option_D}</p>
        </div>

          {/* Answer */}
          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>

            <p className="font-semibold">
              Chọn {q.correct_option}
            </p>

            {q.knowledge && (
              <p className="mt-1">
                <strong>Kiến thức:</strong> {q.knowledge}
              </p>
            )}

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>

            <p className="mt-2">
              <strong>Câu đúng:</strong>{" "}
              <span className="italic">{q.full_sentence}</span>
            </p>

            <p className="mt-2">
              <strong>Tạm dịch:</strong> {q.translation}
            </p>
          </div>

        </div>
      ))}

    </div>
  )
}

export function EssayWordPromptSentenceCompletionBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== "object") return null

  return (
    <div className="mb-10">

      {/* Title */}
      {showInstruction && (
        <p className="font-bold mb-6">
          Complete sentence by using the words or phrases below, adding more words if necessary.
        </p>
      )}

      {data.questions.map((q) => {

        // dynamic blank width theo độ dài prompt
        const baseLength = q.given_prompts.length * 0.6
        const width = Math.min(Math.max(baseLength, 50), 110)

        return (
          <div key={q.number} className="mb-8">

            {/* Given prompts */}
            <p className="tracking-wide">
              <strong>Question {q.number}.</strong> {q.given_prompts}
            </p>

            {/* Blank */}
            <p className="mt-1 flex items-center flex-wrap">
              <span>→</span>
              <span
                className="inline-block border-b border-black ml-2"
                style={{ width: `${width}ch`, minWidth: "280px" }}
              ></span>
            </p>

            {/* Answer */}
            <div className="mt-3 pl-4">

              <p className="font-semibold">Lời giải</p>

              <p className="mt-1">
                <strong>Đáp án:</strong> {q.answer}
              </p>

              {q.knowledge && (
                <p className="mt-2">
                  <strong>Kiến thức:</strong> {q.knowledge}
                </p>
              )}

              <p className="mt-1 whitespace-pre-line">
                {q.explanation}
              </p>

              <p className="mt-2">
                <strong>Câu hoàn chỉnh:</strong>{" "}
                <span className="italic">{q.answer}</span>
              </p>

              <p className="mt-2">
                <strong>Tạm dịch:</strong> {q.translation}
              </p>

            </div>

          </div>
        )
      })}

    </div>
  )
}


export function EssayWordFormCompletionBlock({ data }) {
  if (!data || typeof data !== "object") return null

  // Xác định title cho cả block (chuẩn đề thi: không mix dạng)
 const firstQuestion = data.questions?.[0]

  // Xác định dạng bài
  const isMultiBlank = firstQuestion?.given_words.length >= 2

  // Logic hiển thị instruction
  const showInstruction = isMultiBlank

  // Title tương ứng
  const title = isMultiBlank
    ? "Complete each sentence below, using the correct form of the verbs in the brackets."
    : "Complete the sentence below by filling each blank with the correct form of the word provided."

  return (
    <div className="mb-10">

      {/* Title */}
      {showInstruction && (
        <p className="font-bold mb-6">{title}</p>
      )}

      {data.questions.map((q) => {

        // Render sentence với blank đẹp hơn
       const renderSentence = () => {
        const parts = q.sentence.split("______")

        return parts.map((part, i) => (
          <span key={i}>
            {part}

            {i < parts.length - 1 && (
              <>
                {/* Given word tương ứng */}
                <span className="mx-1">
                  (<span className="font-bold">
                    {q.given_words[i]}
                  </span>)
                </span>

                {/* Blank */}
                <span className="inline-block border-b border-black mx-1 min-w-[100px] align-middle"></span>
              </>
            )}
          </span>
        ))
      }

        // Tạo câu hoàn chỉnh
        const filledSentence = (() => {
          let result = q.sentence
          q.answers.forEach(ans => {
            result = result.replace("______", ans)
          })
          return result
        })()

        return (
          <div key={q.number} className="mb-8">

            {/* Question */}
            {/* <p className="font-semibold">
              Question {q.number}.
            </p> */}

            <p> <strong>Question {q.number}.</strong> {renderSentence()}</p>

            {/* Answer */}
            <div className="mt-3 pl-4">

              <p className="font-semibold">Lời giải</p>

              <p className="mt-1">
                <strong>Đáp án:</strong> {q.answers.join(" và ")}
              </p>

              {q.knowledge && (
                <p className="mt-1">
                  <strong>Kiến thức:</strong> {q.knowledge}
                </p>
              )}

              {/* Giải thích từng blank */}
              <div className="mt-2 space-y-1">
                {Object.entries(q.explanation).map(([key, value]) => (
                  value && (
                    <p key={key}>
                      - {value}
                    </p>
                  )
                ))}
              </div>

              {/* Câu hoàn chỉnh */}
              <p className="mt-2">
                <strong>Câu hoàn chỉnh:</strong>{" "}
                <span className="italic">{filledSentence}</span>
              </p>

              {/* Translation */}
              <p className="mt-2">
                <strong>Tạm dịch:</strong> {q.translation}
              </p>

            </div>

          </div>
        )
      })}

    </div>
  )
}

export function EssayWordOrderingBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== "object") return null

  return (
    <div className="mb-10">

      {/* Title */}
      {showInstruction && (
        <p className="font-bold mb-6">
          Rearrange the given words or phrases to make a meaningful sentence.
        </p>
      )}

      {data.questions.map((q) => {
        // dynamic blank width
        const baseLength = q.given_words.length * 0.6
        const width = Math.min(Math.max(baseLength, 40), 100)

        return (
          <div key={q.number} className="mb-8">


            <p> <strong>Question {q.number}.</strong> {q.given_words}</p>

            {/* Blank */}
            <p className="mt-1 flex items-center flex-wrap">
              <span>→</span>
              <span
                className="inline-block border-b border-black ml-2"
                style={{ width: `${width}ch`, minWidth: "250px" }}
              ></span>
            </p>

            {/* Answer */}
            <div className="mt-3 pl-4">
              <p className="font-semibold">Lời giải</p>

              <p className="mt-1">
                <strong>Đáp án:</strong> {q.answer}
              </p>

              {q.structure && (
                <p className="mt-1">
                  <strong>Cấu trúc:</strong> {q.structure}
                </p>
              )}

              <p className="mt-1">
                <strong>Câu hoàn chỉnh:</strong> {q.full_sentence}
              </p>

              <p className="mt-1 whitespace-pre-line">
                {q.explanation}
              </p>

              <p className="mt-2">
                <strong>Tạm dịch:</strong> {q.translation}
              </p>
            </div>

          </div>
        )
      })}

    </div>
  )
}


export function EssayCombineSentencesBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== "object") return null

  return (
    <div className="mb-10">

      {/* Title */}
      {showInstruction && (
        <p className="font-bold mb-6">
          Combine each pair of sentences below to make a complete sentence.
        </p>
      )}

      {data.questions.map((q) => {
        // dynamic blank width
        const baseLength =
          (q.sentence_1.length + q.sentence_2.length) * 0.6
        const width = Math.min(Math.max(baseLength, 40), 100)

        return (
          <div key={q.number} className="mb-8">

            {/* Question */}
            <p>
             <strong>Question {q.number}.</strong> {q.sentence_1} {q.sentence_2} <strong>({q.given_word})</strong>
            </p>



            {/* Blank */}
            <p className="mt-1 flex items-center flex-wrap">
              <span>→</span>
              <span
                className="inline-block border-b border-black ml-2"
                style={{ width: `${width}ch`, minWidth: "250px" }}
              ></span>
              <span>.</span>
            </p>

            {/* Answer */}
            <div className="mt-3 pl-4">
              <p className="font-semibold">Lời giải</p>

              <p className="mt-1">
                <strong>Đáp án:</strong> {q.combined_sentence}
              </p>

              {q.knowledge && (
                <p className="mt-1">
                  <strong>Cấu trúc:</strong> {q.knowledge}
                </p>
              )}

              <p className="mt-1 whitespace-pre-line">
                {q.explanation}
              </p>

              <p className="mt-2">
                <strong>Tạm dịch:</strong> {q.translation}
              </p>
            </div>

          </div>
        )
      })}

    </div>
  )
}

export function EssaySentenceRewritingBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== "object") return null

  return (
    <div className="mb-10">

      {/* Title */}
      {showInstruction && (
        <p className="font-bold mb-6">
          Rewrite the sentence so that its meaning stays the same, using the words given.
        </p>
      )}

      {data.questions.map((q) => (
        <div key={q.number} className="mb-8">


          <p>
              <strong>Question {q.number}.</strong> {q.original_sentence} <strong>({q.given_word})</strong>
          </p>

          <p className="mt-1">
            → {q.rewrite_prompt} ___________________________________________________
          </p>

          {/* Answer + Explanation */}
          <div className="mt-3 pl-4">

            <p className="font-semibold">Lời giải</p>

            <p className="mt-1">
              <strong>Đáp án:</strong> {q.answer}
            </p>

            {q.knowledge && (
              <p className="mt-1">
                <strong>Cấu trúc:</strong> {q.knowledge}
              </p>
            )}

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>

            {/* Translation */}
            <div className="mt-2">
              <p>
                <strong>Câu gốc:</strong> {q.translation.original}
              </p>
              <p>
                <strong>=</strong> {q.translation.rewritten}
              </p>
            </div>

          </div>

        </div>
      ))}

    </div>
  )
}


export function OpeningAndOrderingBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== "object") return null

  const openingQuestionNumber = data.question_groups?.[0]?.opening_question?.question_number;

  const orderingQuestionNumber = data.question_groups?.[0]?.ordering_question?.question_number;

  return (
    <div className="mb-10">
      {showInstruction && (
        <p className="font-bold italic mb-6">
          Mark the letter A, B, C or D on your answer sheet to indicate the correct answer to each of the following questions from {openingQuestionNumber} to {orderingQuestionNumber}.
        </p>
      )}

      {data.question_groups.map((group, idx) => (
        <div key={idx} className="mb-10">

          {/* Shared stem */}
          <div className="mb-4">
            <p className="italic">
              {group.shared_stem.text}
            </p>
          </div>

          {/* Question 17 - Opening sentence */}
          <div className="mb-6">
            <p className="font-bold mb-2">
               Question {group.opening_question.question_number}. Choose the TOPIC SENTENCE that can BEGIN the text most appropriately.
            </p>

            <div className="pl-6 space-y-1">
              <p>A. {group.opening_question.options.A}</p>
              <p>B. {group.opening_question.options.B}</p>
              <p>C. {group.opening_question.options.C}</p>
              <p>D. {group.opening_question.options.D}</p>
            </div>

            {/* Answer */}
            <div className="mt-3 pl-6">
              <p className="font-semibold">
                Chọn {group.opening_question.answer}
              </p>

               <p className="font-semibold">
                ####
              </p>

              <p className="font-semibold">Lời giải</p>
              <p className="font-bold">
                Câu hỏi: Hãy chọn CÂU CHỦ ĐỀ có thể BẮT ĐẦU đoạn văn một cách phù hợp nhất.
              </p>
              <p className="whitespace-pre-line">
                {group.opening_question.explanation.reasoning}
              </p>

              <p className="mt-1">
                → {group.opening_question.explanation.correct_sentence}
              </p>
            </div>
          </div>

          {/* Question 18 - Ordering */}
          <div>
            {/* <p className="font-semibold">
              Question {group.ordering_question.question_number}:
            </p> */}

            <p  className="font-bold mb-2">
             Question {group.ordering_question.question_number}. Put the sentences (a-c) in the correct order, then fill in the blank to make a logical text. 
            </p>

            {/* Sentences */}
            <div className="pl-6 mb-2 space-y-1">
              <p>a. {group.ordering_question.sentences.a}</p>
              <p>b. {group.ordering_question.sentences.b}</p>
              <p>c. {group.ordering_question.sentences.c}</p>
            </div>

            {/* Options */}
            <div className="pl-6 space-y-1">
              <p>A. {group.ordering_question.options.A}</p>
              <p>B. {group.ordering_question.options.B}</p>
              <p>C. {group.ordering_question.options.C}</p>
              <p>D. {group.ordering_question.options.D}</p>
            </div>

            {/* Answer */}
            <div className="mt-3 pl-6">
               <p className="font-semibold">
                Chọn {group.ordering_question.answer}
              </p>

              <p className="font-semibold">Lời giải</p>

              <p className="font-bold">
               Câu hỏi: Hãy sắp xếp các câu (a-c) theo thứ tự đúng, sau đó điền vào chỗ trống để tạo thành một đoạn văn logic.
              </p>

              <div className="whitespace-pre-line mt-1">
                {group.ordering_question.explanation.steps.map((step, i) => (
                  <p key={i}>- {step}</p>
                ))}
              </div>

              <p className="mt-2">
                <strong>Đoạn văn hoàn chỉnh:</strong>
              </p>
              <p>
                {group.ordering_question.explanation.full_passage}
              </p>

              <p className="font-bold mt-2">
                <strong>Tạm dịch:</strong>
              </p>
              <p>
                {group.ordering_question.explanation.translation}
              </p>
            </div>
          </div>

        </div>
      ))}
    </div>
  )
}


export function OrderingAndClosingBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== "object") return null

  // Dynamic range (vd: 17 → 18)
  const firstGroup = data.question_groups?.[0]
  const lastGroup = data.question_groups?.[data.question_groups.length - 1]

  const start = firstGroup?.ordering_question?.question_number
  const end = lastGroup?.closing_question?.question_number

  return (
    <div className="mb-10">

      {/* Title */}
      {showInstruction && (
        <p className="font-bold italic mb-6">
          Mark the letter A, B, C or D on your answer sheet to indicate the correct answer to each of the following questions from {start} to {end}.
        </p>
      )}

      {data.question_groups.map((group, idx) => (
        <div key={idx} className="mb-10">

          {/* Question 17 - Ordering */}
          <div className="mb-6">
           

            <p className="font-bold mb-2">
              Question {group.ordering_question.question_number}. Put the sentences (a-c) in the correct order, then fill in the blank to make a logical text.
            </p>

            {/* Passage intro */}
            <p className="mb-3">
              {group.ordering_question.passage_intro}
            </p>

            {/* Sentences */}
            <div className="pl-6 mb-2 space-y-1">
              <p>a. {group.ordering_question.sentences.a}</p>
              <p>b. {group.ordering_question.sentences.b}</p>
              <p>c. {group.ordering_question.sentences.c}</p>
            </div>

            {/* Options */}
            <div className="pl-6 space-y-1">
              <p>A. {group.ordering_question.options.A}</p>
              <p>B. {group.ordering_question.options.B}</p>
              <p>C. {group.ordering_question.options.C}</p>
              <p>D. {group.ordering_question.options.D}</p>
            </div>

            {/* Answer */}
            <div className="mt-3 pl-6">
                <p className="font-semibold">
                  Chọn {group.closing_question.answer}
                </p>

                <p className="font-semibold mt-2">Lời giải</p>

                {group.closing_question.knowledge && (
                  <p>Kiến thức: {group.closing_question.knowledge}</p>
                )}

                <p className="mt-1">
                  Câu hỏi: Chọn câu có thể kết thúc đoạn văn (ở Câu {group.ordering_question.question_number}) một cách thích hợp nhất.
                </p>

                <div className="mt-2 space-y-1">
                  <p>- {group.ordering_question.options.A}: {group.closing_question.explanation.option_analysis.A}</p>
                  <p>- {group.ordering_question.options.B}: {group.closing_question.explanation.option_analysis.B}</p>
                  <p>- {group.ordering_question.options.C}: {group.closing_question.explanation.option_analysis.C}</p>
                  <p>- {group.ordering_question.options.D}: {group.closing_question.explanation.option_analysis.D}</p>
                </div>

                <p className="mt-2">
                  {group.closing_question.explanation.reasoning}
                </p>
            </div>
          </div>

          {/* Question 18 - Closing sentence */}
          <div>
            {/* <p className="font-semibold">
              Question {group.closing_question.question_number}:
            </p> */}

            <p className="font-bold mb-2">
              Question {group.closing_question.question_number}. Choose the sentence that can end the text (in Question {group.ordering_question.question_number} ) most appropriately.
            </p>

            {/* Options */}
            <div className="pl-6 space-y-1">
              <p>A. {group.closing_question.options.A}</p>
              <p>B. {group.closing_question.options.B}</p>
              <p>C. {group.closing_question.options.C}</p>
              <p>D. {group.closing_question.options.D}</p>
            </div>

            {/* Answer */}
           <div className="mt-3 pl-6">
            <p className="font-semibold">
              Chọn {group.closing_question.answer}
            </p>

            <p className="font-semibold mt-2">Lời giải</p>

            {group.closing_question.knowledge && (
              <p>Kiến thức: {group.closing_question.knowledge}</p>
            )}

            <p className="mt-1">
              Câu hỏi: Chọn câu có thể kết thúc đoạn văn (ở Câu {group.ordering_question.question_number}) một cách thích hợp nhất.
            </p>

            <div className="mt-2 space-y-1">
              <p>- Câu A: {group.closing_question.explanation.option_analysis.A}</p>
              <p>- Câu B: {group.closing_question.explanation.option_analysis.B}</p>
              <p>- Câu C: {group.closing_question.explanation.option_analysis.C}</p>
              <p>- Câu D: {group.closing_question.explanation.option_analysis.D}</p>
            </div>

            <p className="mt-2">
              {group.closing_question.explanation.reasoning}
            </p>
          </div>
          </div>

        </div>
      ))}

    </div>
  )
}
