# from fastapi import HTTPException
# import pandas as pd
# from collections import defaultdict
# from pathlib import Path
# import uuid
# import os
# from fastapi.responses import FileResponse
# import shutil
# from api.callApi import get_credentials
# from services.english_generator_service.vertex_async_client import AsyncVertexClient
# import asyncio
# import re
# import html
# from docx import Document
# from docx.shared import Pt
# from docx.enum.text import WD_ALIGN_PARAGRAPH
# import logging
# from google.api_core.exceptions import ResourceExhausted
# from collections import defaultdict, Counter

# logger = logging.getLogger(__name__)
# # ============================
# # CONFIG
# # ============================

# LEVELS = ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"]


# APP_DIR = Path(os.environ['APP_DIR']) if os.environ.get('APP_DIR') else Path(__file__).parent.parent.parent.parent.parent
# PROMPT_DIR = APP_DIR / "data" / "prompts" / "TIENGANH"
# print(f">>>>>> debug APP_DIR: {APP_DIR}")
# UPLOAD_DIR = APP_DIR / "data" / "uploads"
# OUTPUT_DIR = APP_DIR / "data" / "outputs"

# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# # ============================
# # PROMPT LOADER
# # ============================

# def load_prompt(filename: str) -> str:
#     path = PROMPT_DIR / filename
#     if not path.exists():
#         raise Exception(f"Không tìm thấy prompt: {filename}")
#     return path.read_text(encoding="utf-8")

# PROMPTS = {
#     "Điền từ": "TA_Dien_tu.md",
#     "Sắp xếp": "TA_sap_xep.md",
#     "Đọc hiểu": "Doc_hieu.md",
#     "Điền cụm từ/điền câu": "Dien_cau_cum_tu.md"
# }

# # CLOZE_EXPLANATION_TEMPLATE = r"""
# # Question {QNUM}
# # Đáp án: [A/B/C/D]. [từ/cụm đúng]
# # Giải thích: [lý do chọn: quy tắc/collocation/ngữ nghĩa, bám ngữ cảnh]
# # Phân tích sai:
# # [Phương án 1]: [nghĩa/loại từ] – [lý do loại]
# # [Phương án 2]: [nghĩa/loại từ] – [lý do loại]
# # [Phương án 3]: [nghĩa/loại từ] – [lý do loại]

# # Trích bài: "[Viết lại câu gốc, thay (N) bằng đáp án đúng]"
# # Dịch nghĩa: [dịch tự nhiên câu có đáp án]
# # """.strip()

# CLOZE_EXPLANATION_TEMPLATE = r"""
# Question {QNUM}: 
# A. {OPT_A}\t\tB. {OPT_B}\t\tC. {OPT_C}\t\tD. {OPT_D}

# Lời giải
# Chọn {ANSWER}

# {EXPLANATION}

# Trích bài: {QUOTE}
# Tạm dịch: {TRANSLATION}
# """.strip()


# SILENT_PHASE_EXPLANATION_TEMPLATE = r"""
# Question {question_number}.
# {question_stem}

# A. {option_A}
# B. {option_B}
# C. {option_C}
# D. {option_D}

# ====================

# Lời giải:
# Chọn {correct_answer}

# Phân tích đáp án đúng:
# - Ngữ pháp: [Phân tích cấu trúc câu: mệnh đề quan hệ / V-ing / liên từ / trạng ngữ / song song / logic ngữ nghĩa...]
# - Logic – Ngữ cảnh: [Giải thích vì sao đáp án này phù hợp mạch ý đoạn văn]
# - Từ khóa liên kết: [Chỉ ra keyword nối với câu trước/sau]
# → Kết luận: [Vì sao đây là đáp án chính xác nhất]

# Phân tích đáp án sai:
# -option A: [Sai ở điểm nào: ngữ pháp / nghĩa / logic / quá cực đoan / trái ngữ cảnh]
# -option B: [Sai vì...]
# -option C: [Sai vì...]
# -option D: [Sai vì...]

# (Lưu ý: Nếu đáp án đúng là A thì vẫn phải phân tích A ở phần đúng, 
# và phần "Phân tích đáp án sai" chỉ phân tích các phương án còn lại.)

# Trích bài:
# "[Trích nguyên văn câu hoặc cụm chứa đáp án]"

# Tạm dịch:
# [Dịch chính xác câu chứa đáp án sang tiếng Việt]

# Chiến lược làm nhanh:
# - Xác định loại câu: (Grammar completion / Logical connector / Result clause / Relative clause / Inference...)
# - Xác định sắc thái đoạn văn: (Positive / Contrast / Warning / Cause–Effect)
# - Loại các phương án trái mạch hoặc cực đoan trước.
# """.strip()

# ARRANGE_SOLUTION_TEMPLATE = r"""
# Lời giải
# Chọn [A/B/C/D]
# [Ghép đúng thứ tự – mỗi mảnh/turn 1 dòng, giữ nguyên tên nhân vật nếu có]
# Tạm dịch:
# [Dịch từng dòng tương ứng, ngắn gọn tự nhiên]
# """.strip()

# READING_COMPREHENSION_EXPLANATION_TEMPLATE = r"""
# Question {question_number}. {question_content}

# A. {option_A}
# B. {option_B}
# C. {option_C}
# D. {option_D}

# Yêu cầu trình bày theo format sau:

# Lời giải:
# Chọn {correct_answer}

# - {option_A_keyword}:
# - Giải thích: {vì sao đúng/sai}

# - {option_B_keyword}:
# - Giải thích: {vì sao đúng/sai}

# - {option_C_keyword}:
# - Giải thích: {vì sao đúng/sai}

# -{option_D_keyword}:
# - Giải thích: {vì sao đúng/sai}

# Thông tin:
# Trích dẫn nguyên văn câu/đoạn trong bài liên quan trực tiếp đến đáp án.

# Tạm dịch:
# Dịch chính xác câu/đoạn trích sang tiếng Việt.
# """.strip()




# # ============================
# # EXCEL EXTRACT LOGIC
# # ============================

# def detect_type_columns(df):
#     col_map = {}
#     for i, col in enumerate(df.columns):
#         col_lower = str(col).lower()
#         if "điền từ" in col_lower:
#             col_map["Điền từ"] = i
#         elif "sắp xếp" in col_lower:
#             col_map["Sắp xếp"] = i
#         elif "đọc hiểu" in col_lower:
#             col_map["Đọc hiểu"] = i
#         elif "điền cụm" in col_lower:
#             col_map["Điền cụm từ/điền câu"] = i
#     return col_map


# def detect_all_levels(row, start_index):
#     found = []
#     for offset in range(4):
#         cell = row.iloc[start_index + offset]
#         if pd.notna(cell) and str(cell).strip() != "":
#             found.append(LEVELS[offset])
#     return found


# # REQUIRED_COUNTS = {
# #     "Điền từ": 6,
# #     "Sắp xếp": 1,
# #     "Đọc hiểu": 9,
# #     "Điền cụm từ/điền câu": 5
# # }


# # def extract_blocks_from_excel(file_path: str):

# #     df = pd.read_excel(file_path, sheet_name="Ma trận")
# #     df.columns = [str(col).strip() for col in df.columns]

# #     meta_cols = ["STT", "Chủ đề", "Số từ", "Độ khó", "Dạng thức bài đọc"]
# #     df[meta_cols] = df[meta_cols].ffill()

# #     type_col_map = detect_type_columns(df)
# #     blocks = []

# #     grouped = df.groupby("STT")

# #     for stt, group in grouped:
# #         topic = group.iloc[0]["Chủ đề"]
# #         word_count = str(group.iloc[0]["Số từ"])
# #         difficulty = group.iloc[0]["Độ khó"]
# #         text_type = group.iloc[0]["Dạng thức bài đọc"]

# #         question_types = defaultdict(list)

# #         for _, row in group.iterrows():
# #             spec = row.get("Đặc tả ma trận")
# #             if pd.isna(spec):
# #                 continue

# #             spec = str(spec).strip()

