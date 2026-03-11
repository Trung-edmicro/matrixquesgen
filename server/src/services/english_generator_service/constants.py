PROMPTS = {
    "Điền từ": "TA_Dien_tu.md",
    "Sắp xếp": "TA_sap_xep.md",
    "Đọc hiểu": "TA_Doc_hieu.md",
    "Điền cụm từ/điền câu": "TA_Dien_cau_cum_tu.md"
}

# ============================
# JSON OUTPUT SCHEMAS (thay thế output_rule dạng text)
# ============================

# ── CLOZE / GAP / RC ────────────────────────────────────────────
# Schema dùng chung cho Điền từ, Điền cụm từ/điền câu, Đọc hiểu
# (chỉ khác nhau ở có/không có passage_title)

CLOZE_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "passage_title": "<tiêu đề bài đọc, để trống nếu không có>",
  "passage": "<toàn bộ nội dung bài đọc, giữ nguyên ký hiệu (1)______, (2)______ ...>",
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "question_content": "<nội dung câu hỏi, ví dụ: 'Question 1: Choose the best word to fill blank (1).' — để trống nếu không có câu hỏi riêng>",
      "option_a": "<nội dung đáp án A>",
      "option_b": "<nội dung đáp án B>",
      "option_c": "<nội dung đáp án C>",
      "option_d": "<nội dung đáp án D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<lý do chọn đáp án đúng>",
      "quote": "<trích nguyên văn câu chứa đáp án trong bài đọc>",
      "translation": "<dịch nghĩa tiếng Việt của câu trích>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
"""

CLOZE_WITH_TITLE_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "passage_title": "<tiêu đề bài đọc, BẮT BUỘC có vì dạng thức là {TEXT_TYPE}>",
  "passage": "<toàn bộ nội dung bài đọc, giữ nguyên ký hiệu (1)______, (2)______ ...>",
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "question_content": "<nội dung câu hỏi, ví dụ: 'What is the main topic of the passage?' — để trống nếu không có câu hỏi riêng>",
      "option_a": "<nội dung đáp án A>",
      "option_b": "<nội dung đáp án B>",
      "option_c": "<nội dung đáp án C>",
      "option_d": "<nội dung đáp án D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<lý do chọn đáp án đúng>",
      "quote": "<trích nguyên văn câu chứa đáp án trong bài đọc>",
      "translation": "<dịch nghĩa tiếng Việt của câu trích>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
"""

# ── ARRANGE ──────────────────────────────────────────────────────

ARRANGE_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "question_number": {START_NUM},
   "question_stem": "a. <sentence>\n
                    b. <sentence>\n
                    c. <sentence>\n
                    d. <sentence>\n
                    e. <sentence>",
  "option_a": "<phương án A - chuỗi sắp xếp>",
  "option_b": "<phương án B - chuỗi sắp xếp>",
  "option_c": "<phương án C - chuỗi sắp xếp>",
  "option_d": "<phương án D - chuỗi sắp xếp>",
  "answer": "<A hoặc B hoặc C hoặc D>",
  "solution_lines": [
    "<dòng 1 của đoạn hội thoại/văn bản đúng thứ tự>",
    "<dòng 2>",
    "..."
  ],
  "translation_lines": [
    "<dịch nghĩa dòng 1>",
    "<dịch nghĩa dòng 2>",
    "..."
  ]
}}

Quy tắc bắt buộc:
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- solution_lines và translation_lines phải có cùng số phần tử
- KHÔNG thêm bất kỳ text nào ngoài JSON
"""

# ── EXPLANATION TEMPLATES (vẫn giữ để inject vào prompt) ─────────

CLOZE_EXPLANATION_TEMPLATE = r"""
Question {QNUM}: 
A. {OPT_A}		B. {OPT_B}		C. {OPT_C}		D. {OPT_D}

Lời giải
Chọn {ANSWER}

{EXPLANATION}

