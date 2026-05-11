PROMPTS = {
    "Điền từ": "TA_Dien_tu.md",
    "Sắp xếp": "TA_sap_xep.md",
    "Đọc hiểu": "TA_Doc_hieu.md",
    "Điền cụm từ/điền câu": "TA_Dien_cau_cum_tu.md",
    "Hoàn thành câu" : "TA_Hoan_thanh_Cau.md",
    "Đồng nghĩa/Trái nghĩa": "TA_Dong_nghia_trai_nghia.md",
    "Tìm lỗi sai": "TA_Tim_loi_sai.md" ,
    "Kết hợp/viết lại câu": "TA_Viet_lai_cau_ket_hop_cau.md",
    "Sắp xếp từ": "TA_Sap_xep_tu.md",
    "Phát âm/Trọng âm": "TA_Phat_am_trong_am.md",
    "Câu giao tiếp": "TA_Cau_giao_tiep.md",
    "Tư duy/Tình huống": "TA_Tinh_huong_tu_duy.md",
    "Hoàn thành câu - từ cho trước": "TA_Hoan_thanh_cau_tu_cho_truoc.md",
    "Tự luận/Kết hợp câu": "TA_Tu_luan_ket_hop_cau.md",
    "Tự luận/Viết lại câu": "TA_Tu_luan_viet_lai_cau.md",
    "Tự luận/Dạng đúng của từ": "TA_Tu_luan_dang_dung_cua_tu.md",
    "Tự luận/sắp xếp từ": "TA_Tu_luan_sap_xep_tu.md",
    "Tự luận/Hoàn thành câu dùng từ cho trước": "TA_Tu_luan_Hoan_thanh_cau_dung_tu_cho_truoc.md"
}

# ============================
# JSON OUTPUT SCHEMAS (thay thế output_rule dạng text)
# ============================

# ── CLOZE / GAP / RC ────────────────────────────────────────────
# Schema dùng chung cho Điền từ, Điền cụm từ/điền câu, Đọc hiểu
# (chỉ khác nhau ở có/không có passage_title)

