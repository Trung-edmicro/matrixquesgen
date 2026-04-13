

PROMPTS_ENGLISH_THCS_MAPPING = {
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
    "Sắp xếp/tìm câu mở đoạn": "TA_Sap_xep_tim_cau_mo_doan.md",
    "Sắp xếp/tìm câu kết đoạn": "TA_Sap_xep_tim_cau_ket_doan.md",
    "Hoàn thành câu - từ cho trước": "TA_Hoan_thanh_cau_tu_cho_truoc.md",
    "Tự luận/Kết hợp câu": "TA_Tu_luan_ket_hop_cau.md",
    "Tự luận/Viết lại câu": "TA_Tu_luan_viet_lai_cau.md",
    "Tự luận/Dạng đúng của từ": "TA_Tu_luan_dang_dung_cua_tu.md",
    "Tự luận/sắp xếp từ": "TA_Tu_luan_sap_xep_tu.md",
    "Tự luận/Hoàn thành câu dùng từ cho trước": "TA_Tu_luan_Hoan_thanh_cau_dung_tu_cho_truoc.md"
}

COMPLETE_THE_SENTENCE_USING_THE_GIVEN_WORD_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{
  "questions": [
    {
      "number": <số thứ tự câu hỏi, integer>,
      "given_words": "<chuỗi từ/cụm từ cho trước, ngăn cách bằng dấu ' / '>",
      "sentence_stem": "<phần đầu câu nếu có, nếu không thì để chuỗi rỗng ''>",
      "answer": "<câu hoàn chỉnh đúng, viết hoa đầu câu và có dấu câu>",
      "knowledge": "<tên cấu trúc/ngữ pháp chính>",
      "explanation": "<giải thích từng bước cách dựng câu từ các từ đã cho, bao gồm chia động từ, thêm từ chức năng>",
      "full_sentence": "<câu hoàn chỉnh đúng (lặp lại để nhấn mạnh)>",
      "translation": "<dịch nghĩa câu hoàn chỉnh sang tiếng Việt>"
    }
  ]
}
"""

SENTENCE_BUILDING_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{
  "questions": [
    {
      "number": <số thứ tự câu hỏi, integer>,

      "given_words": "<chuỗi từ/cụm từ cho trước, ngăn cách bằng dấu ' / '>",

      "options": {
        "A": "<câu hoàn chỉnh A>",
        "B": "<câu hoàn chỉnh B>",
        "C": "<câu hoàn chỉnh C>",
        "D": "<câu hoàn chỉnh D>"
      },

      "answer": "<A/B/C/D>",

      "knowledge": "<tên nội dung kiến thức chính>",

      "explanation": {
        "steps": [
          "<giải thích bước 1: quy tắc quan trọng nhất>",
          "<giải thích bước 2 nếu cần>",
          "<giải thích bước 3 nếu cần>"
        ],
        "correct_sentence": "<câu đúng hoàn chỉnh>"
      },

      "translation": "<dịch câu đúng sang tiếng Việt>"
    }
  ]
}
""".strip()