Trích bài: {QUOTE}
Tạm dịch: {TRANSLATION}
""".strip()

SILENT_PHASE_EXPLANATION_TEMPLATE = r"""
Trường "explanation" trong JSON CHỈ chứa nội dung hướng dẫn giải bên dưới, KHÔNG chứa câu hỏi, KHÔNG chứa danh sách đáp án A/B/C/D.

Phân tích đáp án đúng:
- Ngữ pháp: [Phân tích cấu trúc câu]
- Logic – Ngữ cảnh: [Giải thích vì sao đáp án này phù hợp]
- Từ khóa liên kết: [Chỉ ra keyword nối với câu trước/sau]
→ Kết luận: [Vì sao đây là đáp án chính xác nhất]

Phân tích đáp án sai:
-viết lại đáp án A: [Sai ở điểm nào]
-viết lại đáp án B: [Sai vì...]
-viết lại đáp án C: [Sai vì...]
-viết lại đáp án D: [Sai vì...]

""".strip()

ARRANGE_SOLUTION_TEMPLATE = r"""
Lời giải
Chọn [A/B/C/D]
[Ghép đúng thứ tự]
Tạm dịch:
[Dịch từng dòng tương ứng]
""".strip()

# READING_COMPREHENSION_EXPLANATION_TEMPLATE = r"""
# Question {question_number}. {question_content}

# A. {option_A}
# B. {option_B}
# C. {option_C}
# D. {option_D}

# Lời giải:
# Chọn {correct_answer}

# - {option_A_keyword}: Giải thích vì sao đúng/sai
# - {option_B_keyword}: Giải thích vì sao đúng/sai
# - {option_C_keyword}: Giải thích vì sao đúng/sai
# - {option_D_keyword}: Giải thích vì sao đúng/sai

# Thông tin: [Trích dẫn nguyên văn]
# Tạm dịch: [Dịch sang tiếng Việt]
# """.strip()

# READING_COMPREHENSION_EXPLANATION_TEMPLATE = r"""
# Cấm tuyệt đối viết A B C D trong lời giải, bắt buộc ghi toàn bộ nội dung của các đáp án A B C D

# Question {question_number}. {question_content}

# A. {option_A}
# B. {option_B}
# C. {option_C}
# D. {option_D}

# Lời giải
# Chọn {correct_answer}

# Phân tích đáp án:
# Bắt buộc phân tích đáp án phải viết bằng Tiếng Việt
# {option_A} - viết lại đáp án A
# → [Đúng/Sai]. [Giải thích bằng tiếng Việt]

#  {option_B} - viết lại đáp án B 
# → [Đúng/Sai]. [Giải thích bằng tiếng Việt]

#  {option_C} - viết lại đáp án C
# → [Đúng/Sai]. [Giải thích bằng tiếng Việt]

# {option_D} - viết lại đáp án D
# → [Đúng/Sai]. [Giải thích bằng tiếng Việt]

# Thông tin: [Trích dẫn nguyên văn]
# Tạm dịch: [Dịch sang tiếng Việt]
# """.strip()
READING_COMPREHENSION_EXPLANATION_TEMPLATE = r"""
Quy tắc bắt buộc:
- Cấm tuyệt đối viết A B C D trong phần phân tích đáp án, bắt buộc sử dụng nội dung của từng phương án để làm tiêu đề phân tích
- Cấm tuyệt đối viết lại câu hỏi và đáp án trong lời giải
- Cấm viết chữ Lời giải và chọn đáp án nào đúng

Phân tích đáp án:
Bắt buộc phân tích đáp án phải viết bằng Tiếng Việt

{option_A}
→ [Đúng/Sai]. [Giải thích bằng tiếng Việt]

{option_B}
→ [Đúng/Sai]. [Giải thích bằng tiếng Việt]

{option_C}
→ [Đúng/Sai]. [Giải thích bằng tiếng Việt]

{option_D}
→ [Đúng/Sai]. [Giải thích bằng tiếng Việt]

""".strip()