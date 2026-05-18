import React from "react";
import { MathJax } from "better-react-mathjax";

export default function SafeMathText({ text, className = "" }) {
  if (!text) return null;

  // Xử lý xuống dòng từ AI (\n -> <br/>)
  const formattedText = text.replace(/\\n/g, "<br/>");

  return (
    <MathJax 
      inline 
      dynamic // Quan trọng: Cho phép cập nhật khi dữ liệu thay đổi
      hideUntilTypeset="first" // Tránh hiện mã LaTeX thô trước khi render
      className={className}
    >
      <span dangerouslySetInnerHTML={{ __html: formattedText }} />
    </MathJax>
  );
}


// import React, { Fragment } from "react";
// import { MathJax } from "better-react-mathjax";

// export default function SafeMathText({
//   text,
//   className = "",
// }) {
//   if (!text) return null;

//   // normalize newline
//   const normalized = String(text).replace(/\\n/g, "\n");

//   /**
//    * detect:
//    * $...$
//    * $$...$$
//    * \( ... \)
//    * \[ ... \]
//    */
//   const regex =
//     /(\$\$[\s\S]+?\$\$|\$[^$]+\$|\\\([\s\S]+?\\\)|\\\[[\s\S]+?\\\])/g;

//   const parts = normalized.split(regex);

//   return (
//     <div
//       className={className}
//       style={{
//         whiteSpace: "pre-line",
//         wordBreak: "break-word",
//       }}
//     >
//       {parts.map((part, idx) => {
//         if (!part) return null;

//         const isMath =
//           /^\$\$[\s\S]+?\$\$$/.test(part) ||
//           /^\$[^$]+\$$/.test(part) ||
//           /^\\\([\s\S]+?\\\)$/.test(part) ||
//           /^\\\[[\s\S]+?\\\]$/.test(part);

//         // ===== LATEX =====
//         if (isMath) {
//           return (
//             <MathJax
//               key={idx}
//               inline={
//                 !part.startsWith("$$") &&
//                 !part.startsWith("\\[")
//               }
//               dynamic
//               hideUntilTypeset="first"
//             >
//               {part}
//             </MathJax>
//           );
//         }

//         // ===== NORMAL TEXT =====
//         return (
//           <Fragment key={idx}>
//             {part}
//           </Fragment>
//         );
//       })}
//     </div>
//   );
// }