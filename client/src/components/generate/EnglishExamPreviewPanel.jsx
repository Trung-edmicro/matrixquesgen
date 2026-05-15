import {
  ReloadOutlined,
  CloseOutlined,
} from "@ant-design/icons"
import React,{ useMemo, useState } from "react"
import { Input, Button, message,Tag,notification,Checkbox } from "antd"
import { handleGenerateArrangeEnglishQuestion, handleRegenerateEnglishQuestion } from "../../services/api";
const { TextArea } = Input




export default function EnglishExamPreviewPanel({ examData,onUpdateExam, selectedQuestions,onToggleQuestionSelection }) {
const blocks = examData?.results || [];

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
          // const data = block.parsed
           const data = {
            ...block,
            ...block.parsed
          }

          const prevType = blocks[index - 1]?.type
          const isFirstOfGroup = prevType !== block.type

          switch (block.type) {

            case "ARRANGE":
              return (
                <ArrangeBlock
                  key={index}
                  data={data}
                  index={index}
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
                  index={index}
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
                  index={index}
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
                  index={index}
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
                  index={index}
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
                  index={index}
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
                  index={index}
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
                  index={index}
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
                  index={index}
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
                  index={index}
                  onUpdate={handleUpdateBlock}
                  type={block.type}
                  showInstruction={isFirstOfGroup}
                />
              )
            case "ESSAY_REWRITING_SENTENCES":
                return (
                  <EssaySentenceRewritingBlock
                    key={index}
                    data={data}
                    index={index}
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
                    index={index}
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
                  <EssayWordFormBlock
                    key={index}
                    data={data}
                    index={index}
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
                  <EssayWordPromptBlock
                    key={index}
                    data={data}
                    index={index}
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
                      index={index}
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


export function ClozeBlock({ data,index,onUpdate, type = "GAP", showInstruction= true }) {
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [isReloadingBlock, setIsReloadingBlock] = useState(false);
  const [blockFeedback, setBlockFeedback] = useState("");
  const [valueMap, setValueMap] = useState({});
  const [loadingMap, setLoadingMap] = useState({});

  const title = data?.passage_title;
  const passage = data?.passage || "";
  const questions = data?.questions || [];

  const handleRegenerateWholeBlock = async () => {
    if (!blockFeedback) {
      notification.warning({ message: "Vui lòng nhập yêu cầu sinh lại đoạn văn" });
      return;
    }
    
    setIsReloadingBlock(true);
    try {
      // Truyền q = null để báo hiệu sinh toàn bộ block
      const result = await handleRegenerateEnglishQuestion(data, null, blockFeedback);
      
      if (result.status === "success") {
        // result.parsed lúc này sẽ chứa { passage, passage_title, questions: [...] }
        onUpdate(index, result.parsed); 
        setBlockFeedback("");
        notification.success({ message: "Đã cập nhật đoạn văn và câu hỏi mới!" });
      }
    } catch (error) {
      console.error(error);
      notification.error({ message: "Lỗi kết nối máy chủ" });
    } finally {
      setIsReloadingBlock(false);
    }
  };

   const handleSubmitSingleQ = async (qNumber) => {
    const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này dựa trên nội dung bài đọc";
    setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    try {
      const currentQuestion = questions.find(q => q.number === qNumber);
      // Gửi kèm passage để AI biết ngữ cảnh
      const result = await handleRegenerateEnglishQuestion(
      {
        ...data,
        // Đảm bảo truyền đủ context bài đọc
        passage: passage,
        passage_title: title,
        type: type 
      }, 
      currentQuestion, 
      feedback
    );

      if (result.status === "success") {
        const updatedQuestion = result.parsed?.questions?.[0];
        if (updatedQuestion) {
          onUpdate(index, updatedQuestion);
          setActiveQuestion(null);
          notification.success({ message: `Đã cập nhật câu ${qNumber}` });
        }
      }
    } catch (error) {
      notification.error({ message: "Lỗi khi sinh lại câu hỏi" });
    } finally {
      setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
    }
  };



  const getInstruction = () => {

    // ✅ CHỈ CLOZE dùng text_type_en
    if (type === "CLOZE") {
      const textType = (data?.text_type_en || "").toLowerCase()

      return `Read the following ${textType} and mark the letter A, B, C or D on your answer sheet to indicate the option that best fits each of the numbered blanks.`;
    }

    // ✅ RC: cố định
    if (type === "RC") {
      return "Read the following passage and mark the letter A, B, C or D on your answer sheet to indicate the correct answer to each of the following questions.";
    }

    // ✅ GAP: cố định
    return "Read the following passage and mark the letter A, B, C or D on your answer sheet to indicate the option that best fits each of the numbered blank.";
  }

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }
  return (
    <div className="mb-12 border-l-4 border-blue-200 pl-4">

      <div className="mb-6 bg-blue-50 p-4 rounded-lg border border-blue-100 shadow-sm">
        {/* Dòng 1: Header chứa Tag và Nút bấm */}
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <Tag color="blue" className="font-bold">{type} BLOCK</Tag>
            <span className="text-gray-500 text-sm italic">
              
            </span>
          </div>
          
          <Button 
            type="primary" 
            danger 
            size="small" 
            icon={<ReloadOutlined />} 
            loading={isReloadingBlock}
            onClick={handleRegenerateWholeBlock}
          >
            Sinh lại toàn bộ
          </Button>
        </div>

        {/* Dòng 2: Ô nhập góp ý (p mới) */}
        <div className="mt-2">
          <Input 
            placeholder="Nhập yêu cầu cụ thể để sinh lại toàn bộ đoạn văn và câu hỏi" 
            size="middle" 
            value={blockFeedback}
            onChange={e => setBlockFeedback(e.target.value)}
            className="w-full shadow-sm"
            allowClear
          />
        </div>
</div>

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
              Question {q.number}.
            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}
          
            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
            </p>


            {activeQuestion === q.number && (
              <div className="my-2 p-3 border  rounded bg-gray-50">
                <TextArea
                  rows={2}
                  placeholder="Ví dụ: Đổi câu hỏi này sang kiểm tra từ vựng thay vì ngữ pháp..."
                  value={valueMap[q.number] || ""}
                 onChange={(e) => handleChange(q.number, e.target.value)}
                />
                <div className="mt-2 flex justify-end gap-2">
                  <Button size="small" onClick={() => setActiveQuestion(null)}>Hủy</Button>
                  <Button size="small" type="primary" loading={loadingMap[q.number]} onClick={() => handleSubmitSingleQ(q.number)}>
                    Gửi
                  </Button>
                </div>
              </div>
            )}

             <p className="mt-2 text-sm">
                {q.question_content}
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



export function ArrangeBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions=[],onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

  if (!data || typeof data !== 'object') return null


  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return (selectedQuestions || []).some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }

const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
   const currentQuestion = data.parsed;
   const result = await handleGenerateArrangeEnglishQuestion(
      data,
      feedback
    )

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed;

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};


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

          <Checkbox
                checked={isQuestionSelected(
                  index,
                  data?.parsed.question_number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: data?.parsed.question_number,
                  })
                }
              />{"  "}
        Question {data?.parsed.question_number ?? 'N/A'}. {"    "}

        <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === data.parsed.question_number ? null : data.parsed.question_number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi:{data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
      </p>

        {activeQuestion === data.parsed.question_number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[data.parsed.question_number] || ""}
                onChange={(e) =>
                  handleChange(data.parsed.question_number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[data.parsed.question_number]}
                  onClick={() => handleSubmit(data.parsed.question_number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}


      {data.question_stem && (
  <p className="mb-3 whitespace-pre-line">
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

export function SentenceCompletionBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions = [],onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
    return (selectedQuestions || []).some(
      (item) => item.blockIndex === blockIndex && item.questionNumber === questionNumber
    )
}
  if (!data || typeof data !== 'object') return null

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }



const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        console.log(">>>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};

  return (
    <div className="mb-10">

      {showInstruction && (
        <p className="font-bold mb-6">
          Sentence completion: Choose A, B, C or D to complete each sentence.
        </p>
      )}

      {data.questions.map(q => (
        <div key={`${index}-${q.number}`} className="mb-6">
          <p className="font-semibold">
              <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}

            Question {q.number}.

            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>

          </p>

          {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

          

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


export function   SynonymBlock({ data,index, onUpdate, showInstruction = true,selectedQuestions = [],onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})
  const [messageApi, contextHolder] = message.useMessage()

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
    return (selectedQuestions || []).some(
      (item) => item.blockIndex === blockIndex && item.questionNumber === questionNumber
    )
}
  if (!data || typeof data !== 'object') return null

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }

  if (!data || typeof data !== "object") return null

  const type = data.questions?.[0]?.type

  const title =
    type === "antonym"
      ? "Antonyms: Choose A, B, C or D that has the OPPOSITE meaning to the underlined word/phrase in each question."
      : "Synonyms: Choose A, B, C or D that has the CLOSEST meaning to the underlined word/phrase in each question."


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};
  return (
    <div className="mb-10">
      {contextHolder}

      {/* TITLE */}
      {showInstruction && (
        <p className="font-bold mb-4">{title}</p>
      )}

      {data.questions.map((q) => (
        <div key={`${index}-${q.number}`} className="mb-8">

          {/* 🔥 LINE 1: Question + Icon + Tags */}
          <p className="flex items-center flex-wrap gap-2 mb-1">
              <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}
            <strong>Question {q.number}.</strong>

            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>


           {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}
          {/* 🔥 LINE 2: Question content */}
          <p className="mb-2">
            <span
              dangerouslySetInnerHTML={{ __html: q.question }}
            />
          </p>

          {/* OPTIONS */}
          <div className="pl-6 mt-2 space-y-1">
            <p>A. {q.option_a}</p>
            <p>B. {q.option_b}</p>
            <p>C. {q.option_c}</p>
            <p>D. {q.option_d}</p>
          </div>

          {/* EXPLANATION */}
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


export function ErrorIdentificationBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions = [],onToggleQuestionSelection }) {

  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
    return (selectedQuestions || []).some(
      (item) => item.blockIndex === blockIndex && item.questionNumber === questionNumber
    )
}
  if (!data || typeof data !== 'object') return null

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }



const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};


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
            Question {q.number}.

            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>

          </p>

           {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}  

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


   const getLevelColor = (level) => {
    switch (level) {
      case "Nhận biết":
        return "green"
      case "Thông hiểu":
        return "blue"
      case "Vận dụng":
        return "orange"
      case "Vận dụng cao":
        return "red"
      default:
        return "default"
    }
  }

    const getDiffColor = (diff) => {
    switch (diff) {
      case "A1":
      case "A2":
        return "green"
      case "B1":
      case "B2":
        return "blue"
      case "C1":
      case "C2":
        return "red"
      default:
        return "purple"
    }
  }

export function SentenceTransformationBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {

  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

    const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  if (!data || typeof data !== 'object') return null

  const type = data.questions?.[0]?.type

  const title =
    type === "combination"
      ? "Sentence combination: Choose A, B, C or D that has the CLOSEST meaning to the given pair of sentences in each question."
      : "Sentence rewriting: Choose A, B, C or D that has the CLOSEST meaning to the given sentence in each question."

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};


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

             <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}
            Question {q.number}.{"    "}

            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>

          {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

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


export function PronunciationBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

    const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}
  if (!data || typeof data !== 'object') return null

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};
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
        <div key={`${index}-${q.number}`} className="mb-6">

          <p className="font-semibold">
              <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}
            Question {q.number}.

              <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
             <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>

           {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

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


export function DialogueBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

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


  const isQuestionSelected = (
  blockIndex,
  questionNumber
    ) => {
      return selectedQuestions.some(
        (item) =>
          item.blockIndex === blockIndex &&
          item.questionNumber === questionNumber
      )
    }

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};


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
            <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}

            Question {renderText(q?.number)}.

            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>

          {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}



          {q?.speaker_a && (
            <p> {renderText(q.speaker_a)}</p>
          )}

          {q?.speaker_b && (
            <p> {renderText(q.speaker_b)}</p>
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


export function WordReorderingBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  if (!data || typeof data !== 'object') return null 

  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

    const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};

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
        <div key={`${index}-${q.number}`} className="mb-6">

          {/* QUESTION NUMBER */}
          <p className="font-semibold">
            <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}

            Question {q.number}.{"    "} 
               <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>

             {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

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


export function LogicalThinkingBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {

  const questions = data?.questions || []

  if (!questions.length) return null

  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})
  const [messageApi, contextHolder] = message.useMessage()

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};


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
        <div key={`${index}-${q.number}`} className="mb-8">

          {/* QUESTION NUMBER */}
          <p className="font-semibold">

             <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}

            Question {q.number}.

             <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>

           {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

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


export function EssayWordOrderingBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})
  const [messageApi, contextHolder] = message.useMessage()

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};

  return (
    <div className="mb-10">

      {showInstruction && (
        <p className="font-bold italic mb-6">
          Reorder the words given to make correct sentences.
        </p>
      )}

      {data.questions.map(q => (
        <div key={`${index}-${q.number}`} className="mb-6">
              <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}

          <p><strong>Question {q.number}.</strong>

            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>

          </p>

           {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}
          <p>
             {q.given_words}
             
          </p>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>

            <p>{q.correct_sentence}</p>

            <p className="mt-1">
              <b>Kiến thức:</b> {q.knowledge}
            </p>

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>

            <p className="mt-1">
              <b>Tạm dịch:</b> {q.translation}
            </p>
          </div>

        </div>
      ))}
    </div>
  )
}


