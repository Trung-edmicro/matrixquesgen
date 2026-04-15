
import { useMemo } from "react"

export default function EnglishExamPreviewPanel({ examData }) {

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

  return (
    <div className="h-full overflow-auto bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto bg-white shadow border rounded-lg p-10 text-[15px] leading-7 font-[Times_New_Roman]">

        {/* TITLE */}
        <h1 className="text-center text-xl font-bold mb-8">
          ĐỀ THI TIẾNG ANH
        </h1>

        {/* {blocks.map((block, index) => {

          if (block.type === "ARRANGE") {
            return (
              <ArrangeBlock
                key={index}
                data={block.parsed}
              />
            )
          }

          return (
            <ClozeBlock
              key={index}
              data={block.parsed}
            />
          )
        })} */}

        {/* {blocks.map((block, index) => {
          const data = block.parsed
          console.log(">>>>>>> debug {13123131", block.type)

          switch (block.type) {

            case "ARRANGE":
              return <ArrangeBlock key={index} data={data} />

            // case "GAP":
            //   return <ClozeBlock key={index} data={data} />

            case "SENTENCE_COMPLETION":
              return <SentenceCompletionBlock key={index} data={data} />

            case "SYNONYM_ANTONYM":
              return <SynonymBlock key={index} data={data} />

            case "ERROR_IDENTIFICATION":
              return <ErrorIdentificationBlock key={index} data={data} />

            case "SENTENCE_TRANSFORMATION":
              return <SentenceTransformationBlock key={index} data={data} />

            case "PRONUNCIATION_STRESS":
              return <PronunciationBlock key={index} data={data} />

            case "DIALOUGE_COMPLETION":
              return <DialogueBlock key={index} data={data} />

            case "LOGICAL_THINKING":
              return <LogicalThinkingBlock key={index} data={data} />

            case "WORD_REORDERING":
              return <WordReorderingBlock key={index} data={data} />
           case "GAP":
          case "RC":
          case "CLOZE":
            return <ClozeBlock key={index} data={data} type={block.type} />
          }
        })} */}

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
                  showInstruction={isFirstOfGroup}
                />
              )

            case "SENTENCE_COMPLETION":
              return (
                <SentenceCompletionBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )

            case "SYNONYM_ANTONYM":
              return (
                <SynonymBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )

            case "ERROR_IDENTIFICATION":
              return (
                <ErrorIdentificationBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )

            case "SENTENCE_TRANSFORMATION":
              return (
                <SentenceTransformationBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )

            case "PRONUNCIATION_STRESS":
              return (
                <PronunciationBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )

            case "DIALOUGE_COMPLETION":
              return (
                <DialogueBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )

            case "LOGICAL_THINKING":
              return (
                <LogicalThinkingBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
                />
              )

            case "WORD_REORDERING":
              return (
                <WordReorderingBlock
                  key={index}
                  data={data}
                  showInstruction={isFirstOfGroup}
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
                  showInstruction={isFirstOfGroup}
                />
              )
          }
        })}

      </div>
    </div>
  )
}


