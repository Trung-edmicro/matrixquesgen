// import React, { useMemo } from "react";
// import SafeMathText from "./SafeMathText";

// export default function SoluteStandardPreviewPanel({ examData }) {
//   const data = useMemo(() => {
//     if (examData?.results) return examData.results;
//     return examData;
//   }, [examData]);

//   // Nếu data là mảng (như cấu trúc JSON bạn gửi), lấy phần tử đầu tiên
//   const finalData = Array.isArray(data) ? data[0] : data;
//   const sections = finalData?.sections || [];

//   if (!sections.length) {
//     return (
//       <div className="h-full flex items-center justify-center text-gray-400">
//         Không có dữ liệu hiển thị
//       </div>
//     );
//   }

//   return (
//     <div className="h-full overflow-auto bg-gray-50 p-6 font-serif">
//       <div className="max-w-4xl mx-auto bg-white shadow-lg p-10 border rounded">
//         <h1 className="text-center text-2xl font-bold uppercase mb-8 border-b pb-4">
//           {finalData?.exam_title || "LỜI GIẢI CHI TIẾT"}
//         </h1>

//         {sections.map((section, sIdx) => (
//           <div key={sIdx} className="mb-10">
//             {section.section_title && (
//               <h2 className="font-bold text-lg mb-4  uppercase border-l-4 border-blue-600 pl-3">
//                 {section.section_title}
//               </h2>
//             )}

//             {section.questions.map((q, qIdx) => (
//               <div key={qIdx} className="mb-12 border-b border-gray-100 pb-8 last:border-0">
//                 {/* Nội dung câu hỏi */}
//                 <div className="flex gap-2 mb-4 text-[16px]">
//                   <span className="font-bold whitespace-nowrap">Câu {q.question_number}:</span>
//                   <div className="prose max-w-none">
//                     <SafeMathText text={q.question_content} />
//                   </div>
//                 </div>

//                 {/* Phần trắc nghiệm (nếu có) */}
//                 {q.type === "multiple_choice" && q.options && (
//                   <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 ml-6 mb-6">
//                     {['a', 'b', 'c', 'd'].map(key => {
//                         const opt = q.options[0]?.[`option_${key}`];
//                         if (!opt) return null;
//                         return (
//                             <div key={key} className="flex gap-2 items-start">
//                                 <span className="font-bold uppercase">{key}.</span>
//                                 <SafeMathText text={opt} />
//                             </div>
//                         );
//                     })}
//                   </div>
//                 )}

//                 {/* Phần đáp án đúng cho Short Answer */}
            //     {q.type === "true_false" && (
            //   <>
            //     {/* ===== OPTIONS ===== */}
            //     {q.options && (
            //       <div className="ml-6 mb-6 space-y-2">
            //         {q.options.map((opt, idx) => (
            //           <div key={idx} className="flex gap-2 items-start">
            //             <span className="font-bold lowercase">
            //               {opt.label?.toLowerCase()})
            //             </span>

            //             <div className="flex-1">
            //               <SafeMathText text={opt.content} />
            //             </div>
            //           </div>
            //         ))}
            //       </div>
            //     )}

            //     {/* ===== LỜI GIẢI ===== */}
            //     <div className="bg-blue-50 p-5 rounded-lg border border-blue-100">
            //       <div className="flex items-center gap-2 mb-3">
            //         <span className="bg-blue-600 text-white text-[11px] px-2 py-0.5 rounded font-sans uppercase tracking-wider">
            //           Lời giải
            //         </span>
            //       </div>

            //       {/* ===== 0101 ===== */}
            //       <div className="font-bold text-blue-800 mb-3">
            //         {q.correct_answer}
            //       </div>

            //       {/* ===== #### ===== */}
            //       <div className="font-bold mb-4">
            //         ####
            //       </div>

            //       {/* ===== GIẢI TỪNG Ý ===== */}
            //       <div className="space-y-5">
            //         {q.options.map((opt, idx) => {
            //           const status = opt.is_correct ? "ĐÚNG" : "SAI";

            //           return (
            //             <div key={idx}>
            //               {/* a) ... - ĐÚNG */}
            //               <div className="flex flex-wrap gap-2 leading-relaxed">
            //                 <div>
            //                 - <SafeMathText text={opt.content} />
            //                 </div>

            //                 <span>-</span>

            //                 <span className="font-bold">
            //                   {status}
            //                 </span>
            //               </div>

            //               {/* explanation */}
            //               {opt.explanation && (
            //                 <div className="mt-2 whitespace-pre-line  leading-relaxed">
            //                   <SafeMathText text={opt.explanation} />
            //                 </div>
            //               )}
            //             </div>
            //           );
            //         })}
            //       </div>
            //     </div>
            //   </>
            // )}