export function EssaySentenceRewritingBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)

  const [valueMap, setValueMap] = useState({})

  const [loadingMap, setLoadingMap] = useState({})

  const [messageApi, contextHolder] = message.useMessage()

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};

  return (
    <div className="mb-10">

      {showInstruction && (
        <p className="font-bold mb-6">
          Rewrite the following sentences without changing their meaning.
        </p>
      )}

      {data.questions.map(q => (
        <div  key={`${index}-${q.number}`} className="mb-6">

        

          <p>
            <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}
            <strong>Question {q.number}.</strong>

            <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>
          
           {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

          
          <p>
            {q.original_sentence}
          </p>

          <p>→ {q.rewrite_prompt} ___________________________.</p>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>

            <p>{q.full_rewritten_sentence}</p>

            <p className="mt-1">
              <b>Kiến thức:</b> {q.knowledge}
            </p>

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>

            <p className="mt-1">
              <b>Tạm dịch:</b> {q.translation?.rewritten}
            </p>
          </div>

        </div>
      ))}
    </div>
  )
}


export function EssayCombineSentencesBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }

const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};



  return (
    <div className="mb-10">

      {showInstruction && (
        <p className="font-bold mb-6">
          Rewrite the sentence that best combines each pair of sentences in the following question.
        </p>
      )}

      {data.questions.map(q => (
        <div key={`${index}-${q.number}`} className="mb-6">
          
         
        
          <p>
             <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}
            <strong>Question {q.number}.</strong>
              <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>


            {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

          <p>
            {q.sentence_1}{q.sentence_2}
          </p>
          <p>→ {q.rewrite_prompt} ___________________________.</p>

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>

            <p>{q.combined_sentence}</p>

            <p className="mt-1">
              <b>Kiến thức:</b> {q.knowledge}
            </p>

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>

            <p className="mt-1">
              <b>Tạm dịch:</b> {q.translation?.combined}
            </p>
          </div>

        </div>
      ))}
    </div>
  )
}

