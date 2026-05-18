// import React from "react";
// import SafeMathText from "./SafeMathText";

// export default function SoluteLiteraturePreviewPanel({ examData }) {
//   const data = examData?.exam_data_schema;
//   if (!data) return null;

//   return (
//     <div className="h-full overflow-auto bg-gray-50 p-6 font-serif">
//       <div className="max-w-4xl mx-auto bg-white shadow-lg p-12 border rounded">
//         <h1 className="text-center text-2xl font-bold uppercase mb-10 border-b-2 pb-4">
//           {data.exam_title}
//         </h1>

//         {data.sections.map((sec, idx) => (
//           <div key={idx} className="mb-12">
//             <h2 className="font-bold text-xl text-blue-900 mb-6 border-l-4 border-blue-600 pl-4">
//               {sec.section_title}
//             </h2>
            
//             {sec.reading_passage && (
//               <div className="mb-8 bg-gray-50 p-8 rounded-lg border shadow-sm">
//                 <SafeMathText text={sec.reading_passage.intro_text} className="font-bold mb-4" />
//                 <SafeMathText text={sec.reading_passage.content} className="text-justify leading-8 mb-4 block" />
//                 <p className="text-right italic font-semibold">
//                   <SafeMathText text={`(${sec.reading_passage.source})`} />
//                 </p>
//               </div>
//             )}

//             <div className="space-y-10">
//               {sec.questions.map((q, qidx) => (
//                 <div key={qidx} className="group">
//                   <div className="font-bold text-lg mb-3">
//                     Câu {q.number}: <SafeMathText text={q.question_content} />
//                   </div>
                  
//                   <div className="bg-green-50 p-6 rounded-lg border border-green-100 group-hover:border-green-300 transition-colors">
//                     <p className="font-bold text-green-900 mb-3 border-b border-green-200 pb-1">Hướng dẫn giải:</p>
                    
//                     {q.question_type.includes("WRITING") ? (
//                       <div className="space-y-4">
//                         <div className="bg-white p-3 rounded border border-green-100">
//                           <p className="font-bold text-blue-800">1. Yêu cầu chung:</p>
//                           <ul className="list-disc ml-6 mt-1 space-y-1">
//                             <li><b>Vấn đề:</b> {q.solution.structured_content.a_general_requirements.issue}</li>
//                             <li><b>Hình thức:</b> {q.solution.structured_content.a_general_requirements.form}</li>
//                             <li><b>Dung lượng:</b> {q.solution.structured_content.a_general_requirements.length}</li>
//                           </ul>
//                         </div>
                        
//                         <div>
//                           <p className="font-bold text-blue-800">2. Yêu cầu cụ thể:</p>
//                           <div className="ml-4 mt-2 space-y-4">
//                             {Object.entries(q.solution.structured_content.b_specific_requirements.steps).map(([key, step]) => (
//                               step && (
//                                 <div key={key}>
//                                   <p className="italic font-bold text-gray-700 underline">{step.name}:</p>
//                                   <SafeMathText text={step.content} className="mt-1 block" />
//                                 </div>
//                               )
//                             ))}
//                           </div>
//                         </div>
//                       </div>
//                     ) : (
//                       <SafeMathText text={q.solution.explanation} className="leading-relaxed" />
//                     )}
//                   </div>
//                 </div>
//               ))}
//             </div>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// }



import React from "react";

const normalizeText = (text) => {
  if (!text) return "";
  return text.normalize("NFC");
};

