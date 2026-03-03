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
        
        {/* TITLE giống doc.add_heading("ĐỀ THI TIẾNG ANH") */}
        <h1 className="text-center text-xl font-bold mb-6">
          ĐỀ THI TIẾNG ANH
        </h1>

        {blocks.map((block, index) => (
          <div key={index} className="mb-8">

            {/* Instruction - italic */}
            <p className="italic mb-4">
              {renderInstruction(block)}
            </p>

            {/* Raw AI text parse theo đúng logic extract_cloze_sections */}
            <RenderBlockContent block={block} />

            {/* Separator */}
            <div className="text-center my-6">
              ====================
            </div>
          </div>
        ))}

      </div>
    </div>
  )
}

/* ============================= */
/* INSTRUCTION (giống _add_instruction) */
/* ============================= */

function renderInstruction(block) {
  if (block.type === "CLOZE") {
    return `Read the following ${block.title || "text"} and mark the letter A, B, C or D on your answer sheet to indicate the option that best fits each of the numbered blanks.`
  }

  if (block.type === "ARRANGE") {
    return `Mark the letter A, B, C or D on your answer sheet to indicate the best arrangement of utterances or sentences to make a meaningful exchange or text.`
  }

  if (block.type === "RC") {
    return `Read the following ${block.title || "text"} and mark the letter A, B, C or D on your answer sheet to indicate the correct answer to each question.`
  }

  return `Read the following ${block.title || "text"} and mark the letter A, B, C or D on your answer sheet to indicate the option that best fits each blank.`
}

/* ============================= */
/* BLOCK RENDER */
/* ============================= */

function RenderBlockContent({ block }) {

  const raw = block.data || ""

  if (block.type === "ARRANGE") {
    return <RenderArrange raw={raw} />
  }

  return <RenderClozeGapRC raw={raw} type={block.type} />
}

/* ============================= */
/* CLOZE / GAP / RC */
/* ============================= */

function RenderClozeGapRC({ raw, type }) {

  const parsed = parseClozeSections(raw)

  return (
    <div>

      {/* PASSAGE */}
      <div className="mb-6 space-y-2 text-justify">
        {parsed.passage.split("\n").map((line, i) =>
          line.trim() ? <p key={i}>{line}</p> : null
        )}
      </div>

      {/* QUESTIONS */}
      <div className="space-y-2">
        {parsed.questions.map((line, i) => {

          const isQuestion = /^Question\s+\d+/i.test(line)

          return (
            <p key={i} className={isQuestion ? "font-bold" : ""}>
              {line}
            </p>
          )
        })}
      </div>

      {/* ANSWER KEY */}
      {parsed.answerKey && (
        <div className="mt-6">
          <p className="font-bold">ANSWER KEY</p>
          <p>{parsed.answerKey}</p>
        </div>
      )}

      {/* EXPLANATION */}
      {parsed.explanation && (
        <div className="mt-6 space-y-2">
          <p className="font-bold">HƯỚNG DẪN GIẢI CHI TIẾT</p>
          {parsed.explanation.split("\n").map((line, i) =>
            line.trim() ? <p key={i}>{line}</p> : null
          )}
        </div>
      )}
    </div>
  )
}

/* ============================= */
/* ARRANGE */
/* ============================= */

function RenderArrange({ raw }) {

  const parts = parseArrangeSections(raw)

  return (
    <div>

      {/* Question Block */}
      <div className="space-y-2">
        {parts.questionBlock.map((line, i) => {
          const isQuestion = /^Question\s+\d+/i.test(line)
          return (
            <p key={i} className={isQuestion ? "font-bold" : ""}>
              {line}
            </p>
          )
        })}
      </div>

      {/* Solution */}
      <div className="mt-6">
        <p className="font-bold">Lời giải</p>

        {parts.answerLetter && (
          <p>Chọn {parts.answerLetter}</p>
        )}

        {parts.solutionText.map((line, i) =>
          line.trim() ? <p key={i}>{line}</p> : null
        )}

        {parts.translation.length > 0 && (
          <>
            <p className="font-bold mt-4">Tạm dịch:</p>
            {parts.translation.map((line, i) =>
              line.trim() ? <p key={i}>{line}</p> : null
            )}
          </>
        )}
      </div>
    </div>
  )
}

/* ============================= */
/* PARSE LOGIC (giống python) */
/* ============================= */

function parseClozeSections(raw) {
  const PASS_HDR = "BÀI ĐỌC (PASSAGE)"
  const KEY = "ANSWER KEY"
  const EXPL = "HƯỚNG DẪN GIẢI CHI TIẾT"

  const passIndex = raw.indexOf(PASS_HDR)

  if (passIndex < 0) {
    return {
      passage: raw.slice(0, 200),
      questions: raw.slice(200).split("\n"),
      answerKey: "",
      explanation: ""
    }
  }

  const afterPass = raw.slice(passIndex + PASS_HDR.length)
  const firstQ = afterPass.indexOf("Question")

  const passage = afterPass.slice(0, firstQ).trim()

  const remain = afterPass.slice(firstQ)

  const keyIndex = remain.indexOf(KEY)
  const explIndex = remain.indexOf(EXPL)

  const questionBlock = remain.slice(0, keyIndex > 0 ? keyIndex : explIndex > 0 ? explIndex : undefined)

  const answerKey = keyIndex > 0
    ? remain.slice(keyIndex + KEY.length, explIndex > 0 ? explIndex : undefined).trim()
    : ""

  const explanation = explIndex > 0
    ? remain.slice(explIndex + EXPL.length).trim()
    : ""

  return {
    passage,
    questions: questionBlock.split("\n").map(l => l.trim()).filter(Boolean),
    answerKey,
    explanation
  }
}

function parseArrangeSections(raw) {

  const loiIndex = raw.indexOf("Lời giải")

  if (loiIndex < 0) {
    return {
      questionBlock: raw.split("\n"),
      answerLetter: "",
      solutionText: [],
      translation: []
    }
  }

  const questionBlock = raw.slice(0, loiIndex).split("\n")

  const after = raw.slice(loiIndex)

  const match = after.match(/Chọn\s+([ABCD])/)
  const answerLetter = match ? match[1] : ""

  const tamIndex = after.indexOf("Tạm dịch:")

  let solutionText = []
  let translation = []

  if (tamIndex > 0) {
    solutionText = after.slice(0, tamIndex).split("\n")
    translation = after.slice(tamIndex + "Tạm dịch:".length).split("\n")
  } else {
    solutionText = after.split("\n")
  }

  return {
    questionBlock,
    answerLetter,
    solutionText,
    translation
  }
}