# #             for q_type, start_col in type_col_map.items():
# #                 levels = detect_all_levels(row, start_col)
# #                 for lv in levels:
# #                     question_types[q_type].append({
# #                         "spec": spec,
# #                         "level": lv
# #                     })

# #         for q_type, questions in question_types.items():
# #             required = REQUIRED_COUNTS.get(q_type)
# #             if required and len(questions) != required:
# #                 raise Exception(
# #                     f"LỖI STT {stt} - {q_type}: yêu cầu {required}, đọc được {len(questions)}"
# #                 )

# #             blocks.append({
# #                 "type": q_type,
# #                 "topic": topic,
# #                 "difficulty": difficulty,
# #                 "text_type": text_type,
# #                 "word_count": word_count,
# #                 "questions": questions
# #             })

# #     return blocks

# META_COLS = ["STT", "Chủ đề", "Số từ", "Độ khó", "Dạng thức bài đọc"]


# def extract_blocks_from_excel(file_path: str):

#     df = pd.read_excel(file_path, sheet_name="Ma trận")
#     df.columns = [str(col).strip() for col in df.columns]

#     df[META_COLS] = df[META_COLS].ffill()

#     type_col_map = detect_type_columns(df)

#     blocks = []

#     # dùng để đếm tổng số câu hỏi theo từng column
#     total_counts = Counter()

#     grouped = df.groupby("STT")

#     for stt, group in grouped:

#         topic = group.iloc[0]["Chủ đề"]
#         word_count = str(group.iloc[0]["Số từ"])
#         difficulty = group.iloc[0]["Độ khó"]
#         text_type = group.iloc[0]["Dạng thức bài đọc"]

#         question_types = defaultdict(list)

#         for _, row in group.iterrows():

#             spec = row.get("Đặc tả ma trận")
#             if pd.isna(spec):
#                 continue

#             spec = str(spec).strip()

#             for q_type, start_col in type_col_map.items():

#                 levels = detect_all_levels(row, start_col)

#                 for lv in levels:
#                     question_types[q_type].append({
#                         "spec": spec,
#                         "level": lv
#                     })

#         # in số câu hỏi theo từng column của STT hiện tại
#         print(f"\n=== STT {stt} ===")

#         for q_type, questions in question_types.items():

#             count = len(questions)

#             print(f"{q_type}: {count} questions")

#             total_counts[q_type] += count

#             blocks.append({
#                 "type": q_type,
#                 "topic": topic,
#                 "difficulty": difficulty,
#                 "text_type": text_type,
#                 "word_count": word_count,
#                 "question_count": count,
#                 "questions": questions
#             })

#     # in tổng toàn file
#     print("\n=== TOTAL QUESTIONS PER COLUMN ===")
#     for q_type, count in total_counts.items():
#         print(f"{q_type}: {count}")

#     return blocks

# # ============================
# # GENERATE DOCX LOGIC
# # ============================

# # def generate_exam_docx(blocks, output_path):

# #     doc = Document()

# #     for block in blocks:

# #         doc.add_heading(f"{block['type']} - {block['topic']}", level=2)

# #         prompt_template = load_prompt(PROMPTS[block["type"]])

# #         for q in block["questions"]:
# #             content = prompt_template.replace("{{spec}}", q["spec"]) \
# #                                      .replace("{{level}}", q["level"])
# #             doc.add_paragraph(content)

# #     doc.save(output_path)
# async def generate_exam_docx(blocks, output_path):

#     credentials, project_id = get_credentials()

#     client = AsyncVertexClient(
#         project_id=project_id,
#         creds=credentials,
#         model="gemini-2.5-pro"
#     )

#     doc = Document()
#     doc.add_heading("ĐỀ THI TIẾNG ANH", level=1)

#     q_count = 1
#     tasks = []
#     block_meta = []

#     for block in blocks:

#         topic     = block["topic"]
#         q_type    = block["type"]
#         text_type = block["text_type"]
#         print(f">>>>>> debug text_type {text_type}")
#         diff      = block["difficulty"]
#         so_tu     = block.get("word_count", "")
#         questions = block["questions"]
#         n_q       = len(questions)

#         # ===============================
#         # 🔥 LOAD PROMPT THEO TYPE
#         # ===============================

#         try:
#             prompt_template = load_prompt(PROMPTS[q_type])
#         except Exception:
#             prompt_template = ""   # fallback rỗng nếu thiếu file

#         specs_list = [
#             f"Câu {i+1}: {q['spec']} (Cấp độ: {q['level']})"
#             for i, q in enumerate(questions)
#         ]

#         # ===============================
#         # 1️⃣ CLOZE
#         # ===============================

#         if q_type == "Điền từ":

#             output_questions = "".join(
#                 [f"Question {q_count+i}:\nA. ... B. ... C. ... D. ...\n"
#                  for i in range(n_q)]
#             )
#             if text_type == "Quảng cáo" or text_type == "Thông báo": 
#                 output_rule = (
#                             "\n\n# CHỈ TRẢ VỀ (TEXT THUẦN)\n"
#                             "TIÊU ĐỀ BÀI ĐỌC(PASSAGE TITLE)\n"
#                             "BÀI ĐỌC (PASSAGE)\n[passage]\n\n"
#                             "## Yêu cầu tuyệt đối: Với dạng thức bài đọc đã được quy thì tiêu đề và nội dung phải tuân thủ theo dạng thức bài đọc đó"
#                             + output_questions +
#                             "\nANSWER KEY\n"
#                             + ", ".join([f"{i+1}-[A/B/C/D]" for i in range(n_q)]) +
#                             "\n\nHƯỚNG DẪN GIẢI CHI TIẾT\n[explanations]\n"
#                 )
#             else:
#                 output_rule = (
#                     "\n\n# CHỈ TRẢ VỀ (TEXT THUẦN)\n"
#                     "BÀI ĐỌC (PASSAGE)\n[passage]\n\n"
#                     + output_questions +
#                     "\nANSWER KEY\n"
#                     + ", ".join([f"{i+1}-[A/B/C/D]" for i in range(n_q)]) +
#                     "\n\nHƯỚNG DẪN GIẢI CHI TIẾT\n[explanations]\n"
#                 )
#             formatted_prompt = (
#                     prompt_template
#                         .replace("{TOPIC_NAME}", topic)
#                         .replace("{TEXT_TYPE}", text_type)
#                         .replace("{DIFFICULTY_LEVEL}", diff)
#                 )

#             ai_input = (
#                 f"{formatted_prompt}\n\n"
#                 f"Chủ đề: {topic}\n"
#                 f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
#                 f"{CLOZE_EXPLANATION_TEMPLATE}\n\n"
#                 f"Số từ: {so_tu}\n"
#                 f"Độ khó: {diff}\n"
#                 f"Dạng thức: {text_type}\n"
#                 f"Số câu: {n_q}\n"
#                 + "\n".join(specs_list)
#                 + output_rule
#             )

#             task = client.generate(prompt=ai_input)
#             tasks.append(task)
#             block_meta.append(("CLOZE", topic))
#             q_count += n_q

#         # ===============================
#         # 2️⃣ ARRANGE
#         # ===============================

#         elif q_type == "Sắp xếp":

#             spec_item = questions[0]

#             ai_input = (
#                 f"{prompt_template}\n\n"
#                 f"Chủ đề: {topic}\n"
#                 f"Độ khó: {diff}\n"
#                 f"Dạng thức: {text_type}\n"
#                 f"Đặc tả ma trận: {spec_item['spec']}\n"
#                 f"Mức độ: {spec_item['level']}\n"
#                 f"Đánh số câu: Question {q_count}\n\n"
#                 f"{ARRANGE_SOLUTION_TEMPLATE}"
#             )

#             task = client.generate(prompt=ai_input)
#             tasks.append(task)
#             block_meta.append(("ARRANGE", topic))
#             q_count += 1

#         # ===============================
#         # 3️⃣ READING COMPREHENSION
#         # ===============================