export default function SoluteLiteraturePreviewPanel({ examData }) {
  // Chuẩn hóa dữ liệu về dạng mảng
  const exams = Array.isArray(examData) ? examData : examData ? [examData] : [];

  if (exams.length === 0) {
    return <div className="p-10 text-center text-gray-500">Đang tải dữ liệu hoặc không có dữ liệu...</div>;
  }

  return (
    <div className="h-full overflow-auto  p-6 font-sans">
      <div className="max-w-4xl mx-auto space-y-12">
        {exams.map((item, index) => {
          // Lấy dữ liệu thực tế (AI có thể trả về wrap trong exam_data_schema hoặc không)
          const data = item.exam_data_schema || item;

          return (
            <div key={index} className="bg-white shadow-lg p-12 border rounded">
              {/* Tiêu đề đề thi */}
              <h1 className="text-center text-2xl font-bold uppercase mb-10 border-b-2 pb-4">
                {data.exam_title}
              </h1>

              {data.sections?.map((sec, idx) => (
                <div key={idx} className="mb-12">
                  {/* Tiêu đề phần (I. ĐỌC HIỂU, II. VIẾT...) */}
                  <h2 className="font-bold text-xl mb-6 border-l-4 border-blue-600 pl-4">
                    {sec.section_title}
                  </h2>
                  
                  {/* Văn bản đọc hiểu (nếu có) */}
       {sec.reading_passage &&
            (
              sec.reading_passage.intro_text ||
              sec.reading_passage.content ||
              sec.reading_passage.source
            ) && (
              <div className="mb-8 bg-gray-50 p-8 rounded-lg border shadow-sm">

                {sec.reading_passage.intro_text && (
                  <div
                    className="font-bold mb-4 block"
                    dangerouslySetInnerHTML={{
                      __html: sec.reading_passage.intro_text
                    }}
                  />
                )}

                {sec.reading_passage.content && (
                  <div
                    className="whitespace-pre-line leading-8 mb-4 text-justify"
                    dangerouslySetInnerHTML={{
                       __html: normalizeText(sec.reading_passage.content)
                    }}
                  />
                )}

                {sec.reading_passage.source && (
                  <p className="text-right">
                    <span
                      dangerouslySetInnerHTML={{
                        __html: `(${sec.reading_passage.source})`
                      }}
                    />
                  </p>
                )}

              </div>
            )}
                  {/* Danh sách câu hỏi */}
                  <div className="space-y-10">
                    {sec.questions?.map((q, qidx) => (
                      <div key={qidx} className="group">
                        <div className="font-semibold text-lg mb-3 flex items-start gap-2">
                          <span className="shrink-0">
                            Câu {q.number}:
                          </span>

                          <span
                            className="flex-1 min-w-0"
                            dangerouslySetInnerHTML={{ __html: q.question_content }}
                          />
                        </div>
                        
                        {/* Box Hướng dẫn giải */}
                        <div className="bg-green-50 p-6 rounded-lg border border-green-100">
                          {/* <p className="font-bold  mb-3 border-b border-green-200 pb-1">Lời giải</p> */}
                          
                          {/* Phân loại hiển thị theo loại câu hỏi */}
                          {q.question_type?.includes("WRITING") ? (
                            <div className="space-y-4">
                              <div className="bg-white p-3 rounded border border-green-100">
                                <p className="font-bold">1. Yêu cầu chung:</p>
                                <ul className="list-disc ml-6 mt-1 space-y-1">
                                  <li><b>Vấn đề:</b> {q.solution?.structured_content?.a_general_requirements?.issue}</li>
                                  <li><b>Hình thức:</b> {q.solution?.structured_content?.a_general_requirements?.form}</li>
                                  <li><b>Dung lượng:</b> {q.solution?.structured_content?.a_general_requirements?.length}</li>
                                </ul>
                              </div>
                              
                              <div>
                                <p className="font-bold">2. Yêu cầu cụ thể:</p>
                                <div className="ml-4 mt-2 space-y-4">
                                  {q.solution?.structured_content?.b_specific_requirements?.steps && 
                                   Object.entries(q.solution.structured_content.b_specific_requirements.steps).map(([key, step]) => (
                                    step?.content && (
                                      <div key={key}>
                                        <p >{step.name}:</p>
                                        <div 
                                          className="mt-1 block text-justify"
                                          dangerouslySetInnerHTML={{ __html: step.content }} 
                                        />
                                      </div>
                                    )
                                  ))}
                                </div>
                              </div>
                            </div>
                          ) : (
                            /* Cho phần Đọc hiểu (READING) */
                            <div 
                              className="leading-relaxed whitespace-pre-line text-justify text-gray-800"
                              dangerouslySetInnerHTML={{ __html: q.solution?.explanation }} 
                            />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}