export function ClozeBlock({ data, type = "GAP", showInstruction= true }) {

  const title = data?.passage_title
  const passage = data?.passage || ""
  const questions = data?.questions || []

  const getInstruction = () => {

    // ✅ CHỈ CLOZE dùng text_type_en
    if (type === "CLOZE") {
      const textType = (data?.text_type_en || "").toLowerCase()

      return `Read the following ${textType} and mark the letter A, B, C or D on your answer sheet to indicate the option that best fits each of the numbered blanks.`
    }

    // ✅ RC: cố định
    if (type === "RC") {
      return "Read the following passage and mark the letter A, B, C or D on your answer sheet to indicate the correct answer to each of the following questions."
    }

    // ✅ GAP: cố định
    return "Read the following passage and mark the letter A, B, C or D on your answer sheet to indicate the option that best fits each of the numbered blank."
  }

  return (
    <div className="mb-12">

      {/* INSTRUCTION */}
      {showInstruction && (
  <p className="font-bold mb-6">
    {getInstruction()}
  </p>
)}

      {/* TITLE */}
      {title && (
        <h2 className="text-center font-bold mb-5">
          {title}
        </h2>
      )}

      {/* PASSAGE */}
      <div className="mb-8 text-justify space-y-2">
        {passage
          .split("\n")
          .filter(line => line.trim())
          .map((line, i) => (
            <p key={i}>{line}</p>
          ))}
      </div>

      {/* QUESTIONS */}
      {questions.map((q) => {

        const options = [
          `A. ${q.option_a}`,
          `B. ${q.option_b}`,
          `C. ${q.option_c}`,
          `D. ${q.option_d}`,
        ]

        const isLong =
          options.join("").length > 120

        return (
          <div key={q.number} className="mb-7">

            <p className="font-semibold">
              Question {q.number}:
            </p>

            <div className="pl-6 mt-1">
              {isLong ? (
                <>
                  <p>{options[0]} &nbsp;&nbsp; {options[1]}</p>
                  <p>{options[2]} &nbsp;&nbsp; {options[3]}</p>
                </>
              ) : (
                <p>
                  {options[0]} &nbsp;&nbsp;
                  {options[1]} &nbsp;&nbsp;
                  {options[2]} &nbsp;&nbsp;
                  {options[3]}
                </p>
              )}
            </div>

            {/* EXPLANATION */}
            <div className="mt-3 pl-6 text-gray-800">
              <p className="font-semibold">Lời giải</p>
              <p className="font-semibold">Chọn {q.answer}</p>

              {q.explanation && (
                <p className="mt-1 whitespace-pre-line">
                  {q.explanation}
                </p>
              )}

              {q.quote && (
                <p
                  className="mt-1"
                  dangerouslySetInnerHTML={{
                    __html: `<b>Trích bài:</b> ${q.quote}`
                  }}
                />
              )}

              {q.translation && (
                <p className="mt-1">
                  <b>Tạm dịch:</b> {q.translation}
                </p>
              )}
            </div>

          </div>
        )
      })}

    </div>
  )
}



export function ArrangeBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== 'object') return null

    const instruction =
    "Mark the letter A, B, C or D on your answer sheet to indicate the best arrangement of utterances or sentences to make a meaningful exchange or text."

  return (
    <div className="mb-12">
      {showInstruction && (
        <p className="font-bold mb-6">
          {instruction}
        </p>
      )}

      {/* QUESTION */}
      <p className="font-semibold">
        Question {data?.question_number ?? 'N/A'}:
      </p>

      {data.question_stem && (
        <p className="mb-3">
          {data.question_stem}
        </p>
      )}

      {/* OPTIONS */}
      <div className="pl-6 mb-4 space-y-1">

        <p>A. {data.option_a}</p>
        <p>B. {data.option_b}</p>
        <p>C. {data.option_c}</p>
        <p>D. {data.option_d}</p>

      </div>

      {/* EXPLANATION */}
      <div className="pl-6">

        <p className="font-semibold">
          Lời giải
        </p>

        <p className="font-semibold">
          Chọn {data.answer}
        </p>

        {data.solution_lines?.map((l, i) => (
          <p key={i}>
            {l}
          </p>
        ))}

        {data.translation_lines?.map((l, i) => (
          <p key={i}>
            <b>Tạm dịch:</b> {l}
          </p>
        ))}

      </div>

    </div>
  )
}