CLOZE_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.
Trường "explaination" không được ghi thêm chữ "Lời giải", không ghi chữ "Phương án 1", Phương án 2", "Phương án n"
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
Trường "explaination" không được ghi thêm chữ "Lời giải", không ghi chữ "Phương án 1", Phương án 2", "Phương án n"
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
""".strip()

SENTENCE_COMPLETION_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
  {{
      "number": <số thứ tự câu hỏi, integer>,
      "question": "<câu hoàn chỉnh có đúng 1 chỗ trống ______>",
      "option_a": "<đáp án A>",
      "option_b": "<đáp án B>",
      "option_c": "<đáp án C>",
      "option_d": "<đáp án D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<lời giải theo đúng quy tắc TEXT_TYPE (Grammar / Vocabulary / Word Formation)>",
      "translation": "<dịch nghĩa câu hoàn chỉnh sau khi điền đáp án>"
  }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- Mỗi "question" phải có đúng 1 chỗ trống dạng ______
- Mỗi câu có đủ 4 phương án A, B, C, D
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- explanation phải tuân thủ đúng quy tắc theo TEXT_TYPE:
  + Grammar: nêu công thức + cách dùng ngắn gọn
  + Vocabulary: liệt kê 4 phương án và giải nghĩa, có “→ phù hợp ngữ cảnh”
  + Word Formation: phân tích từ loại + liệt kê 4 dạng từ, có “→ chọn”
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


SYNONYM_ANTONYM_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "question": "<câu chứa từ/cụm từ được hỏi, định dạng <strong><u>word</u></strong> nếu có",
      "type": "<synonym hoặc antonym>",
      "option_a": "<đáp án A>",
      "option_b": "<đáp án B>",
      "option_c": "<đáp án C>",
      "option_d": "<đáp án D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<lời giải: gồm nghĩa từ gốc + nghĩa 4 phương án + đánh dấu đáp án đúng (→ phù hợp ngữ cảnh hoặc → trái nghĩa với ...) + giải thích ngắn>",
      "translation": "<dịch nghĩa câu hoàn chỉnh sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- "type" chỉ nhận giá trị: "synonym" hoặc "antonym"
- "question" phải chứa từ/cụm từ được hỏi ở dạng <strong><u>word</u></strong> nếu có
- Mỗi câu có đủ 4 phương án A, B, C, D
- TẤT CẢ phương án phải cùng từ loại với từ gốc
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- explanation phải:
  + Ghi nghĩa của từ gốc (kèm loại từ)
  + Ghi nghĩa của cả 4 phương án (kèm loại từ)
  + Đánh dấu đúng phương án bằng:
    - “→ phù hợp ngữ cảnh (= từ gốc)” với synonym
    - “→ trái nghĩa với {{từ gốc}}” với antonym
  + Có giải thích ngắn vì sao đúng trong ngữ cảnh
- Với antonym: nên có ít nhất 1 distractor là từ đồng nghĩa với từ gốc
- translation là câu đã hiểu đầy đủ nghĩa theo ngữ cảnh
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


ERROR_IDENTIFICATION_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "question": "<câu chứa đúng 4 phần được gạch chân dạng <u>...</u>",
      "option_a": "<phần gạch chân tương ứng A>",
      "option_b": "<phần gạch chân tương ứng B>",
      "option_c": "<phần gạch chân tương ứng C>",
      "option_d": "<phần gạch chân tương ứng D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<giải thích lỗi sai (1–3 câu), nêu rõ quy tắc đúng>",
      "correction": "<từ/cụm sai> → <từ/cụm đúng>",
      "translation": "<dịch nghĩa câu đã sửa sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- "question" phải chứa đúng 4 phần gạch chân dạng <u>...</u>
- 4 phần gạch chân phải trùng chính tả với option_a, option_b, option_c, option_d
- Mỗi câu có đủ 4 phương án A, B, C, D
- Chỉ có ĐÚNG 1 đáp án đúng (phần chứa lỗi)
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- explanation:
  + Chỉ giải thích lỗi sai và quy tắc đúng
  + KHÔNG nhắc A/B/C/D
  + Ngắn gọn 1–3 câu
- correction phải đúng format: "<sai> → <đúng>"
- translation là câu đã sửa hoàn chỉnh
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


SENTENCE_TRANSFORMATION_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.
{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "type": "<rewriting hoặc combination>",
      "instruction": "<Sentence rewriting: Choose A, B, C or D that has the CLOSEST meaning to the given sentence in each question. | Sentence combination: Choose A, B, C or D that has the CLOSEST meaning to the given pair of sentences in each question.>",
      "question": "<1 câu gốc nếu rewriting, hoặc 2 câu gốc nếu combination>",
      "option_a": "<đáp án A>",
      "option_b": "<đáp án B>",
      "option_c": "<đáp án C>",
      "option_d": "<đáp án D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<lời giải: gồm chọn đáp án đúng + phân tích 4 phương án (dịch + nhận xét) theo format>",
      "translation": "<dịch nghĩa câu gốc>",
      "correct_translation": "<dịch nghĩa phương án đúng>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- "type" chỉ nhận: "rewriting" hoặc "combination"

- instruction:
  + Nếu type = rewriting → dùng:
    "Sentence rewriting: Choose A, B, C or D that has the CLOSEST meaning to the given sentence in each question."
  + Nếu type = combination → dùng:
    "Sentence combination: Choose A, B, C or D that has the CLOSEST meaning to the given pair of sentences in each question."

- rewriting: "question" chứa 1 câu gốc
- combination: "question" chứa 2 câu gốc

- Mỗi câu có đủ 4 phương án A, B, C, D
- Chỉ có 1 đáp án đúng duy nhất (cùng nghĩa 100% với câu gốc)
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D

- explanation phải:
  + Có dòng chọn đáp án đúng (chỉ ghi ký tự)
  + Phân tích 4 phương án: mỗi phương án gồm câu tiếng Anh + dịch + nhận xét đúng/sai
  + Chỉ rõ vì sao đáp án đúng giữ nguyên nghĩa và đúng cấu trúc

- translation là nghĩa của câu gốc
- correct_translation là nghĩa của phương án đúng

- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()

WORD_REORDERING_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.
{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "word_list": "<dãy từ xáo trộn, phân tách bằng dấu '/' và kết thúc bằng dấu câu>",
      "option_a": "<câu sắp xếp A>",
      "option_b": "<câu sắp xếp B>",
      "option_c": "<câu sắp xếp C>",
      "option_d": "<câu sắp xếp D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<giải thích cấu trúc ngữ pháp hoặc logic trật tự từ (dạng văn xuôi)>",
      "translation": "<dịch nghĩa câu đúng sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- "word_list":
  + Các từ/cụm từ phải được phân tách bằng dấu "/"
  + Có dấu câu (., ?, !) ở cuối
  + Không được theo trật tự câu đúng
- Mỗi câu có đủ 4 phương án A, B, C, D
- Tất cả phương án phải dùng ĐỦ các từ trong word_list (không thiếu, không thừa)
- Chỉ có 1 đáp án đúng duy nhất (đúng ngữ pháp và tự nhiên nhất)
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- explanation:
  + Giải thích cấu trúc ngữ pháp hoặc trật tự từ
  + KHÔNG nhắc A/B/C/D
- translation là câu đúng hoàn chỉnh
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


PRONUNCIATION_STRESS_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.
{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "type": "<pronunciation hoặc stress>",
      "option_a": "<từ A (có thể chứa <u>...</u> nếu là phát âm)>",
      "option_b": "<từ B>",
      "option_c": "<từ C>",
      "option_d": "<từ D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<giải thích: nêu từ khác biệt + lý do (âm hoặc trọng âm)>",
      "details": [
        {{
          "word": "<từ>",
          "ipa": "<phiên âm IPA>",
          "pos": "<loại từ>",
          "meaning": "<nghĩa tiếng Việt>"
        }}
      ]
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- "type" chỉ nhận: "pronunciation" hoặc "stress"
- Mỗi câu có đủ 4 phương án A, B, C, D
- Nếu type = pronunciation:
  + Các từ phải có phần gạch chân dạng <u>...</u>
  + 3 từ có cách phát âm giống nhau, 1 từ khác
- Nếu type = stress:
  + 4 từ phải có cùng số âm tiết
  + 3 từ cùng vị trí trọng âm, 1 từ khác
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- explanation:
  + Nêu rõ từ khác biệt và lý do (âm hoặc trọng âm)
  + KHÔNG dùng A/B/C/D
- "details":
  + Gồm đúng 4 phần tử tương ứng 4 từ
  + Mỗi phần tử có: word, ipa, pos, meaning
- Phiên âm phải chuẩn IPA
- KHÔNG thêm bất kỳ text nào ngoài JSON
"""