#         elif q_type == "Đọc hiểu":

#             output_questions = "".join(
#                 [f"Question {q_count+j}:\nA. ... B. ... C. ... D. ...\n"
#                  for j in range(n_q)]
#             )

#             output_rule = (
#                 "\n\n# CHỈ TRẢ VỀ (TEXT THUẦN)\n"
#                 "TIÊU ĐỀ BÀI ĐỌC(PASSAGE TITLE)\n"
#                 "BÀI ĐỌC (PASSAGE)\n[passage]\n\n"
#                 + output_questions +
#                 "\nANSWER KEY\n"
#                 + ", ".join([f"{j+1}-[A/B/C/D]" for j in range(n_q)]) +
#                 "\n\nHƯỚNG DẪN GIẢI CHI TIẾT\n[explanations]\n"
#             )

#             ai_input = (
#                 f"{prompt_template}\n\n"
#                 f"Chủ đề: {topic}\n"
#                 f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
#                 f"{READING_COMPREHENSION_EXPLANATION_TEMPLATE}\n\n"
#                 f"Số từ: {so_tu}\n"
#                 f"Độ khó: {diff}\n"
#                 f"Dạng thức: {text_type}\n"
#                 f"Số câu: {n_q}\n"
#                 + "\n".join(specs_list)
#                 + output_rule
#             )

#             task = client.generate(prompt=ai_input)
#             tasks.append(task)
#             block_meta.append(("RC", topic))
#             q_count += n_q

#         # ===============================
#         # 4️⃣ GAP FILL
#         # ===============================

#         elif q_type == "Điền cụm từ/điền câu":

#             output_questions = "".join(
#                 [f"Question {q_count+j}:\nA. ... B. ... C. ... D. ...\n"
#                  for j in range(n_q)]
#             )

#             output_rule = (
#                 "\n\n# CHỈ TRẢ VỀ (TEXT THUẦN)\n"
#                 "TIÊU ĐỀ BÀI ĐỌC(PASSAGE TITLE)\n"
#                 "BÀI ĐỌC (PASSAGE)\n[passage]\n\n"
#                 + output_questions +
#                 "\nANSWER KEY\n"
#                 + ", ".join([f"{j+1}-[A/B/C/D]" for j in range(n_q)]) +
#                 "\n\nHƯỚNG DẪN GIẢI CHI TIẾT\n[explanations]\n"
#             )

#             ai_input = (
#                 f"{prompt_template}\n\n"
#                 f"Chủ đề: {topic}\n"
#                 f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
#                 f"{SILENT_PHASE_EXPLANATION_TEMPLATE}\n\n"
#                 f"Số từ: {so_tu}\n"
#                 f"Độ khó: {diff}\n"
#                 f"Dạng thức: {text_type}\n"
#                 f"Số câu: {n_q}\n"
#                 + "\n".join(specs_list)
#                 + output_rule
#             )

#             task = client.generate(prompt=ai_input)
#             tasks.append(task)
#             block_meta.append(("GAP", topic))
#             q_count += n_q


#     # semaphore = asyncio.Semaphore(3) 
#     # async def limited_generate(task):
#     #     async with semaphore:
#     #         return await task

#     # tasks = [limited_generate(t) for t in tasks]

#     responses = await asyncio.gather(*tasks, return_exceptions= True)
    
#     # print(f">>>>>> debug 1232132 response {responses}")

#     results = []

#     for (block_type, topic), response_text in zip(block_meta, responses):
#         results.append({
#             "type": block_type,
#             "data": response_text,
#             "title": topic
#         })

#     # doc.save(output_path)
#     generate_docx_from_ai_results(results,output_path)

#     return results


# def generate_docx_from_ai_results(results, output_path):

#     doc = Document()
#     _apply_default_style(doc)

#     for res in results:

#         _add_instruction(doc, res)
#         raw = res.get("data") or ""
#         if res["type"] == "CLOZE":
#             _render_cloze_or_gap(doc, raw, merge_options=True)

#         elif res["type"] == "GAP":
#             _render_cloze_or_gap(doc, raw, merge_options=False)

#         elif res["type"] == "RC":
#             _render_cloze_or_gap(doc, raw, merge_options=False)

#         elif res["type"] == "ARRANGE":
#             _render_arrange(doc, raw)

#         _add_separator(doc)

#     doc.save(output_path)


# def export_docx_from_data(json_data, output_path):
#     """
#     Nhận trực tiếp JSON object (dict)
#     Lấy key 'results'
#     Render docx giống generate_docx_from_ai_results
#     """

#     # 1️⃣ Lấy results từ JSON
#     results = json_data.get("results")

#     if not results:
#         raise Exception("No 'results' found in JSON")

#     # 2️⃣ Tạo document
#     doc = Document()
#     _apply_default_style(doc)

#     # 3️⃣ Render từng block
#     for res in results:

#         _add_instruction(doc, res)

#         raw = res.get("data") or ""
#         res_type = res.get("type")

#         if res_type == "CLOZE":
#             _render_cloze_or_gap(doc, raw, merge_options=True)

#         elif res_type == "GAP":
#             _render_cloze_or_gap(doc, raw, merge_options=False)

#         elif res_type == "RC":
#             _render_cloze_or_gap(doc, raw, merge_options=False)

#         elif res_type == "ARRANGE":
#             _render_arrange(doc, raw)

#         else:
#             print("⚠ Unknown type:", res_type)
#             continue

#         _add_separator(doc)

#     # 4️⃣ Save file
#     doc.save(output_path)

#     return output_path

# # =========================================================
# # STYLE
# # =========================================================

# def _apply_default_style(doc):
#     style = doc.styles['Normal']
#     font = style.font
#     font.name = 'Times New Roman'
#     font.size = Pt(12)


# # =========================================================
# # INSTRUCTION
# # =========================================================

# def _add_instruction(doc, res):

#     instruction = doc.add_paragraph()

#     if res['type'] == "CLOZE":
#         text = (
#             f"Read the following {res.get('title','text')} and mark the letter A, B, C or D "
#             "on your answer sheet to indicate the option that best fits each of the numbered blanks."
#         )

#     elif res['type'] == "ARRANGE":
#         text = (
#             "Mark the letter A, B, C or D on your answer sheet to indicate the best arrangement "
#             "of utterances or sentences to make a meaningful exchange or text."
#         )

#     elif res['type'] == "RC":
#         text = (
#             f"Read the following {res.get('title','text')} and mark the letter A, B, C or D "
#             "on your answer sheet to indicate the correct answer to each question."
#         )

#     else:  # GAP
#         text = (
#             f"Read the following {res.get('title','text')} and mark the letter A, B, C or D "
#             "on your answer sheet to indicate the option that best fits each blank."
#         )

#     run = instruction.add_run(text)
#     run.italic = True


# # =========================================================
# # CLOZE / GAP / RC
# # =========================================================

# def _render_cloze_or_gap(doc, raw_text, merge_options=False):

#     blocks = extract_cloze_sections(raw_text)

#     _render_passage(doc, blocks["passage"])

#     q_lines = normalize_question_lines(blocks["questions"])

#     if merge_options:
#         q_lines = merge_options_single_line(q_lines)

#     _render_questions(doc, q_lines)

#     _render_answer_key(doc, blocks["answer_key"])
#     _render_explanation(doc, blocks["explanation"])


# # def _render_passage(doc, passage):
# #     for line in (passage or "").split('\n'):
# #         line = line.strip()
# #         if not line:
# #             continue
# #         p = doc.add_paragraph()
# #         p.add_run(line)
# #         p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# def _render_passage(doc, passage):

#     bold_ul_pattern = r"\*\*(.*?)\*\*"
#     underline_pattern = r"<u>(.*?)</u>"
#     roman_pattern = r"\[(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\]"

#     combined = f"{bold_ul_pattern}|{underline_pattern}|{roman_pattern}"

#     for line in (passage or "").split("\n"):
#         line = line.strip()
#         if not line:
#             continue

#         p = doc.add_paragraph()