OPENING_AND_ORDERING_SENTENCE_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "question_groups": [
    {{
      "group_number": <số thứ tự nhóm/cặp câu hỏi, integer>,

      "shared_stem": {{
        "range": "<ví dụ: from 17 to 18>",
        "text": "<đoạn chứa 2 chỗ trống, ví dụ: (17) ______ ... (18) ______ ...>"
      }},

      "opening_question": {{
        "question_number": <số câu hỏi, integer>,
        "options": {{
          "A": "<câu mở A>",
          "B": "<câu mở B>",
          "C": "<câu mở C>",
          "D": "<câu mở D>"
        }},
        "answer": "<A/B/C/D>",
        "knowledge": "<nếu MATRIX_TABLE yêu cầu thì ghi, nếu không để ''>",
        "explanation": {{
          "reasoning": "<giải thích vì sao đáp án đúng khái quát được toàn đoạn; vì sao các phương án khác sai (quá cụ thể/lạc chủ đề/sai trọng tâm)>",
          "correct_sentence": "<nguyên văn câu mở đúng>"
        }}
      }},

      "ordering_question": {{
        "question_number": <số câu hỏi tiếp theo, integer>,
        "sentences": {{
          "a": "<câu a>",
          "b": "<câu b>",
          "c": "<câu c>"
        }},
        "options": {{
          "A": "<thứ tự, ví dụ: a - b - c>",
          "B": "<thứ tự>",
          "C": "<thứ tự>",
          "D": "<thứ tự>"
        }},
        "answer": "<A/B/C/D>",
        "knowledge": "<nếu MATRIX_TABLE yêu cầu thì ghi, nếu không để ''>",
        "explanation": {{
          "steps": [
            "<giải thích bước 1>",
            "<giải thích bước 2>",
            "<giải thích bước 3 nếu có>"
          ],
          "correct_order": "<thứ tự đúng, ví dụ: b - a - c>",
          "full_passage": "<toàn bộ đoạn văn hoàn chỉnh sau khi điền đúng>",
          "translation": "<dịch đoạn văn hoàn chỉnh sang tiếng Việt>"
        }}
      }}
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()

ORDERING_AND_CLOSING_SENTENCE_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "question_groups": [
    {{
      "group_number": <số thứ tự nhóm/cặp câu hỏi, integer>,

      "ordering_question": {{
        "question_number": <số câu hỏi, integer>,
        "passage_intro": "<phần đoạn văn trước chỗ trống, kết thúc bằng dấu _____.>",
        "sentences": {{
          "a": "<câu a>",
          "b": "<câu b>",
          "c": "<câu c>"
        }},
        "options": {{
          "A": "<thứ tự, ví dụ: a - b - c>",
          "B": "<thứ tự>",
          "C": "<thứ tự>",
          "D": "<thứ tự>"
        }},
        "answer": "<A/B/C/D>",
        "explanation": {{
          "steps": [
            "<giải thích bước 1>",
            "<giải thích bước 2>",
            "<giải thích bước 3 nếu có>"
          ],
          "correct_order": "<thứ tự đúng, ví dụ: c - a - b>",
          "full_passage": "<toàn bộ đoạn văn hoàn chỉnh sau khi điền đúng>",
          "translation": "<dịch đoạn văn hoàn chỉnh sang tiếng Việt>"
        }}
      }},

      "closing_question": {{
        "question_number": <số câu hỏi tiếp theo, integer>,
        "options": {{
          "A": "<câu kết A>",
          "B": "<câu kết B>",
          "C": "<câu kết C>",
          "D": "<câu kết D>"
        }},
        "answer": "<A/B/C/D>",
        "knowledge": "<nếu MATRIX_TABLE yêu cầu thì ghi, nếu không thì để chuỗi rỗng ''>",
        "explanation": {{
          "option_analysis": {{
            "A": "<dịch nghĩa câu A>",
            "B": "<dịch nghĩa câu B>",
            "C": "<dịch nghĩa câu C>",
            "D": "<dịch nghĩa câu D>"
          }},
          "reasoning": "<giải thích vì sao đáp án đúng phù hợp nhất với mạch đoạn văn, có thể kèm loại phương án sai>"
        }}
      }}
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()



ERROR_IDENTIFICATION_THCS_JSON_SCHEMA = """
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

WORD_REORDERING_THCS_JSON_SCHEMA = """
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

PRONUNCIATION_STRESS_THCS_JSON_SCHEMA = """
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
""".strip()



LOGICAL_THINKING_THCS_JSON_SCHEMA = """
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
""".strip()


SYNONYM_ANTONYM_THCS_JSON_SCHEMA = """
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


DIALOGUE_COMPLETION_THCS_JSON_SCHEMA = """
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
""".strip()


SENTENCE_COMPLETION_THPT_JSON_SCHEMA = """
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


ESSAY_SENTENCE_REWRITING_THCS_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "original_sentence": "<câu gốc tiếng Anh>",

      "given_word": "<từ/cụm từ gợi ý IN HOA>",

      "rewrite_prompt": "<phần đầu câu viết lại đã cho sẵn>",

      "answer": "<phần còn lại của câu viết lại>",

      "knowledge": "<tên cấu trúc/ngữ pháp chính>",

      "explanation": "<giải thích cấu trúc và cách áp dụng vào câu này>",

      "translation": {
        "original": "<dịch câu gốc sang tiếng Việt>",
        "rewritten": "<dịch câu viết lại hoàn chỉnh sang tiếng Việt>"
      }
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()

ESSAY_COMBINE_SENTENCES_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "sentence_1": "<câu gốc thứ nhất>",

      "sentence_2": "<câu gốc thứ hai>",

      "given_word": "<từ/cụm từ gợi ý (IN HOA)>",

      "combined_sentence": "<câu hoàn chỉnh sau khi kết hợp>",

      "knowledge": "<tên cấu trúc: and / but / because / although / relative clause...>",

      "explanation": "<giải thích cách dùng cấu trúc, mối quan hệ nghĩa giữa 2 câu và cách kết hợp>",

      "translation": "<dịch câu hoàn chỉnh sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


ESSAY_WORD_ORDERING_THCS_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "given_words": "<chuỗi từ/cụm từ đã xáo trộn, ngăn cách bằng ' / ' và bao gồm dấu câu>",

      "answer": "<câu hoàn chỉnh đúng>",

      "structure": "<tên cấu trúc/ngữ pháp chính>",

      "full_sentence": "<câu hoàn chỉnh đúng (lặp lại)>",

      "explanation": "<giải thích cấu trúc câu và lý do sắp xếp theo thứ tự đó>",

      "translation": "<dịch câu hoàn chỉnh sang tiếng Việt>"
    }}
  ]
}}
Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()


ESSAY_WORD_FORM_SENTENCE_COMPLETION_THCS_JSON_SCHEMA = """
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
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()

ESSAY_WORD_PROMPT_SENTENCE_COMPLETION_THCS_JSON_SCHEMA = """
Trả về DUY NHẤT một JSON object hợp lệ, KHÔNG markdown, KHÔNG text ngoài JSON.

{{
  "questions": [
    {{
      "number": <số thứ tự câu hỏi, integer>,

      "given_prompts": "<chuỗi từ/cụm từ ngăn cách bằng dấu ' / '>",

      "sentence_starter": "<phần đầu câu nếu có, nếu không thì để null>",

      "answer": "<câu hoàn chỉnh đúng (viết hoa đầu câu, có dấu chấm)>",

      "knowledge": "<tên kiến thức: It takes / present simple / to-infinitive...>",

      "explanation": "<giải thích cách dựng câu: cấu trúc, chia động từ, thêm từ cần thiết>",

      "translation": "<dịch câu hoàn chỉnh sang tiếng Việt>"
    }}
  ]
}}

Quy tắc bắt buộc:
- questions là mảng có đúng {N_Q} phần tử
- Đánh số "number" bắt đầu từ {START_NUM}
- answer chỉ là 1 ký tự in hoa: A, B, C hoặc D
- KHÔNG thêm bất kỳ text nào ngoài JSON
""".strip()