//                 {/* Short Answer */}
//                 {q.type === "short_answer" && q.correct_answer && (
//                   <div className="ml-6 mb-4 font-bold text-green-700">
//                     Đáp số: {q.correct_answer}
//                   </div>
//                 )}

//                   <p>
//                     {q.options?.[0]?.answer && (
//                         <span className="font-bold  ml-2">Chọn {q.options[0].answer}</span>
//                     )}
//                   </p>

//                 {/* Lời giải */}
//                 <div className="bg-blue-50 p-5 rounded-lg border border-blue-100">
//                   <div className="flex items-center gap-2 mb-3">
//                     <span className="bg-blue-600 text-white text-[11px] px-2 py-0.5 rounded font-sans uppercase tracking-wider">
//                       Lời giải
//                     </span>
                  
//                   </div>

             
                  
//                   <div className="text-gray-800 leading-relaxed whitespace-pre-line">
//                     <SafeMathText text={q.explanation} />
//                   </div>
                  
//                   {q.conclusion && (
//                     <div className="mt-4 font-bold  border-t border-red-200 pt-2">
//                       Kết luận: <SafeMathText text={q.conclusion} />
//                     </div>
//                   )}
//                 </div>
//               </div>
//             ))}
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// }


import React, { useMemo } from "react";
import SafeMathText from "./SafeMathText";

