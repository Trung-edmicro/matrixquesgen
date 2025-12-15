import { useState } from 'react'
import ExamPreviewPanel from './ExamPreviewPanel'

// Mock data từ session thực tế
const mockExamData = {
  "metadata": {
    "session_id": "94e39914-0d97-464b-a0e5-5e3d26927c82",
    "total_questions": 28,
    "tn_count": 24,
    "ds_count": 4,
    "matrix_file": "07. SỬ 12. ma trận KSCL lần 1.xlsx",
    "generated_at": "2025-12-15T13:25:19.550943",
    "status": "completed"
  },
  "questions": {
    "TN": [
      {
        "question_code": "C10",
        "question_type": "TN",
        "lesson_name": "Bài 3. Trật tự thế giới sau Chiến tranh lạnh",
        "level": "NB",
        "question_stem": "Sau khi Chiến tranh lạnh kết thúc, xu thế phát triển chủ đạo của thế giới là",
        "options": {
          "A": "hòa bình, hợp tác và phát triển.",
          "B": "chạy đua vũ trang và chiến tranh.",
          "C": "đối đầu căng thẳng giữa các nước lớn.",
          "D": "thiết lập các liên minh quân sự toàn cầu."
        },
        "correct_answer": "A",
        "explanation": "Sau khi Chiến tranh lạnh kết thúc, thế giới chuyển dần sang xu thế hòa bình, ổn định và hợp tác phát triển."
      },
      {
        "question_code": "C15",
        "question_type": "TN",
        "lesson_name": "Bài 4. Sự ra đời và phát triển của Hiệp hội các quốc gia Đông Nam Á",
        "level": "TH",
        "question_stem": "Hiệp hội các quốc gia Đông Nam Á (ASEAN) được tuyên bố thành lập vào tháng 8-1967 tại thủ đô của quốc gia nào sau đây?",
        "options": {
          "A": "In-đô-nê-xi-a",
          "B": "Thái Lan",
          "C": "Phi-lip-pin",
          "D": "Ma-lai-xi-a"
        },
        "correct_answer": "B",
        "explanation": "Ngày 8-8-1967, Hiệp hội các quốc gia Đông Nam Á (ASEAN) được thành lập tại Băng Cốc (thủ đô của Thái Lan)."
      },
      {
        "question_code": "C1",
        "question_type": "TN",
        "lesson_name": "Bài 1. Liên Hợp Quốc",
        "level": "VD",
        "question_stem": "Hiến chương Liên hợp quốc được thông qua tại hội nghị nào sau đây?",
        "options": {
          "A": "Hội nghị Ianta (2 - 1945)",
          "B": "Hội nghị San Francisco (4 đến 6 - 1945)",
          "C": "Hội nghị Pốtxđam (7 đến 8 - 1945)",
          "D": "Hội nghị Vécxai (1919 - 1920)"
        },
        "correct_answer": "B",
        "explanation": "Từ ngày 25-4 đến ngày 26-6-1945, đại biểu 50 nước họp tại San Francisco để thông qua Hiến chương Liên hợp quốc."
      }
    ],
    "DS": [
      {
        "question_code": "C3",
        "question_type": "DS",
        "lesson_name": "Bài 3. Trật tự thế giới sau Chiến tranh lạnh",
        "source_text": "Sau khi Chiến tranh lạnh chấm dứt, trật tự thế giới hai cực I-an-ta tan rã, thế giới hình thành xu hướng đa cực. Nhiều trung tâm quyền lực xuất hiện và cạnh tranh với nhau trong việc chi phối quan hệ quốc tế như Mỹ, Liên minh châu Âu (EU), Nhật Bản, Trung Quốc, Liên bang Nga... Xu thế chủ đạo của thế giới là hòa bình, hợp tác và phát triển. Các quốc gia đều tập trung nguồn lực vào phát triển kinh tế. Các nước lớn tránh xung đột trực tiếp, chủ trương đối thoại, thỏa hiệp để giải quyết các vấn đề quốc tế.",
        "statements": {
          "a": {
            "text": "Đoạn tư liệu khẳng định sau khi Chiến tranh lạnh kết thúc, trật tự hai cực I-an-ta đã sụp đổ và thế giới hình thành xu thế đa cực.",
            "level": "NB",
            "correct_answer": true
          },
          "b": {
            "text": "Theo tư liệu, sau Chiến tranh lạnh, các quốc gia đều tập trung nguồn lực vào phát triển quân sự và chạy đua vũ trang để xác lập vị thế quốc tế.",
            "level": "NB",
            "correct_answer": false
          },
          "c": {
            "text": "Sự vươn lên của các cường quốc như Mỹ, Nhật Bản, Trung Quốc, Liên bang Nga được đề cập trong tư liệu là biểu hiện cụ thể của xu thế đa cực trong quan hệ quốc tế.",
            "level": "TH",
            "correct_answer": true
          },
          "d": {
            "text": "Xu thế đối thoại và thỏa hiệp giữa các nước lớn được đề cập trong tư liệu là cơ sở để khẳng định nguy cơ chiến tranh và xung đột quân sự đã bị loại bỏ hoàn toàn khỏi đời sống quốc tế hiện nay.",
            "level": "VD",
            "correct_answer": false
          }
        },
        "explanation": {
          "a": "Đúng. Tư liệu nêu rõ: 'Sau khi Chiến tranh lạnh chấm dứt, trật tự thế giới hai cực I-an-ta tan rã... xu hướng đa cực'.",
          "b": "Sai. Tư liệu nêu rõ các quốc gia 'tập trung vào phát triển kinh tế', không phải tập trung vào phát triển quân sự.",
          "c": "Đúng. Việc xuất hiện nhiều trung tâm quyền lực cạnh tranh và chi phối quan hệ quốc tế chính là bản chất của xu thế đa cực.",
          "d": "Sai. Dù xu thế chủ đạo là hòa bình, hợp tác và các nước lớn tránh xung đột trực tiếp, nhưng thực tế các cuộc xung đột cục bộ vẫn diễn ra."
        }
      },
      {
        "question_code": "C1",
        "question_type": "DS",
        "lesson_name": "Bài 1. Liên Hợp Quốc",
        "source_text": "Hiến chương Liên hợp quốc là văn bản pháp lý quan trọng nhất, là cơ sở cho tổ chức và hoạt động của Liên hợp quốc. Ngày 26-6-1945, tại thành phố San Francisco (Mỹ), đại biểu 50 nước đã kí Hiến chương Liên hợp quốc. Theo Hiến chương, các nguyên tắc hoạt động của Liên hợp quốc bao gồm: Bình đẳng về chủ quyền quốc gia; Tôn trọng toàn vẹn lãnh thổ và độc lập chính trị của tất cả các nước; Cấm đe dọa sử dụng vũ lực hoặc sử dụng vũ lực trong quan hệ quốc tế; Giải quyết các tranh chấp quốc tế bằng biện pháp hòa bình; Không can thiệp vào công việc nội bộ của bất kì nước nào.",
        "statements": {
          "a": {
            "text": "Sự kiện ngày 26-6-1945 tại San Francisco (Mỹ) đánh dấu việc đại biểu 50 nước đã kí kết văn bản pháp lý quan trọng nhất của Liên hợp quốc.",
            "level": "NB",
            "correct_answer": true
          },
          "b": {
            "text": "Theo tư liệu, một trong những nguyên tắc hoạt động của Liên hợp quốc là được phép can thiệp vào công việc nội bộ của các nước thành viên để duy trì hòa bình.",
            "level": "NB",
            "correct_answer": false
          },
          "c": {
            "text": "Nội dung tư liệu cho thấy Hiến chương Liên hợp quốc đóng vai trò là khuôn khổ pháp lý nền tảng quy định các nguyên tắc ứng xử cơ bản trong quan hệ quốc tế.",
            "level": "TH",
            "correct_answer": true
          },
          "d": {
            "text": "Chủ trương giải quyết các vấn đề tranh chấp ở Biển Đông thông qua thương lượng hòa bình của Việt Nam là sự vận dụng các nguyên tắc hoạt động của Liên hợp quốc.",
            "level": "VD",
            "correct_answer": true
          }
        },
        "explanation": {
          "a": "Đúng. Thông tin trong tư liệu nêu rõ: 'Ngày 26-6-1945, tại thành phố San Francisco (Mỹ), đại biểu 50 nước đã kí Hiến chương Liên hợp quốc'.",
          "b": "Sai. Tư liệu nêu rõ nguyên tắc là 'Không can thiệp vào công việc nội bộ của bất kì nước nào'.",
          "c": "Đúng. Tư liệu khẳng định Hiến chương là 'văn bản pháp lý quan trọng nhất', 'cơ sở cho tổ chức và hoạt động'.",
          "d": "Đúng. Việt Nam kiên trì giải quyết tranh chấp bằng biện pháp hòa bình là sự vận dụng trực tiếp nguyên tắc được nêu trong Hiến chương."
        }
      }
    ]
  }
}

export default function TestPreview() {
  return (
    <div className="h-screen p-4 bg-gray-50">
      <div className="mb-4">
        <h1 className="text-xl font-medium text-gray-900">Test Preview Component</h1>
        <p className="text-sm text-gray-600">
          Data từ session: {mockExamData.metadata.session_id.slice(0, 8)}... 
          ({mockExamData.metadata.tn_count} TN, {mockExamData.metadata.ds_count} DS)
        </p>
      </div>
      
      <div className="h-[calc(100vh-100px)]">
        <ExamPreviewPanel 
          examData={mockExamData}
          isGenerating={false}
          sessionId={mockExamData.metadata.session_id}
        />
      </div>
    </div>
  )
}