export function SentenceCompletionBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== 'object') return null
  return (
    <div className="mb-10">

      {showInstruction && (
        <p className="font-bold mb-6">
          Sentence completion: Choose A, B, C or D to complete each sentence.
        </p>
      )}

      {data.questions.map(q => (
        <div key={q.number} className="mb-6">
          <p className="font-semibold">
            Question {q.number}:
          </p>

          <p className="mt-1">{q.question}</p>

          <div className="pl-6 mt-2 space-y-1">
            <p>A. {q.option_a}</p>
            <p>B. {q.option_b}</p>
            <p>C. {q.option_c}</p>
            <p>D. {q.option_d}</p>
          </div>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>
            <p className="font-semibold">Chọn {q.answer}</p>

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>

            {q.translation && (
              <p className="mt-1">
                <b>Tạm dịch:</b> {q.translation}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}


// function SynonymBlock({ data }) {
//   if (!data || typeof data !== 'object') return null
//   const type = data.questions?.[0]?.type

//   const title =
//     type === "antonym"
//       ? "Antonyms: Choose A, B, C or D that has the OPPOSITE meaning to the underlined word/phrase in each question."
//       : "Synonyms: Choose A, B, C or D that has the CLOSEST meaning to the underlined word/phrase in each question."

//   return (
//     <div className="mb-10">

//       <p className="font-bold mb-6">
//         {title}
//       </p>

//       {data.questions.map(q => (
//         <div key={q.number} className="mb-6">

//            <p className="font-bold mb-6">
//               {title}
//             </p>

//           <p className="font-semibold">
//             Question {q.number}:
//           </p>

//           <p dangerouslySetInnerHTML={{ __html: q.question }} />

//           <div className="pl-6 mt-2 space-y-1">
//             <p>A. {q.option_a}</p>
//             <p>B. {q.option_b}</p>
//             <p>C. {q.option_c}</p>
//             <p>D. {q.option_d}</p>
//           </div>

//           <div className="mt-3 pl-6">
//             <p className="font-semibold">Lời giải</p>
//             <p className="font-semibold">Chọn {q.answer}</p>

//             <p className="mt-1 whitespace-pre-line">
//               {q.explanation}
//             </p>
//           </div>
//         </div>
//       ))}
//     </div>
//   )
// }

export function SynonymBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== 'object') return null
  const type = data.questions?.[0]?.type

  const title =
    type === "antonym"
      ? "Antonyms: Choose A, B, C or D that has the OPPOSITE meaning to the underlined word/phrase in each question."
      : "Synonyms: Choose A, B, C or D that has the CLOSEST meaning to the underlined word/phrase in each question."

  return (
    <div className="mb-10">

      {/* ✅ TITLE CHỈ 1 LẦN */}
      {/* <p className="font-bold mb-6">
        {title}
      </p> */}
            {showInstruction && (
        <p className="font-bold mb-6">
          {title}
        </p>
      )}

      {data.questions.map(q => (
        <div key={q.number} className="mb-6">

           <p
            dangerouslySetInnerHTML={{
              __html: `<strong>Question ${q.number}.</strong> ${q.question}`
            }}
          />

          <div className="pl-6 mt-2 space-y-1">
            <p>A. {q.option_a}</p>
            <p>B. {q.option_b}</p>
            <p>C. {q.option_c}</p>
            <p>D. {q.option_d}</p>
          </div>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>
            <p className="font-semibold">Chọn {q.answer}</p>

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>
          </div>
        </div>
      ))}

    </div>
  )
}


export function ErrorIdentificationBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== 'object') return null
  return (
    <div className="mb-10">

         {/* <p className="font-bold italic mb-6">
           Mark the letter A, B, C, or D to indicate the underlined part that needs correction in the following questions.
      </p> */}

      {showInstruction && (
      <p className="font-bold italic mb-6">
        Mark the letter A, B, C, or D to indicate the underlined part that needs correction in the following questions.
      </p>
    )}

      {data.questions.map(q => (
        <div key={q.number} className="mb-6">
          <p className="font-semibold">
            Question {q.number}:
          </p>

          <p dangerouslySetInnerHTML={{ __html: q.question }} />

          <div className="pl-6 mt-2 space-y-1">
            <p>A. {q.option_a}</p>
            <p>B. {q.option_b}</p>
            <p>C. {q.option_c}</p>
            <p>D. {q.option_d}</p>
          </div>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>
            <p className="font-semibold">Chọn {q.answer}</p>

            <p>{q.explanation}</p>

            {q.correction && (
              <p><b>Sửa:</b> {q.correction}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}


export function SentenceTransformationBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== 'object') return null

  const type = data.questions?.[0]?.type

  const title =
    type === "combination"
      ? "Sentence combination: Choose A, B, C or D that has the CLOSEST meaning to the given pair of sentences in each question."
      : "Sentence rewriting: Choose A, B, C or D that has the CLOSEST meaning to the given sentence in each question."

  return (
    <div className="mb-10">
     {showInstruction && (
        <p className="font-bold mb-6">
          {title}
        </p>
      )}

      {data.questions.map(q => (
        <div key={q.number} className="mb-6">

          <p className="font-semibold">
            Question {q.number}:
          </p>

          {/* {q.instruction && (
            <p className="italic mb-1">
              {q.instruction}
            </p>
          )} */}

          <p>{q.question}</p>

          <div className="pl-6 mt-2 space-y-1">
            <p>A. {q.option_a}</p>
            <p>B. {q.option_b}</p>
            <p>C. {q.option_c}</p>
            <p>D. {q.option_d}</p>
          </div>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>
            <p className="font-semibold">Chọn {q.answer}</p>
            <p>####</p>
            <p className="whitespace-pre-line">
              {q.explanation}
            </p>
          </div>

        </div>
      ))}

    </div>
  )
}


export function PronunciationBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== 'object') return null
  return (
    <div className="mb-10">
      {/* <p className="font-bold italic mb-6">
        Mark the letter A, B, C or D to indicate the word whose underlined part differs from the other three in pronunciation.
      </p> */}

      {showInstruction && (
      <p className="font-bold italic mb-6">
        Mark the letter A, B, C or D to indicate the word whose underlined part differs from the other three in pronunciation.
      </p>
    )}

      {data.questions.map(q => (
        <div key={q.number} className="mb-6">

          <p className="font-semibold">
            Question {q.number}:
          </p>

          <div className="pl-6 space-y-1">
            <p dangerouslySetInnerHTML={{ __html: "A. " + q.option_a }} />
            <p dangerouslySetInnerHTML={{ __html: "B. " + q.option_b }} />
            <p dangerouslySetInnerHTML={{ __html: "C. " + q.option_c }} />
            <p dangerouslySetInnerHTML={{ __html: "D. " + q.option_d }} />
          </div>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Chọn {q.answer}</p>
            <p>{q.explanation}</p>

            {q.details?.map((d, i) => (
              <p key={i}>
                {d.word} {d.ipa} ({d.pos}): {d.meaning}
              </p>
            ))}
          </div>

        </div>
      ))}

    </div>
  )
}


export function DialogueBlock({ data, showInstruction = true }) {

  const renderText = (val) => {
    if (val === null || val === undefined) return "";
    if (typeof val === "object") {
      // ưu tiên field text nếu có
      if (val.text) return val.text;

      // fallback an toàn
      return JSON.stringify(val);
    }
    return val;
  };

  if (!data?.questions || !Array.isArray(data.questions)) {
    return <div>Invalid data</div>;
  }

  return (
    <div className="mb-10">

      {/* <p className="font-bold mb-6">
        Dialogue completion: Choose A, B, C or D to complete each dialogue.
      </p> */}

      {showInstruction && (
        <p className="font-bold mb-6">
          Dialogue completion: Choose A, B, C or D to complete each dialogue.
        </p>
      )}
      {data.questions.map((q, index) => (
        <div key={q?.number ?? index} className="mb-6">
       
          <p className="font-semibold">
            Question {renderText(q?.number)}:
          </p>

          {q?.speaker_a && (
            <p><b>A:</b> {renderText(q.speaker_a)}</p>
          )}

          {q?.speaker_b && (
            <p><b>B:</b> {renderText(q.speaker_b)}</p>
          )}

          <div className="pl-6 mt-2 space-y-1">
            {q?.option_a && <p>A. {renderText(q.option_a)}</p>}
            {q?.option_b && <p>B. {renderText(q.option_b)}</p>}
            {q?.option_c && <p>C. {renderText(q.option_c)}</p>}
            {q?.option_d && <p>D. {renderText(q.option_d)}</p>}
          </div>

          <div className="mt-3 pl-6">
            {q?.answer && (
              <p className="font-semibold">
                Chọn {renderText(q.answer)}
              </p>
            )}

            {q?.explanation && (
              <p>{renderText(q.explanation)}</p>
            )}
          </div>

        </div>
      ))}
    </div>
  );
}


export function WordReorderingBlock({ data, showInstruction = true }) {
  if (!data || typeof data !== 'object') return null 
  return (
    <div className="mb-10">

      {/* <p className="font-bold italic mb-6">
        Reorder the words given to make correct sentences.
      </p> */}

      {showInstruction && (
      <p className="font-bold italic mb-6">
        Reorder the words given to make correct sentences.
      </p>
    )}

      {data.questions.map(q => (
        <div key={q.number} className="mb-6">

          {/* QUESTION NUMBER */}
          <p className="font-semibold">
            Question {q.number}:
          </p>

          {/* WORD LIST */}
          <p className="mt-1 italic">
            {q.word_list}
          </p>

          {/* OPTIONS */}
          <div className="pl-6 mt-2 space-y-1">
            <p>A. {q.option_a}</p>
            <p>B. {q.option_b}</p>
            <p>C. {q.option_c}</p>
            <p>D. {q.option_d}</p>
          </div>

          {/* EXPLANATION */}
          <div className="mt-3 pl-6 text-gray-800">

            <p className="font-semibold">
              Lời giải
            </p>

            <p className="font-semibold">
              Chọn {q.answer}
            </p>

            {q.explanation && (
              <p className="mt-1 whitespace-pre-line">
                {q.explanation}
              </p>
            )}

            {q.translation && (
              <p className="mt-1">
                <b>Tạm dịch:</b> {q.translation}
              </p>
            )}

          </div>

        </div>
      ))}

    </div>
  )
}


export function LogicalThinkingBlock({ data, showInstruction = true }) {

  const questions = data?.questions || []

  if (!questions.length) return null

  return (
    <div className="mb-12">

      {/* TITLE (chỉ 1 lần) */}
      {/* <p className="font-bold mb-6">
        Logical thinking and problem solving: Choose A, B, C or D to answer each question.
      </p> */}

      {showInstruction && (
          <p className="font-bold mb-6">
            Logical thinking and problem solving: Choose A, B, C or D to answer each question.
          </p>
        )}

      {questions.map(q => (
        <div key={q.number} className="mb-8">

          {/* QUESTION NUMBER */}
          <p className="font-semibold">
            Question {q.number}:
          </p>

          {/* SCENARIO */}
          {q.scenario && (
            <p className="mt-1">
              {q.scenario}
            </p>
          )}

          {/* DIALOGUE */}
          {q.speaker_a && (
            <p className="mt-1">
              {q.speaker_a}
            </p>
          )}

          {q.speaker_b && (
            <p>
              {q.speaker_b}
            </p>
          )}

          {/* QUESTION */}
          {q.question && (
            <p className="mt-1">
              {q.question}
            </p>
          )}

          {/* OPTIONS */}
          <div className="pl-6 mt-2 space-y-1">
            <p>A. {q.option_a}</p>
            <p>B. {q.option_b}</p>
            <p>C. {q.option_c}</p>
            <p>D. {q.option_d}</p>
          </div>

          {/* EXPLANATION */}
          <div className="mt-3 pl-6 text-gray-800">

            <p className="font-semibold">
              Lời giải
            </p>

            <p className="font-semibold">
              Chọn {q.answer}
            </p>

            {q.explanation && (
              <p className="mt-1 whitespace-pre-line">
                {q.explanation}
              </p>
            )}

            {/* TRANSLATION */}
            {q.translation && (
              <div className="mt-2 space-y-1">

                {q.translation.scenario && (
                  <p>
                    <b>Tình huống:</b> {q.translation.scenario}
                  </p>
                )}

                {q.translation.question && (
                  <p>
                    <b>Câu hỏi:</b> {q.translation.question}
                  </p>
                )}

                {q.translation.speaker_a && (
                  <p>{q.translation.speaker_a}</p>
                )}

                {q.translation.speaker_b && (
                  <p>{q.translation.speaker_b}</p>
                )}

              </div>
            )}

          </div>

        </div>
      ))}

    </div>
  )
}