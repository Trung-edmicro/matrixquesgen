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

        <h1 className="text-center text-xl font-bold mb-6">
          ĐỀ THI TIẾNG ANH
        </h1>

        {blocks.map((block, index) => {

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
        })}

      </div>
    </div>
  )

  function ClozeBlock({ data }) {

  const title = data?.passage_title
  const passage = data?.passage || ""
  const questions = data?.questions || []

  return (
    <div className="mb-10">

      {title && (
        <h2 className="text-center font-bold mb-4">
          {title}
        </h2>
      )}

      <div className="mb-6 space-y-2 text-justify">
        {passage.split("\n").map((line, i) =>
          line.trim() && <p key={i}>{line}</p>
        )}
      </div>

      {questions.map((q) => {

        const options = [
          `A. ${q.option_a}`,
          `B. ${q.option_b}`,
          `C. ${q.option_c}`,
          `D. ${q.option_d}`,
        ]

        // Nếu tổng độ dài quá lớn → chuyển layout 2 dòng
        const isLong =
          options.join("").length > 120

        return (
          <div key={q.number} className="mb-6">

            <p className="font-semibold">
              Question {q.number}: {q.question_content}
            </p>

            {/* OPTIONS */}
            <div
              className={`pl-4 mt-2 gap-x-6 gap-y-1 ${
                isLong
                  ? "grid grid-cols-2"
                  : "grid grid-cols-4"
              }`}
            >
              <p>{options[0]}</p>
              <p>{options[1]}</p>
              <p>{options[2]}</p>
              <p>{options[3]}</p>
            </div>

            <div className="mt-3 pl-4 text-gray-700">

              <p className="font-semibold">Lời giải</p>
              <p className="font-semibold">Chọn {q.answer}</p>

              {q.explanation && (
                <p className="mt-2 whitespace-pre-line">
                  {q.explanation}
                </p>
              )}

              {q.quote && (
                <p className="mt-1">
                  <b>Trích bài:</b> {q.quote}
                </p>
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

function ArrangeBlock({ data }) {

  return (
    <div className="mb-10">

      <p className="font-semibold">
        Question {data.question_number}:
      </p>

      {data.question_stem && (
        <p className="mb-2">{data.question_stem}</p>
      )}

      <p className="mb-3">
        A. {data.option_a} &nbsp;&nbsp;
        B. {data.option_b} &nbsp;&nbsp;
        C. {data.option_c} &nbsp;&nbsp;
        D. {data.option_d}
      </p>

      <div className="pl-4">

        <p className="font-semibold">Lời giải</p>
        <p className="font-semibold">Chọn {data.answer}</p>

        {data.solution_lines?.map((l, i) => (
          <p key={i}>{l}</p>
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
}