export function EssayWordFormBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})

  const formatSentence = (sentence, givenWord) => {
    if (!sentence) return ""

    // Check nếu đã có (WORD)
    const hasBracketWords = /______\s*\([A-Za-z ,]+\)/i.test(sentence)

    if (hasBracketWords) return sentence

    if (!givenWord) return sentence

    const words = givenWord.split(",").map(w => w.trim())
    let index = 0

    return sentence.replace(/______/g, () => {
      if (index < words.length) {
        const word = words[index++]
        return `______ (${word})`
      }
      return "______"
    })
  }

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};


  return (
    <div className="mb-10">

      {showInstruction && (
        <p className="font-bold italic mb-6">
          Complete the following sentences with the correct forms of the word in the brackets.
        </p>
      )}

      {data.questions.map(q => {
        const finalSentence = formatSentence(q.sentence, q.given_word)

        return (
          <div key={`${index}-${q.number}`} className="mb-6">
            <p>
             <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}

              <strong>Question {q.number}.</strong>
               <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
            </p>
               {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

            <p>
              {finalSentence}
            </p>

            <div className="mt-3 pl-6">
              <p className="font-semibold">Lời giải</p>

              <p>{q.answer}</p>

              <p className="mt-1 whitespace-pre-line">
                {q.explanation}
              </p>

              <p className="mt-1">
                <b>Tạm dịch:</b> {q.translation}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}


export function EssayWordPromptBlock({ data,index, onUpdate, showInstruction = true, selectedQuestions,onToggleQuestionSelection }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [valueMap, setValueMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})
  const [messageApi, contextHolder] = message.useMessage()

  const isQuestionSelected = (
  blockIndex,
  questionNumber
) => {
  return selectedQuestions.some(
    (item) =>
      item.blockIndex === blockIndex &&
      item.questionNumber === questionNumber
  )
}

  const handleChange = (qNumber, val) => {
    setValueMap((prev) => ({
      ...prev,
      [qNumber]: val,
    }))
  }


const handleSubmit = async (qNumber) => {
  const feedback = valueMap[qNumber] || "Sinh lại câu hỏi này";
  setLoadingMap(prev => ({ ...prev, [qNumber]: true }));

    notification.info({
    title: "Đã gửi yêu cầu",
    description: "Đã gửi yêu cầu sinh lại câu hỏi. Vui lòng đợi kết quả!",
    placement: "topRight",
    duration: 3
  });

  try {
    const currentQuestion = data.questions.find(q => q.number === qNumber);
    const result = await handleRegenerateEnglishQuestion(data, currentQuestion, feedback);

    if (result.status === "success") {
      // Backend trả về: { questions: [ {number: 1, ...} ] }
      const updatedQuestion = result.parsed?.questions?.[0];

      if (updatedQuestion) {
        // Gọi hàm onUpdate của cha (EnglishExamPreviewPanel)
        console.log(">>>>> debug index", index);
        onUpdate(index, updatedQuestion); 
        setActiveQuestion(null);

        notification.success({
        title: "Thành công",
        description: `Câu ${qNumber} đã được sinh lại`,
        placement: "topRight",
        duration: 2
      });
    
      }
    }
  } catch (error) {
    // ... handle error
  } finally {
    setLoadingMap(prev => ({ ...prev, [qNumber]: false }));
  }
};



  return (
    <div className="mb-10">

      {showInstruction && (
        <p className="font-bold mb-6">
          Complete sentence by using the words or phrases below, adding more words if necessary.
        </p>
      )}

      {data.questions.map(q => (
        <div key={`${index}-${q.number}`} className="mb-6">

          <p>
              <Checkbox
                checked={isQuestionSelected(
                  index,
                  q.number
                )}
                onChange={() =>
                  onToggleQuestionSelection({
                    blockIndex: index,
                    questionNumber: q.number,
                  })
                }
              />{"  "}

            <strong>Question {q.number}.</strong>

             <ReloadOutlined
              style={{ cursor: "pointer" }}
              onClick={() =>
                setActiveQuestion(
                  activeQuestion === q.number ? null : q.number
                )
              }
            />
            {"    "}

            {/* TAGS */}
            <Tag color="geekblue">Chủ đề: {data.title}</Tag>{"    "}
            <Tag color="geekblue">Dạng câu hỏi: {data.spec}</Tag>{"    "}
            <Tag color={getLevelColor(data.level)}>
              Mức độ: {data.level}
            </Tag>{"    "}
            <Tag color={getDiffColor(data.diff)}>
              Độ khó: {data.diff}
            </Tag>
          </p>

          {activeQuestion === q.number && (
            <div className="mt-2 pl-6 border p-3 rounded-lg bg-gray-50">

              <div className="flex justify-end gap-2 mb-2">
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setActiveQuestion(null)}
                >
                  Đóng
                </Button>
              </div>

              <TextArea
                rows={3}
                placeholder="Nhập câu trả lời..."
                value={valueMap[q.number] || ""}
                onChange={(e) =>
                  handleChange(q.number, e.target.value)
                }
              />

              <div className="mt-2 flex justify-end">
                <Button
                  type="primary"
                  loading={loadingMap[q.number]}
                  onClick={() => handleSubmit(q.number)}
                >
                  Gửi
                </Button>
              </div>
            </div>
          )}

          <p>
            {q.given_prompts}
          </p>

          {q.sentence_starter && (
            <p>→ {q.sentence_starter} ___________________________.</p>
          )}

          <div className="mt-3 pl-6">
            <p className="font-semibold">Lời giải</p>

            <p>Đáp án: {q.full_sentence}</p>

            <p className="mt-1">
              <b>Kiến thức:</b> {q.knowledge}
            </p>

            <p className="mt-1 whitespace-pre-line">
              {q.explanation}
            </p>

            <p className="mt-1">
              <b>Tạm dịch:</b> {q.translation}
            </p>
          </div>

        </div>
      ))}
    </div>
  )
}