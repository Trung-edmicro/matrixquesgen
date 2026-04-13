
import { useMemo } from "react"
import { ArrangeBlock, ClozeBlock, DialogueBlock, ErrorIdentificationBlock, LogicalThinkingBlock,
        PronunciationBlock, SentenceTransformationBlock, SentenceCompletionBlock, SynonymBlock, WordReorderingBlock } from "./EnglishExamPreviewPanel"
export default function EnglishExamTHCSPreviewPanel({ examData }) {

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