#         pos = 0
#         for m in re.finditer(combined, line):

#             # text trước match
#             if m.start() > pos:
#                 p.add_run(line[pos:m.start()])

#             if m.group(1):  
#                 # **text**
#                 run = p.add_run(m.group(1))
#                 run.bold = True
#                 run.underline = True

#             elif m.group(2):
#                 # <u>text</u>
#                 run = p.add_run(m.group(2))
#                 run.underline = True

#             else:
#                 # [I] [II] ...
#                 run = p.add_run(m.group())
#                 run.bold = True

#             pos = m.end()

#         # phần text còn lại
#         if pos < len(line):
#             p.add_run(line[pos:])

#         p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


# def _render_questions(doc, lines):
#     for line in lines:
#         p = doc.add_paragraph()

#         if re.match(r"^Question\s+\d+[:\.]", line, re.I):
#             r = p.add_run(line)
#             r.bold = True
#         else:
#             p.add_run(line)


# def _render_answer_key(doc, key_block):
#     if not key_block:
#         return

#     doc.add_paragraph().add_run("ANSWER KEY").bold = True

#     pairs = parse_answer_key_block(key_block)

#     if pairs:
#         ak_text = ", ".join([f"{i}-{k}" for i, k in pairs])
#         doc.add_paragraph(ak_text)
#     else:
#         doc.add_paragraph(key_block)


# def _render_explanation(doc, explanation):
#     if not explanation:
#         return

#     doc.add_paragraph().add_run("HƯỚNG DẪN GIẢI CHI TIẾT").bold = True

#     for line in explanation.split('\n'):
#         text = line.strip()
#         if not text:
#             continue
#         p = doc.add_paragraph()
#         add_text_with_markdown_bold(p, text)


# # =========================================================
# # ARRANGE
# # =========================================================

# def _render_arrange(doc, raw_text):

#     parts = extract_arrange_sections(raw_text)

#     q_lines = normalize_question_lines(parts["question_block"])
#     q_lines = merge_options_single_line(q_lines)

#     _render_questions(doc, q_lines)

#     doc.add_paragraph().add_run("Lời giải").bold = True

#     if parts["answer_letter"]:
#         doc.add_paragraph(f"Chọn {parts['answer_letter']}")

#     if parts["solution_text"]:
#         for ln in parts["solution_text"].splitlines():
#             p = doc.add_paragraph()
#             add_text_with_markdown_bold(p, ln.strip())

#     if parts["translation"]:
#         doc.add_paragraph().add_run("Tạm dịch:").bold = True
#         for ln in parts["translation"].splitlines():
#             doc.add_paragraph(ln.strip())


# # =========================================================
# # OPTION MERGE (CHO CLOZE / GAP / ARRANGE)
# # =========================================================

# def merge_options_single_line(lines):

#     merged = []
#     buffer = []

#     for line in lines:

#         if re.match(r"^Question\s+\d+[:\.]", line, re.I):
#             if buffer:
#                 merged.append("    ".join(buffer))
#                 buffer = []
#             merged.append(line)

#         elif re.match(r"^[ABCD]\.\s", line):
#             buffer.append(line.strip())

#         else:
#             if buffer:
#                 merged.append("    ".join(buffer))
#                 buffer = []
#             merged.append(line)

#     if buffer:
#         merged.append("    ".join(buffer))

#     return merged


# def add_text_with_markdown_bold(paragraph, text):
#     clean_text = (text or "").replace("**", "")
#     paragraph.add_run(clean_text)


# def _add_separator(doc):
#     doc.add_paragraph("\n" + "=" * 20 + "\n")

# def add_text_with_markdown_bold(paragraph, text):
#     parts = re.split(r"(\*\*.*?\*\*)", text)
#     for part in parts:
#         if not part:
#             continue
#         if part.startswith("**") and part.endswith("**"):
#             run = paragraph.add_run(part[2:-2])
#             run.bold = True
#         else:
#             paragraph.add_run(part)


# def extract_cloze_sections(raw_text):
#     print(f">>>>>> debug raw_text: {raw_text}")
#     s = html.unescape(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
#     PASS_HDR = "BÀI ĐỌC (PASSAGE)"
#     KEY1 = "ANSWER KEY"
#     EXPL1 = "HƯỚNG DẪN GIẢI CHI TIẾT"
#     EXPL2 = "HƯỚNG DẪN GIẢI"

#     pos_pass = s.find(PASS_HDR)
#     if pos_pass < 0:
#         return {"passage": s[:200], "questions": s[200:], "answer_key": "", "explanation": ""}

#     start_pass = pos_pass + len(PASS_HDR)
#     pos_first_q = s.find("Question", start_pass)
#     if pos_first_q < 0:
#         return {"passage": s[start_pass:].strip(), "questions": "", "answer_key": "", "explanation": ""}

#     passage = s[start_pass:pos_first_q].strip()
#     pos_key = s.find(KEY1, pos_first_q)
#     pos_expl = -1
#     for h in [EXPL1, EXPL2]:
#         p = s.find(h, pos_first_q)
#         if p >= 0:
#             pos_expl = p
#             break

#     cut = min([p for p in [pos_key, pos_expl] if p >= 0], default=len(s))
#     questions = s[pos_first_q:cut].strip()

#     answer_key = ""
#     explanation = ""
#     if pos_key >= 0:
#         key_end = pos_expl if pos_expl > pos_key else len(s)
#         answer_key = s[pos_key + len(KEY1):key_end].strip()
#     if pos_expl >= 0:
#         expl_hdr = EXPL1 if s.find(EXPL1) == pos_expl else EXPL2
#         explanation = s[pos_expl + len(expl_hdr):].strip()

#     return {"passage": passage, "questions": questions,
#             "answer_key": answer_key, "explanation": explanation}


# def extract_arrange_sections(raw_text):
#     s = html.unescape(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
#     result = {"question_block": "", "answer_letter": "", "solution_text": "", "translation": ""}
#     pos_loi = re.search(r"^Lời giải", s, re.MULTILINE)
#     if not pos_loi:
#         result["question_block"] = s
#         return result
#     result["question_block"] = s[:pos_loi.start()].strip()
#     after = s[pos_loi.end():]
#     m_chon = re.search(r"Chọn\s+([ABCD])", after)
#     if m_chon:
#         result["answer_letter"] = m_chon.group(1)
#         after2 = after[m_chon.end():]
#     else:
#         after2 = after
#     pos_tam = after2.find("Tạm dịch:")
#     if pos_tam >= 0:
#         result["solution_text"] = after2[:pos_tam].strip()
#         result["translation"] = after2[pos_tam + len("Tạm dịch:"):].strip()
#     else:
#         result["solution_text"] = after2.strip()
#     return result


# def normalize_question_lines(qtext):
#     lines = []
#     for raw in (qtext or "").splitlines():
#         line = html.unescape(raw).strip()
#         if not line:
#             continue
#         line = re.sub(r"\sA\.\s", "\tA. ", line)
#         line = re.sub(r"\sB\.\s", "\tB. ", line)
#         line = re.sub(r"\sC\.\s", "\tC. ", line)
#         line = re.sub(r"\sD\.\s", "\tD. ", line)
#         lines.append(line)
#     return lines


# def parse_answer_key_block(key_block):
#     s = (key_block or "").replace("\r\n", "\n")
#     pairs = []
#     for m in re.finditer(r"(\d+)\s*[-=:]\s*([ABCD])", s, re.I):
#         pairs.append((int(m.group(1)), m.group(2).upper()))
#     if pairs:
#         return sorted(pairs, key=lambda x: x[0])
#     for m in re.finditer(r"(\d+)\s+([ABCD])\b", s, re.I):
#         pairs.append((int(m.group(1)), m.group(2).upper()))
#     return sorted(pairs, key=lambda x: x[0])


# def merge_options_single_line(lines):
#     """
#     Gom các đáp án A/B/C/D về cùng 1 dòng.
#     """
#     merged = []
#     buffer = []
#     current_question = None