// --- Component hiển thị Bảng ---
const TableRenderer = ({ tableData }) => {
  if (!tableData) return null;
  const { title, headers, rows, notes, source, unit } = tableData;

  return (
    <div className="my-6 overflow-x-auto">
      {title && (
        <div className="text-center font-bold mb-2 text-sm md:text-base">
          {title.toUpperCase()} {unit && `(${unit})`}
        </div>
      )}
      <table className="min-w-full border-collapse border border-gray-400 text-sm md:text-base">
        <thead>
          <tr className="bg-gray-100">
            {headers.map((header, idx) => (
              <th key={idx} className="border border-gray-400 p-2 font-bold text-center">
                <SafeMathText text={header} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-gray-50">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="border border-gray-400 p-2 text-center">
                  <SafeMathText text={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {(source || notes) && (
        <div className="text-xs mt-2 italic text-right text-gray-600">
          {source && <span>Nguồn: {source}</span>}
          {notes && <span className="ml-2">{notes}</span>}
        </div>
      )}
    </div>
  );
};

export default function SoluteStandardPreviewPanel({ examData }) {
  const data = useMemo(() => {
    if (examData?.results) return examData.results;
    return examData;
  }, [examData]);

  const finalData = Array.isArray(data) ? data[0] : data;
  const sections = finalData?.sections || [];

  if (!sections.length) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        Không có dữ liệu hiển thị
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-gray-50 p-6 font-sans">
      <div className="max-w-4xl mx-auto bg-white shadow-lg p-10 border rounded">
        <h1 className="text-center text-2xl font-bold uppercase mb-8 border-b pb-4 text-blue-800">
          {finalData?.exam_title || "LỜI GIẢI CHI TIẾT"}
        </h1>

        {sections.map((section, sIdx) => (
          <div key={sIdx} className="mb-10">
            {section.section_title && (
              <h2 className="font-bold text-lg mb-6 uppercase border-l-4 border-blue-600 pl-3 bg-blue-50 py-2">
                {section.section_title}
              </h2>
            )}

       {section.questions.map((q, qIdx) => {
  const mediaList = q.media || [];

  const hasBeforeMedia = mediaList.some(
    (m) => m && m.position === "before_question_content"
  );

  const hasAfterMedia = mediaList.some(
    (m) => m && m.position === "after_question_content"
  );

  // Không có media nào
  const hasNoMedia = !hasBeforeMedia && !hasAfterMedia;

  return (
    <div
      key={qIdx}
      className="mb-12 border-b border-gray-100 pb-8 last:border-0"
    >

      {/* QUESTION */}
      <div className="mb-4 text-[16px] leading-relaxed">

        {/* CASE:
            1. Có after media  -> content cùng dòng
            2. Không có media  -> content cùng dòng
        */}
        {(hasAfterMedia || hasNoMedia) ? (
          <div className="flex flex-wrap gap-2">

            <span className="font-bold whitespace-nowrap text-blue-700">
              Câu {q.question_number}.
            </span>

            {q.question_title && (
              <span className="font-bold">
                <SafeMathText text={q.question_title} />
              </span>
            )}

            {q.question_content && (
              <span>
                <SafeMathText text={q.question_content} />
              </span>
            )}
          </div>
        ) : (
          <>
            {/* Chỉ render question line */}
            <div className="flex flex-wrap gap-2">

              <span className="font-bold whitespace-nowrap">
                Câu {q.question_number}.
              </span>

              {q.question_title && (
                <span className="font-bold">
                  <SafeMathText text={q.question_title} />
                </span>
              )}
            </div>

            {/* BEFORE MEDIA */}
            {mediaList.map((m, mIdx) => {
              if (!m) return null;

              if (m.position === "before_question_content") {

                if (m.type === "table") {
                  return (
                    <TableRenderer
                      key={mIdx}
                      tableData={m}
                    />
                  );
                }

                if (m.type === "image") {
                  return (
                    <div
                      key={mIdx}
                      className="my-4 flex justify-center"
                    >
                      <img
                        src={m.url}
                        alt=""
                        className="max-w-full h-auto rounded"
                      />
                    </div>
                  );
                }
              }

              return null;
            })}

            {/* Content paragraph riêng */}
            {q.question_content && (
              <div className="mt-3 whitespace-pre-line">
                <SafeMathText text={q.question_content} />
              </div>
            )}
          </>
        )}
      </div>

      {/* AFTER MEDIA */}
      {mediaList.map((m, mIdx) => {
        if (!m) return null;

        if (m.position === "after_question_content") {

          if (m.type === "table") {
            return (
              <TableRenderer
                key={mIdx}
                tableData={m}
              />
            );
          }

          if (m.type === "image") {
            return (
              <div
                key={mIdx}
                className="my-4 flex justify-center"
              >
                <img
                  src={m.url}
                  alt=""
                  className="max-w-full h-auto rounded"
                />
              </div>
            );
          }
        }

        return null;
      })}

      {/* multiple_choice */}
      {q.type === "multiple_choice" && q.options && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 ml-6 mb-6">
          {["a", "b", "c", "d"].map((key) => {
            const opt = q.options[0]?.[`option_${key}`];

            if (!opt) return null;

            return (
              <div key={key} className="flex gap-2 items-start">
                <span className="font-bold uppercase">{key}.</span>
                <SafeMathText text={opt} />
              </div>
            );
          })}
        </div>
      )}

      {/* true_false */}
      {q.type === "true_false" && q.options && (
        <div className="ml-6 mb-6 space-y-3">
          {q.options.map((opt, idx) => (
            <div
              key={idx}
              className="flex gap-2 items-start border-l-2 border-gray-100 pl-3"
            >
              <span className="font-bold">
                {opt.label.toLowerCase()})
              </span>

              <div className="flex-1 italic">
                <SafeMathText text={opt.content} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SOLUTION */}
      <div className="bg-blue-50 p-5 rounded-lg border border-blue-100 relative">
        <div className="absolute -top-3 left-4">
          <span className="bg-blue-600 text-white text-[11px] px-3 py-1 rounded-full font-sans uppercase tracking-wider shadow-sm">
            Lời giải
          </span>
        </div>

        <div className="mt-2">

          <div className="mb-3">
            {q.type === "multiple_choice" &&
              q.options?.[0]?.answer && (
                <div className="text-lg">
                  Chọn{" "}
                  <span className="font-bold">
                    {q.options[0].answer}
                  </span>
                </div>
              )}

            {q.type === "true_false" &&
              q.correct_answer && (
                <div className="text-lg">
                  Đáp án:{" "}
                  <span className="font-bold font-mono tracking-widest">
                    {q.correct_answer}
                  </span>
                </div>
              )}

            {q.type === "short_answer" &&
              q.correct_answer && (
                <div className="text-lg">
                  Đáp án:{" "}
                  <span >
                    {q.correct_answer}
                  </span>
                </div>
              )}
          </div>

          {q.type === "true_false" ? (
            <div className="space-y-4 mt-4">
              <div className="font-bold text-gray-400">####</div>

              {q.options.map((opt, idx) => (
                <div
                  key={idx}
                  className="bg-white/50 p-3 rounded border border-blue-50"
                >
                  <div className="flex gap-2 mb-1">
                    <p>{opt.content}</p>

                    <span
                      className={`font-bold ml-auto ${
                        opt.is_correct
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      — {opt.is_correct ? "ĐÚNG" : "SAI"}
                    </span>
                  </div>

                  {opt.explanation && (
                    <div className="text-sm pl-5 border-l border-blue-200">
                      <SafeMathText text={opt.explanation} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-800 leading-relaxed whitespace-pre-line">
              <SafeMathText text={q.explanation} />
            </div>
          )}

          {q.conclusion && (
            <div className="mt-4 font-bold border-t border-blue-200 pt-2">
              Kết luận:{" "}
              <SafeMathText text={q.conclusion} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
})}
          </div>
        ))}
      </div>
    </div>
  );
}