DIALOGUE_COMPLETION_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.
{{
  "instruction": "Dialogue completion: Choose A, B, C or D to complete each dialogue.",
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "speaker_a": "<lời thoại của người A>",
      "speaker_b": "______",
      "option_a": "<phương án A>",
      "option_b": "<phương án B>",
      "option_c": "<phương án C>",
      "option_d": "<phương án D>",
      "answer": "<A hoặc B hoặc C hoặc D>",
      "explanation": "<lời giải: gồm nghĩa của phương án đúng (→ phù hợp ngữ cảnh) và nghĩa của 3 phương án còn lại>",
      "translation": {{
        "speaker_a": "<dịch lời thoại của A>",
        "speaker_b": "<dịch đáp án đúng>"
      }}
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- "speaker_b" luôn là "______"
- Mỗi câu có đủ 4 phương án A, B, C, D
- Chỉ có 1 đáp án đúng duy nhất
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- explanation:
  + Nêu nghĩa của phương án đúng và đánh dấu “→ phù hợp ngữ cảnh”
  + Nêu nghĩa của 3 phương án còn lại
  + KHÔNG dùng A/B/C/D trong lời giải
- translation:
  + Gồm 2 phần: speaker_a và speaker_b
  + speaker_b là bản dịch của đáp án đúng
- KHÔNG thêm bất kỳ text nào ngoài JSON
"""

LOGICAL_THINKING_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.
{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,
      "type": "<social_interaction | dialogue_response | cause_inference | result_prediction | fact_verification | definition_example>",

      "scenario": "<mô tả tình huống>",

      "speaker_a": "<lời thoại của người A, chỉ dùng nếu là dialogue_response, ngược lại để null>",
      "speaker_b": "<______ nếu là dialogue_response, ngược lại để null>",

      "question": "<câu hỏi chính (nếu KHÔNG có hội thoại)>",

      "option_a": "<phương án A>",
      "option_b": "<phương án B>",
      "option_c": "<phương án C>",
      "option_d": "<phương án D>",

      "answer": "<A hoặc B hoặc C hoặc D>",

      "explanation": "<lời giải: gồm tóm tắt tình huống + nghĩa phương án đúng (→ phù hợp) + nghĩa và lý do sai của 3 phương án còn lại>",

      "translation": {{
        "scenario": "<dịch tình huống>",
        "question": "<dịch câu hỏi nếu có, nếu không thì null>",
        "speaker_a": "<dịch lời thoại A nếu có, nếu không thì null>",
        "speaker_b": "<dịch đáp án đúng nếu có hội thoại, nếu không thì null>"
      }}
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- type phải thuộc 1 trong các giá trị:
  + social_interaction
  + dialogue_response
  + cause_inference
  + result_prediction
  + fact_verification
  + definition_example

- Nếu type = dialogue_response:
  + BẮT BUỘC có speaker_a
  + speaker_b = "______"
  + question có thể null hoặc giữ dạng: "What would be the best response...?"
- Nếu KHÔNG phải dialogue_response:
  + speaker_a = null
  + speaker_b = null
  + BẮT BUỘC có question

- Mỗi câu có đủ 4 phương án A, B, C, D
- Chỉ có 1 đáp án đúng duy nhất
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D

- explanation:
  + Có tóm tắt tình huống
  + Nêu nghĩa phương án đúng và đánh dấu “→ phù hợp”
  + Nêu nghĩa và lý do sai của 3 phương án còn lại
  + KHÔNG dùng A/B/C/D trong lời giải

- translation:
  + Luôn có scenario
  + Nếu không có hội thoại → speaker_a, speaker_b = null
  + Nếu có hội thoại → speaker_b là bản dịch của đáp án đúng

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

READING_COMPREHENSION_EXPLANATION_TEMPLATE = r"""
Quy tắc bắt buộc:
- Cấm tuyệt đối viết A B C D trong phần phân tích đáp án, bắt buộc sử dụng nội dung của từng phương án để làm tiêu đề phân tích
- Cấm tuyệt đối viết lại câu hỏi và đáp án trong lời giải
- Cấm viết chữ Lời giải và chọn đáp án nào đúng
- Không cần viết thông tin, tạm dịch vì cấu trúc json trả về đã yêu cầu
""".strip()




WORD_FORM_SENTENCE_COMPLETION_THPT_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "sentence": "<câu có 1 hoặc nhiều chỗ trống ______>",

      "given_words": [
        "<TỪ GỐC 1 - IN HOA>",
        "<TỪ GỐC 2 - IN HOA nếu có>",
        "<TỪ GỐC 3 - nếu có>"
      ],

      "answers": [
        "<đáp án cho blank 1>",
        "<đáp án cho blank 2>",
        "<đáp án cho blank 3>"
      ],

      "knowledge": "<tên kiến thức chính: word form / verb tense / V-ing / collocation...>",

      "explanation": {{
        "blank_1": "<giải thích vì sao dùng dạng này (loại từ, thì, cấu trúc...)>",
        "blank_2": "<giải thích blank 2 nếu có>",
        "blank_3": "<giải thích blank 3 nếu có>"
      }},

      "translation": "<dịch câu hoàn chỉnh sang tiếng Việt>"
    }
  ]
}}
Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer KHÔNG phải A/B/C/D, mà là phần còn lại của câu
- full_rewritten_sentence = rewrite_prompt + answer
- KHÔNG thêm bất kỳ text nào ngoài JSON
"""


ESSAY_SENTENCE_REWRITING_THPT_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "original_sentence": "<câu gốc tiếng Anh>",

      "rewrite_prompt": "<phần đầu câu viết lại đã cho sẵn>",

      "answer": "<phần còn lại của câu viết lại>",

      "full_rewritten_sentence": "<câu hoàn chỉnh sau khi viết lại>",

      "knowledge": "<tên cấu trúc/ngữ pháp chính>",

      "explanation": "<giải thích cấu trúc và cách áp dụng vào câu này>",

      "translation": {{
        "original": "<dịch câu gốc sang tiếng Việt>",
        "rewritten": "<dịch câu viết lại hoàn chỉnh sang tiếng Việt>"
      }}
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer KHÔNG phải A/B/C/D, mà là phần còn lại của câu
- full_rewritten_sentence = rewrite_prompt + answer
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


ESSAY_COMBINE_SENTENCES_THPT_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "sentence_1": "<câu gốc thứ nhất>",

      "sentence_2": "<câu gốc thứ hai>",

      "rewrite_prompt": "<phần đầu câu đã cho sẵn (ví dụ: Jack, who)>",

      "answer": "<phần còn lại của câu>",

      "combined_sentence": "<câu hoàn chỉnh sau khi kết hợp>",

      "knowledge": "<tên cấu trúc: relative clause / although / because / participle clause...>",

      "explanation": "<giải thích cách dùng cấu trúc, mối quan hệ nghĩa giữa 2 câu và cách kết hợp>",

      "translation": {{
        "original_1": "<dịch câu 1>",
        "original_2": "<dịch câu 2>",
        "combined": "<dịch câu đã kết hợp>"
      }}
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer là phần còn lại của câu (KHÔNG phải A/B/C/D)
- combined_sentence = rewrite_prompt + answer
- rewrite_prompt phải giữ nguyên đề bài cho
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


ESSAY_WORD_ORDERING_THPT_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "given_words": "<chuỗi từ/cụm từ đã xáo trộn, ngăn cách bằng ' / ' và bao gồm dấu câu>",

      "correct_sentence": "<câu hoàn chỉnh đúng>",

      "knowledge": "<tên cấu trúc/ngữ pháp chính (ví dụ: S + V + O / because clause / adverb of frequency...)>",

      "explanation": "<giải thích cách sắp xếp từ, trật tự câu và ý nghĩa>",

      "translation": "<dịch câu hoàn chỉnh sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- correct_sentence là câu hoàn chỉnh đúng (KHÔNG phải A/B/C/D)
- given_words phải giữ nguyên thứ tự đề bài (không tự ý sửa)
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()

ESSAY_WORD_FORM_SENTENCE_COMPLETION_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "sentence": "<câu có chỗ trống ______>", nếu có từ trong ngoặc thì phải viết thường,

       "given_words": [
        "<TỪ GỐC 1 - viết thường>",
        "<TỪ GỐC 2 - viết thường nếu có>",
        "<TỪ GỐC 3 - nếu có>"
      ],

      "answer": "<từ đúng sau khi biến đổi>",

      "full_sentence": "<câu hoàn chỉnh sau khi điền>",

      "knowledge": "<tên kiến thức chính: word form / V-ing / adjective / noun form...>",

      "explanation": "<giải thích vì sao dùng dạng từ này (loại từ, cấu trúc, vị trí trong câu...)",

      "translation": "<dịch câu hoàn chỉnh sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer là từ đúng (KHÔNG phải A/B/C/D)
- given_words phải viết thường
- full_sentence phải đúng ngữ pháp và khớp với answer
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


ESSAY_WORD_PROMPT_SENTENCE_COMPLETION_THPT_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "given_prompts": "<chuỗi từ/cụm từ ngăn cách bằng dấu ' / '>",

      "sentence_starter": "<phần đầu câu nếu đề cho (ví dụ: Binh), nếu không thì null>",

      "full_sentence": "<câu hoàn chỉnh đúng (viết hoa đầu câu, có dấu chấm)>",

      "knowledge": "<tên cấu trúc: present simple / adverb of frequency / It takes / to-infinitive...>",

      "explanation": "<giải thích cách dựng câu: trật tự từ, chia động từ, thêm từ cần thiết>",

      "translation": "<dịch câu hoàn chỉnh sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- full_sentence là câu hoàn chỉnh đúng (KHÔNG phải A/B/C/D)
- given_prompts phải giữ nguyên thứ tự đề bài
- sentence_starter = null nếu đề không cho sẵn
- full_sentence phải sử dụng đầy đủ ý từ given_prompts (có thể thêm từ chức năng cần thiết)
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()