#     for line in lines:
#         # Nếu là Question
#         if re.match(r"^Question\s+\d+[:\.]", line, re.I):
#             # flush câu trước
#             if current_question:
#                 if buffer:
#                     merged.append("\t".join(buffer))
#                     buffer = []
#             merged.append(line)
#             current_question = line

#         # Nếu là đáp án A/B/C/D
#         elif re.match(r"^[ABCD]\.\s", line):
#             buffer.append(line.strip())

#         else:
#             # flush option nếu có
#             if buffer:
#                 merged.append("\t".join(buffer))
#                 buffer = []
#             merged.append(line)

#     # flush cuối
#     if buffer:
#         merged.append("\t".join(buffer))

#     return merged
# # ============================
# # MAIN FLOW
# # ============================

# async def generate_english_flow(file):
#     session_id = str(uuid.uuid4())
#     excel_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
#     output_path = OUTPUT_DIR / f"ENGLISH_EXAM_{session_id}.docx"

#     try:
#         # Save uploaded file
#         with open(excel_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         # Extract blocks
#         blocks = extract_blocks_from_excel(str(excel_path))

#         # Generate docx
#         results = await generate_exam_docx(blocks, str(output_path))

#         # Optional: return file directly
#         # FileResponse(
#         #     path=output_path,
#         #     filename=output_path.name,
#         #     media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#         # )

#         FileResponse(
#             path=str(output_path),
#             filename=f"ENGLISH_EXAM_{session_id}.docx",
#             media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#         )


#         return {
#             "session_id": session_id,
#             "status": "success",
#             "message": "Generate English exam successfully",
#             "results": results
#         }


#     except Exception as e:
#         logger.exception("Error while generating English exam")
        

#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to generate English exam: {str(e)}"
#         )


from fastapi import HTTPException
import pandas as pd
from collections import defaultdict
from pathlib import Path
import uuid
import os
import json
from fastapi.responses import FileResponse
import shutil
from api.callApi import get_credentials
from services.english_generator_service.vertex_async_client import AsyncVertexClient
import asyncio
import re
import html
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import logging
from google.api_core.exceptions import ResourceExhausted
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

# ============================
# CONFIG
# ============================

LEVELS = ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"]

APP_DIR = Path(os.environ['APP_DIR']) if os.environ.get('APP_DIR') else Path(__file__).parent.parent.parent.parent.parent
PROMPT_DIR = APP_DIR / "data" / "prompts" / "TIENGANH"
print(f">>>>>> debug APP_DIR: {APP_DIR}")
UPLOAD_DIR = APP_DIR / "data" / "uploads"
OUTPUT_DIR = APP_DIR / "data" / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================
# PROMPT LOADER
# ============================

def load_prompt(filename: str) -> str:
    path = PROMPT_DIR / filename
    if not path.exists():
        raise Exception(f"Không tìm thấy prompt: {filename}")
    return path.read_text(encoding="utf-8")

PROMPTS = {
    "Điền từ": "TA_Dien_tu.md",
    "Sắp xếp": "TA_sap_xep.md",
    "Đọc hiểu": "Doc_hieu.md",
    "Điền cụm từ/điền câu": "Dien_cau_cum_tu.md"
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
  "question_stem": "<mô tả yêu cầu bài sắp xếp>",
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
Question {question_number}.
{question_stem}

A. {option_A}
B. {option_B}
C. {option_C}
D. {option_D}

====================

Lời giải:
Chọn {correct_answer}

Phân tích đáp án đúng:
- Ngữ pháp: [Phân tích cấu trúc câu]
- Logic – Ngữ cảnh: [Giải thích vì sao đáp án này phù hợp]
- Từ khóa liên kết: [Chỉ ra keyword nối với câu trước/sau]
→ Kết luận: [Vì sao đây là đáp án chính xác nhất]

Phân tích đáp án sai:
-option A: [Sai ở điểm nào]
-option B: [Sai vì...]
-option C: [Sai vì...]
-option D: [Sai vì...]

Trích bài: "[Trích nguyên văn câu chứa đáp án]"
Tạm dịch: [Dịch chính xác sang tiếng Việt]
""".strip()

ARRANGE_SOLUTION_TEMPLATE = r"""
Lời giải
Chọn [A/B/C/D]
[Ghép đúng thứ tự]
Tạm dịch:
[Dịch từng dòng tương ứng]
""".strip()

READING_COMPREHENSION_EXPLANATION_TEMPLATE = r"""
Question {question_number}. {question_content}

A. {option_A}
B. {option_B}
C. {option_C}
D. {option_D}

Lời giải:
Chọn {correct_answer}

- {option_A_keyword}: Giải thích vì sao đúng/sai
- {option_B_keyword}: Giải thích vì sao đúng/sai
- {option_C_keyword}: Giải thích vì sao đúng/sai
- {option_D_keyword}: Giải thích vì sao đúng/sai

Thông tin: [Trích dẫn nguyên văn]
Tạm dịch: [Dịch sang tiếng Việt]
""".strip()


# ============================
# EXCEL EXTRACT LOGIC
# ============================

def detect_type_columns(df):
    col_map = {}
    for i, col in enumerate(df.columns):
        col_lower = str(col).lower()
        if "điền từ" in col_lower:
            col_map["Điền từ"] = i
        elif "sắp xếp" in col_lower:
            col_map["Sắp xếp"] = i
        elif "đọc hiểu" in col_lower:
            col_map["Đọc hiểu"] = i
        elif "điền cụm" in col_lower:
            col_map["Điền cụm từ/điền câu"] = i
    return col_map


def detect_all_levels(row, start_index):
    found = []
    for offset in range(4):
        cell = row.iloc[start_index + offset]
        if pd.notna(cell) and str(cell).strip() != "":
            found.append(LEVELS[offset])
    return found


META_COLS = ["STT", "Chủ đề", "Số từ", "Độ khó", "Dạng thức bài đọc"]


def extract_blocks_from_excel(file_path: str):

    df = pd.read_excel(file_path, sheet_name="Ma trận")
    df.columns = [str(col).strip() for col in df.columns]
    df[META_COLS] = df[META_COLS].ffill()

    type_col_map = detect_type_columns(df)
    blocks = []
    total_counts = Counter()
    grouped = df.groupby("STT")

    for stt, group in grouped:
        topic = group.iloc[0]["Chủ đề"]
        word_count = str(group.iloc[0]["Số từ"])
        difficulty = group.iloc[0]["Độ khó"]
        text_type = group.iloc[0]["Dạng thức bài đọc"]
        question_types = defaultdict(list)

        for _, row in group.iterrows():
            spec = row.get("Đặc tả ma trận")
            if pd.isna(spec):
                continue
            spec = str(spec).strip()
            for q_type, start_col in type_col_map.items():
                levels = detect_all_levels(row, start_col)
                for lv in levels:
                    question_types[q_type].append({"spec": spec, "level": lv})

        print(f"\n=== STT {stt} ===")
        for q_type, questions in question_types.items():
            count = len(questions)
            print(f"{q_type}: {count} questions")
            total_counts[q_type] += count
            blocks.append({
                "type": q_type,
                "topic": topic,
                "difficulty": difficulty,
                "text_type": text_type,
                "word_count": word_count,
                "question_count": count,
                "questions": questions
            })

    print("\n=== TOTAL QUESTIONS PER COLUMN ===")
    for q_type, count in total_counts.items():
        print(f"{q_type}: {count}")

    return blocks


# ============================
# JSON PARSE HELPERS
# ============================

def _safe_parse_json(raw: str) -> dict | None:
    """
    Cố gắng parse JSON từ response của AI.
    Xử lý trường hợp AI trả về markdown fences hoặc text thừa.
    """
    if not raw:
        return None

    # Strip markdown code fences nếu có
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Tìm JSON object đầu tiên
    start = text.find("{")
    if start == -1:
        logger.warning("No JSON object found in AI response")
        return None

    # Tìm closing brace tương ứng (depth counting)
    depth = 0
    end = -1
    in_string = False
    escape_next = False

    for i, ch in enumerate(text[start:], start=start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        logger.warning("Could not find closing brace in AI response")
        return None

    json_str = text[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}. Attempting cleanup...")

        # Cleanup: loại bỏ trailing commas trước } hoặc ]
        json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e2:
            logger.error(f"JSON parse failed after cleanup: {e2}")
            return None


# ============================
# GENERATE DOCX LOGIC
# ============================

async def generate_exam_docx(blocks, output_path):

    credentials, project_id = get_credentials()

    client = AsyncVertexClient(
        project_id=project_id,
        creds=credentials,
        model="gemini-2.5-pro"
    )

    doc = Document()
    doc.add_heading("ĐỀ THI TIẾNG ANH", level=1)

    q_count = 1
    tasks = []
    block_meta = []

    for block in blocks:

        topic     = block["topic"]
        q_type    = block["type"]
        text_type = block["text_type"]
        print(f">>>>>> debug text_type {text_type}")
        diff      = block["difficulty"]
        so_tu     = block.get("word_count", "")
        questions = block["questions"]
        n_q       = len(questions)

        try:
            prompt_template = load_prompt(PROMPTS[q_type])
        except Exception:
            prompt_template = ""

        specs_list = [
            f"Câu {i+1}: {q['spec']} (Cấp độ: {q['level']})"
            for i, q in enumerate(questions)
        ]

        # ===============================
        # 1️⃣ CLOZE (Điền từ)
        # ===============================

        if q_type == "Điền từ":

            formatted_prompt = (
                prompt_template
                    .replace("{TOPIC_NAME}", topic)
                    .replace("{TEXT_TYPE}", text_type)
                    .replace("{DIFFICULTY_LEVEL}", diff)
            )

            # Chọn schema có/không có tiêu đề tùy text_type
            has_title = text_type in ("Quảng cáo", "Thông báo", "Advertisement", "Announcement")
            if has_title:
                output_rule = CLOZE_WITH_TITLE_JSON_SCHEMA.format(
                    TEXT_TYPE=text_type,
                    N_Q=n_q,
                    START_NUM=q_count
                )
            else:
                output_rule = CLOZE_JSON_SCHEMA.format(
                    N_Q=n_q,
                    START_NUM=q_count
                )

            ai_input = (
                f"{formatted_prompt}\n\n"
                f"Chủ đề: {topic}\n"
                f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
                f"{CLOZE_EXPLANATION_TEMPLATE}\n\n"
                f"Số từ: {so_tu}\n"
                f"Độ khó: {diff}\n"
                f"Dạng thức: {text_type}\n"
                f"Số câu: {n_q}\n"
                + "\n".join(specs_list)
                + "\n\n## OUTPUT FORMAT\n"
                + output_rule
            )

            task = client.generate(prompt=ai_input)
            tasks.append(task)
            block_meta.append(("CLOZE", topic, n_q, q_count))
            q_count += n_q

        # ===============================
        # 2️⃣ ARRANGE (Sắp xếp)
        # ===============================

        elif q_type == "Sắp xếp":

            spec_item = questions[0]
            output_rule = ARRANGE_JSON_SCHEMA.format(START_NUM=q_count)

            ai_input = (
                f"{prompt_template}\n\n"
                f"Chủ đề: {topic}\n"
                f"Độ khó: {diff}\n"
                f"Dạng thức: {text_type}\n"
                f"Đặc tả ma trận: {spec_item['spec']}\n"
                f"Mức độ: {spec_item['level']}\n"
                f"Đánh số câu: Question {q_count}\n\n"
                f"## OUTPUT FORMAT\n"
                + output_rule
            )

            task = client.generate(prompt=ai_input)
            tasks.append(task)
            block_meta.append(("ARRANGE", topic, 1, q_count))
            q_count += 1

        # ===============================
        # 3️⃣ READING COMPREHENSION (Đọc hiểu)
        # ===============================

        elif q_type == "Đọc hiểu":

            output_rule = CLOZE_WITH_TITLE_JSON_SCHEMA.format(
                TEXT_TYPE=text_type,
                N_Q=n_q,
                START_NUM=q_count
            )

            ai_input = (
                f"{prompt_template}\n\n"
                f"Chủ đề: {topic}\n"
                f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
                f"{READING_COMPREHENSION_EXPLANATION_TEMPLATE}\n\n"
                f"Số từ: {so_tu}\n"
                f"Độ khó: {diff}\n"
                f"Dạng thức: {text_type}\n"
                f"Số câu: {n_q}\n"
                + "\n".join(specs_list)
                + "\n\n## OUTPUT FORMAT\n"
                + output_rule
            )

            task = client.generate(prompt=ai_input)
            tasks.append(task)
            block_meta.append(("RC", topic, n_q, q_count))
            q_count += n_q

        # ===============================
        # 4️⃣ GAP FILL (Điền cụm từ/điền câu)
        # ===============================

        elif q_type == "Điền cụm từ/điền câu":

            output_rule = CLOZE_WITH_TITLE_JSON_SCHEMA.format(
                TEXT_TYPE=text_type,
                N_Q=n_q,
                START_NUM=q_count
            )

            ai_input = (
                f"{prompt_template}\n\n"
                f"Chủ đề: {topic}\n"
                f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
                f"{SILENT_PHASE_EXPLANATION_TEMPLATE}\n\n"
                f"Số từ: {so_tu}\n"
                f"Độ khó: {diff}\n"
                f"Dạng thức: {text_type}\n"
                f"Số câu: {n_q}\n"
                + "\n".join(specs_list)
                + "\n\n## OUTPUT FORMAT\n"
                + output_rule
            )

            task = client.generate(prompt=ai_input)
            tasks.append(task)
            block_meta.append(("GAP", topic, n_q, q_count))
            q_count += n_q

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for (block_type, topic, n_q, start_num), response_text in zip(block_meta, responses):
        if isinstance(response_text, Exception):
            logger.error(f"Block {block_type}/{topic} failed: {response_text}")
            response_text = ""

        parsed = _safe_parse_json(response_text)

        results.append({
            "type": block_type,
            "title": topic,
            "data": response_text,       # raw text (giữ lại để debug)
            "parsed": parsed,            # dict đã parse
            "question_count": n_q,
            "start_num": start_num,
        })

    generate_docx_from_ai_results(results, output_path)
    return results


# ============================
# DOCX GENERATION FROM RESULTS
# ============================

def generate_docx_from_ai_results(results, output_path):
    doc = Document()
    _apply_default_style(doc)

    for res in results:
        _add_instruction(doc, res)
        parsed = res.get("parsed")

        if parsed is None:
            # Fallback: dùng raw text parser cũ nếu JSON parse thất bại
            logger.warning(f"Falling back to text parser for block {res['type']}/{res['title']}")
            raw = res.get("data") or ""
            _render_fallback(doc, res["type"], raw)
        else:
            if res["type"] in ("CLOZE", "GAP", "RC"):
                _render_cloze_from_json(doc, parsed, merge_options=(res["type"] == "CLOZE"))
            elif res["type"] == "ARRANGE":
                _render_arrange_from_json(doc, parsed)

        _add_separator(doc)

    doc.save(output_path)


def export_docx_from_data(json_data, output_path):
    """
    Nhận trực tiếp JSON object (dict), lấy key 'results', render docx.
    Hỗ trợ cả format mới (có 'parsed') và format cũ (chỉ có 'data' text).
    """
    results = json_data.get("results")
    if not results:
        raise Exception("No 'results' found in JSON")

    # Nếu result chưa có 'parsed', thử parse từ 'data'
    for res in results:
        if "parsed" not in res or res["parsed"] is None:
            res["parsed"] = _safe_parse_json(res.get("data") or "")

    doc = Document()
    _apply_default_style(doc)

    for res in results:
        _add_instruction(doc, res)
        parsed = res.get("parsed")
        res_type = res.get("type")

        if parsed is None:
            raw = res.get("data") or ""
            _render_fallback(doc, res_type, raw)
        else:
            if res_type in ("CLOZE", "GAP", "RC"):
                _render_cloze_from_json(doc, parsed, merge_options=(res_type == "CLOZE"))
            elif res_type == "ARRANGE":
                _render_arrange_from_json(doc, parsed)
            else:
                logger.warning(f"Unknown type: {res_type}")

        _add_separator(doc)

    doc.save(output_path)
    return output_path


# ============================
# JSON → DOCX RENDERERS
# ============================

def _render_cloze_from_json(doc: Document, parsed: dict, merge_options: bool = False):
    """
    Render CLOZE / GAP / RC từ JSON đã parse.

    JSON structure:
    {
      "passage_title": "...",
      "passage": "...",
      "questions": [
        {
          "number": 1,
          "question_content": "...",   ← nội dung câu hỏi (có thể rỗng với CLOZE)
          "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...",
          "answer": "A",
          "explanation": "...",
          "quote": "...",
          "translation": "..."
        }, ...
      ]
    }
    """
    # ── Tiêu đề ──
    title = (parsed.get("passage_title") or "").strip()
    if title:
        p = doc.add_paragraph()
        run = p.add_run(title)
        run.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ── Passage ──
    _render_passage(doc, parsed.get("passage") or "")

    # ── Questions ──
    questions = parsed.get("questions") or []
    for q in questions:
        num              = q.get("number", "?")
        question_content = (q.get("question_content") or "").strip()
        opt_a = q.get("option_a", "")
        opt_b = q.get("option_b", "")
        opt_c = q.get("option_c", "")
        opt_d = q.get("option_d", "")

        # Header: "Question N:" + nội dung câu hỏi (nếu có) trên cùng đoạn
        p = doc.add_paragraph()
        p.add_run(f"Question {num}:").bold = True
        if question_content:
            p.add_run(f" {question_content}")

        if merge_options:
            # Ghép A B C D trên 1 dòng (dạng CLOZE)
            opts_line = f"A. {opt_a}\t\tB. {opt_b}\t\tC. {opt_c}\t\tD. {opt_d}"
            doc.add_paragraph(opts_line)
        else:
            doc.add_paragraph(f"A. {opt_a}")
            doc.add_paragraph(f"B. {opt_b}")
            doc.add_paragraph(f"C. {opt_c}")
            doc.add_paragraph(f"D. {opt_d}")

    # ── Answer Key ──
    if questions:
        p = doc.add_paragraph()
        p.add_run("ANSWER KEY").bold = True
        key_pairs = [f"{q.get('number')}-{q.get('answer','?')}" for q in questions]
        doc.add_paragraph(", ".join(key_pairs))

    # ── Explanations ──
    if questions:
        p = doc.add_paragraph()
        p.add_run("HƯỚNG DẪN GIẢI CHI TIẾT").bold = True

        for q in questions:
            num              = q.get("number", "?")
            question_content = (q.get("question_content") or "").strip()
            answer   = q.get("answer", "?")
            expl     = q.get("explanation", "")
            quote    = q.get("quote", "")
            trans    = q.get("translation", "")
            opt_a    = q.get("option_a", "")
            opt_b    = q.get("option_b", "")
            opt_c    = q.get("option_c", "")
            opt_d    = q.get("option_d", "")

            # Header câu + nội dung câu hỏi
            p = doc.add_paragraph()
            p.add_run(f"Question {num}:").bold = True
            if question_content:
                p.add_run(f" {question_content}")

            # Options dòng (dùng trong phần giải)
            doc.add_paragraph(f"A. {opt_a}\t\tB. {opt_b}\t\tC. {opt_c}\t\tD. {opt_d}")

            # Lời giải
            p = doc.add_paragraph()
            p.add_run("Lời giải").bold = True
            doc.add_paragraph(f"Chọn {answer}")

            # Giải thích
            for line in (expl or "").splitlines():
                line = line.strip()
                if line:
                    p = doc.add_paragraph()
                    add_text_with_markdown_bold(p, line)

            # Trích bài + Tạm dịch
            if quote:
                p = doc.add_paragraph()
                p.add_run("Trích bài: ").bold = True
                p.add_run(quote)
            if trans:
                p = doc.add_paragraph()
                p.add_run("Tạm dịch: ").bold = True
                p.add_run(trans)

            doc.add_paragraph("")  # khoảng trống giữa các câu


def _render_arrange_from_json(doc: Document, parsed: dict):
    """
    Render ARRANGE từ JSON đã parse.

    JSON structure:
    {
      "question_number": 1,
      "question_stem": "...",
      "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...",
      "answer": "A",
      "solution_lines": ["line1", "line2", ...],
      "translation_lines": ["trans1", "trans2", ...]
    }
    """
    num        = parsed.get("question_number", "?")
    stem       = parsed.get("question_stem", "")
    opt_a      = parsed.get("option_a", "")
    opt_b      = parsed.get("option_b", "")
    opt_c      = parsed.get("option_c", "")
    opt_d      = parsed.get("option_d", "")
    answer     = parsed.get("answer", "?")
    sol_lines  = parsed.get("solution_lines") or []
    trans_lines = parsed.get("translation_lines") or []

    # Question stem
    p = doc.add_paragraph()
    p.add_run(f"Question {num}:").bold = True
    if stem:
        doc.add_paragraph(stem)

    # Options (ghép 1 dòng như chuẩn cũ)
    opts_line = f"A. {opt_a}\t\tB. {opt_b}\t\tC. {opt_c}\t\tD. {opt_d}"
    doc.add_paragraph(opts_line)

    # Lời giải
    p = doc.add_paragraph()
    p.add_run("Lời giải").bold = True
    doc.add_paragraph(f"Chọn {answer}")

    for line in sol_lines:
        if line.strip():
            doc.add_paragraph(line.strip())

    # Tạm dịch
    if trans_lines:
        p = doc.add_paragraph()
        p.add_run("Tạm dịch:").bold = True
        for line in trans_lines:
            if line.strip():
                doc.add_paragraph(line.strip())


# ============================
# FALLBACK: TEXT PARSERS (giữ lại phòng khi JSON parse thất bại)
# ============================

def _render_fallback(doc: Document, block_type: str, raw: str):
    """Fallback về text parser cũ khi JSON parse thất bại."""
    logger.warning(f"Using text fallback renderer for type={block_type}")
    if block_type in ("CLOZE", "GAP", "RC"):
        _render_cloze_or_gap(doc, raw, merge_options=(block_type == "CLOZE"))
    elif block_type == "ARRANGE":
        _render_arrange(doc, raw)
    else:
        doc.add_paragraph(raw or "(No content)")


def _render_cloze_or_gap(doc, raw_text, merge_options=False):
    blocks = extract_cloze_sections(raw_text)
    _render_passage(doc, blocks["passage"])
    q_lines = normalize_question_lines(blocks["questions"])
    if merge_options:
        q_lines = merge_options_single_line(q_lines)
    _render_questions(doc, q_lines)
    _render_answer_key(doc, blocks["answer_key"])
    _render_explanation(doc, blocks["explanation"])


def _render_arrange(doc, raw_text):
    parts = extract_arrange_sections(raw_text)
    q_lines = normalize_question_lines(parts["question_block"])
    q_lines = merge_options_single_line(q_lines)
    _render_questions(doc, q_lines)
    doc.add_paragraph().add_run("Lời giải").bold = True
    if parts["answer_letter"]:
        doc.add_paragraph(f"Chọn {parts['answer_letter']}")
    if parts["solution_text"]:
        for ln in parts["solution_text"].splitlines():
            p = doc.add_paragraph()
            add_text_with_markdown_bold(p, ln.strip())
    if parts["translation"]:
        doc.add_paragraph().add_run("Tạm dịch:").bold = True
        for ln in parts["translation"].splitlines():
            doc.add_paragraph(ln.strip())


# ============================
# STYLE & COMMON DOCX HELPERS
# ============================

def _apply_default_style(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)


def _add_instruction(doc, res):
    instruction = doc.add_paragraph()
    if res['type'] == "CLOZE":
        text = (
            f"Read the following {res.get('title','text')} and mark the letter A, B, C or D "
            "on your answer sheet to indicate the option that best fits each of the numbered blanks."
        )
    elif res['type'] == "ARRANGE":
        text = (
            "Mark the letter A, B, C or D on your answer sheet to indicate the best arrangement "
            "of utterances or sentences to make a meaningful exchange or text."
        )
    elif res['type'] == "RC":
        text = (
            f"Read the following {res.get('title','text')} and mark the letter A, B, C or D "
            "on your answer sheet to indicate the correct answer to each question."
        )
    else:  # GAP
        text = (
            f"Read the following {res.get('title','text')} and mark the letter A, B, C or D "
            "on your answer sheet to indicate the option that best fits each blank."
        )
    run = instruction.add_run(text)
    run.italic = True


def _render_passage(doc, passage):
    bold_ul_pattern = r"\*\*(.*?)\*\*"
    underline_pattern = r"<u>(.*?)</u>"
    roman_pattern = r"\[(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\]"
    combined = f"{bold_ul_pattern}|{underline_pattern}|{roman_pattern}"

    for line in (passage or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        p = doc.add_paragraph()
        pos = 0
        for m in re.finditer(combined, line):
            if m.start() > pos:
                p.add_run(line[pos:m.start()])
            if m.group(1):
                run = p.add_run(m.group(1))
                run.bold = True
                run.underline = True
            elif m.group(2):
                run = p.add_run(m.group(2))
                run.underline = True
            else:
                run = p.add_run(m.group())
                run.bold = True
            pos = m.end()
        if pos < len(line):
            p.add_run(line[pos:])
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def _render_questions(doc, lines):
    for line in lines:
        p = doc.add_paragraph()
        if re.match(r"^Question\s+\d+[:\.]", line, re.I):
            r = p.add_run(line)
            r.bold = True
        else:
            p.add_run(line)


def _render_answer_key(doc, key_block):
    if not key_block:
        return
    doc.add_paragraph().add_run("ANSWER KEY").bold = True
    pairs = parse_answer_key_block(key_block)
    if pairs:
        ak_text = ", ".join([f"{i}-{k}" for i, k in pairs])
        doc.add_paragraph(ak_text)
    else:
        doc.add_paragraph(key_block)


def _render_explanation(doc, explanation):
    if not explanation:
        return
    doc.add_paragraph().add_run("HƯỚNG DẪN GIẢI CHI TIẾT").bold = True
    for line in explanation.split('\n'):
        text = line.strip()
        if not text:
            continue
        p = doc.add_paragraph()
        add_text_with_markdown_bold(p, text)


def _add_separator(doc):
    doc.add_paragraph("\n" + "=" * 20 + "\n")


def add_text_with_markdown_bold(paragraph, text):
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        else:
            paragraph.add_run(part)


# ============================
# LEGACY TEXT EXTRACT (FALLBACK)
# ============================

def extract_cloze_sections(raw_text):
    print(f">>>>>> debug raw_text (fallback): {raw_text[:200]}")
    s = html.unescape(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    PASS_HDR = "BÀI ĐỌC (PASSAGE)"
    KEY1 = "ANSWER KEY"
    EXPL1 = "HƯỚNG DẪN GIẢI CHI TIẾT"
    EXPL2 = "HƯỚNG DẪN GIẢI"

    pos_pass = s.find(PASS_HDR)
    if pos_pass < 0:
        return {"passage": s[:200], "questions": s[200:], "answer_key": "", "explanation": ""}

    start_pass = pos_pass + len(PASS_HDR)
    pos_first_q = s.find("Question", start_pass)
    if pos_first_q < 0:
        return {"passage": s[start_pass:].strip(), "questions": "", "answer_key": "", "explanation": ""}

    passage = s[start_pass:pos_first_q].strip()
    pos_key = s.find(KEY1, pos_first_q)
    pos_expl = -1
    for h in [EXPL1, EXPL2]:
        p = s.find(h, pos_first_q)
        if p >= 0:
            pos_expl = p
            break

    cut = min([p for p in [pos_key, pos_expl] if p >= 0], default=len(s))
    questions = s[pos_first_q:cut].strip()

    answer_key = ""
    explanation = ""
    if pos_key >= 0:
        key_end = pos_expl if pos_expl > pos_key else len(s)
        answer_key = s[pos_key + len(KEY1):key_end].strip()
    if pos_expl >= 0:
        expl_hdr = EXPL1 if s.find(EXPL1) == pos_expl else EXPL2
        explanation = s[pos_expl + len(expl_hdr):].strip()

    return {"passage": passage, "questions": questions,
            "answer_key": answer_key, "explanation": explanation}


def extract_arrange_sections(raw_text):
    s = html.unescape(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    result = {"question_block": "", "answer_letter": "", "solution_text": "", "translation": ""}
    pos_loi = re.search(r"^Lời giải", s, re.MULTILINE)
    if not pos_loi:
        result["question_block"] = s
        return result
    result["question_block"] = s[:pos_loi.start()].strip()
    after = s[pos_loi.end():]
    m_chon = re.search(r"Chọn\s+([ABCD])", after)
    if m_chon:
        result["answer_letter"] = m_chon.group(1)
        after2 = after[m_chon.end():]
    else:
        after2 = after
    pos_tam = after2.find("Tạm dịch:")
    if pos_tam >= 0:
        result["solution_text"] = after2[:pos_tam].strip()
        result["translation"] = after2[pos_tam + len("Tạm dịch:"):].strip()
    else:
        result["solution_text"] = after2.strip()
    return result


def normalize_question_lines(qtext):
    lines = []
    for raw in (qtext or "").splitlines():
        line = html.unescape(raw).strip()
        if not line:
            continue
        line = re.sub(r"\sA\.\s", "\tA. ", line)
        line = re.sub(r"\sB\.\s", "\tB. ", line)
        line = re.sub(r"\sC\.\s", "\tC. ", line)
        line = re.sub(r"\sD\.\s", "\tD. ", line)
        lines.append(line)
    return lines


def parse_answer_key_block(key_block):
    s = (key_block or "").replace("\r\n", "\n")
    pairs = []
    for m in re.finditer(r"(\d+)\s*[-=:]\s*([ABCD])", s, re.I):
        pairs.append((int(m.group(1)), m.group(2).upper()))
    if pairs:
        return sorted(pairs, key=lambda x: x[0])
    for m in re.finditer(r"(\d+)\s+([ABCD])\b", s, re.I):
        pairs.append((int(m.group(1)), m.group(2).upper()))
    return sorted(pairs, key=lambda x: x[0])


def merge_options_single_line(lines):
    merged = []
    buffer = []
    current_question = None

    for line in lines:
        if re.match(r"^Question\s+\d+[:\.]", line, re.I):
            if current_question:
                if buffer:
                    merged.append("\t".join(buffer))
                    buffer = []
            merged.append(line)
            current_question = line
        elif re.match(r"^[ABCD]\.\s", line):
            buffer.append(line.strip())
        else:
            if buffer:
                merged.append("\t".join(buffer))
                buffer = []
            merged.append(line)

    if buffer:
        merged.append("\t".join(buffer))

    return merged


# ============================
# MAIN FLOW
# ============================

async def generate_english_flow(file):
    session_id = str(uuid.uuid4())
    excel_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
    output_path = OUTPUT_DIR / f"ENGLISH_EXAM_{session_id}.docx"

    try:
        with open(excel_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        blocks = extract_blocks_from_excel(str(excel_path))
        results = await generate_exam_docx(blocks, str(output_path))

        FileResponse(
            path=str(output_path),
            filename=f"ENGLISH_EXAM_{session_id}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        return {
            "session_id": session_id,
            "status": "success",
            "message": "Generate English exam successfully",
            "results": results
        }

    except Exception as e:
        logger.exception("Error while generating English exam")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate English exam: {str(e)}"
        )