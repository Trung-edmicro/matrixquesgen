import shutil
import uuid
from fastapi import HTTPException
import pandas as pd
from collections import defaultdict
from pathlib import Path
import os
import json
from api.callApi import get_credentials
# from services.english_generator_service.vertex_async_client import AsyncVertexClient
from .english_excel_helper import extract_blocks_from_excel
from .docx_helper_english import add_formatted_paragraph, render_formatted_paragraph
from services.english_generator_service.vertex_async_3_1_model import AsyncVertexGemini31
import asyncio
import re
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import logging
from .constants import (CLOZE_EXPLANATION_TEMPLATE, 
                        ARRANGE_JSON_SCHEMA,
     CLOZE_WITH_TITLE_JSON_SCHEMA, CLOZE_JSON_SCHEMA,
       READING_COMPREHENSION_EXPLANATION_TEMPLATE, SILENT_PHASE_EXPLANATION_TEMPLATE, PROMPTS)
logger = logging.getLogger(__name__)
from .drive_helper_services import fetch_drive_md_files, load_vocabulary_from_drive
from bs4 import BeautifulSoup

# ============================
# CONFIG
# ============================

LEVELS = ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"]

APP_DIR = Path(os.environ['APP_DIR']) if os.environ.get('APP_DIR') else Path(__file__).parent.parent.parent.parent.parent
PROMPT_DIR = APP_DIR / "data" / "prompts" / "TIENGANH"
UPLOAD_DIR = APP_DIR / "data" / "uploads"
OUTPUT_DIR = APP_DIR / "data" / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_prompt(filename: str) -> str:
    global _drive_prompts_cache

    # Load drive 1 lần
    if _drive_prompts_cache is None:
        print("🔎 Fetching prompts from Drive...")
        _drive_prompts_cache = fetch_drive_md_files()

    # Nếu có trên drive
    if filename in _drive_prompts_cache:
        print(f"✅ Load từ Drive: {filename}")
        return _drive_prompts_cache[filename]

    # fallback local
    path = PROMPT_DIR / filename

    if not path.exists():
        raise Exception(f"Không tìm thấy prompt: {filename}")

    print(f"📂 Load từ LOCAL: {filename}")
    return path.read_text(encoding="utf-8")


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


def safe_str(val):
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s

async def generate_exam_docx(blocks, output_path):

    project_id = get_credentials()

    # client = AsyncVertexClient(
    #     project_id=project_id,
    #     creds=credentials,
    #     model="gemini-2.5-pro"
    # )

    client = AsyncVertexGemini31(
    project_id="onluyen-media",
    model="gemini-3.1-pro-preview",
    thinking_level="HIGH"
)

    doc = Document()
    doc.add_heading("ĐỀ THI TIẾNG ANH", level=1)

    q_count = 1
    tasks = []
    block_meta = []

    for block in blocks:

        topic     = block["topic"]
        vocabulary = block["vocabulary"]
        vocabulary_example = block["vocabulary_example"]
        if pd.isna(vocabulary) or str(vocabulary).strip() == "":
            # vocabulary = load_vocabulary_from_drive(topic) or ""
            vocabulary = load_vocabulary_from_drive(vocabulary_example) or ""

        vocabulary = str(vocabulary)
        q_type    = block["type"]
        text_type = block["text_type"]
        text_type_en = block["text_type_en"]
        diff      = block["difficulty"]
        so_tu     = block.get("word_count", "")
        questions = block["questions"]
        document_sample = block["document_sample"]
       
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

            formatted_cloze_prompt = (
                prompt_template
                    .replace("{TOPIC_NAME}", safe_str(topic))
                    .replace("{TEXT_TYPE}", safe_str(text_type))
                    .replace("{CEFR_LEVEL}", safe_str(diff))
                    .replace("{VOCABULARY_LIST}", safe_str(vocabulary))
                    .replace("{TARGET_WORD_COUNT}", safe_str(so_tu))
                    .replace("{SOURCE_TEXT}", safe_str(document_sample))
            )

            print(f">>>>>>> debug formatted cloze prompt {formatted_cloze_prompt}")

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
                f"{formatted_cloze_prompt}\n\n"
                f"Chủ đề: {topic}\n"
                f"Từ vựng tham khảo: {vocabulary}\n"
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
            block_meta.append(("CLOZE", topic, n_q, q_count,text_type_en))
            q_count += n_q

        # ===============================
        # 2️⃣ ARRANGE (Sắp xếp)
        # ===============================

        elif q_type == "Sắp xếp":

            spec_item = questions[0]
            output_rule = ARRANGE_JSON_SCHEMA.format(START_NUM=q_count)
            formatted_arrange_prompt = (
                            prompt_template
                                .replace("{TOPIC_NAME}", safe_str(topic))
                                .replace("{TEXT_TYPE}", safe_str(text_type))
                                .replace("{CEFR_LEVEL}", safe_str(diff))
                                .replace("{VOCABULARY_LIST}", safe_str(vocabulary))
                                .replace("{TARGET_WORD_COUNT}", safe_str(so_tu))
                        )
            print(f">>>>>> debug formatted_arrage_prompt {formatted_arrange_prompt}")

            ai_input = (
                f"{formatted_arrange_prompt}\n\n"
                f"Chủ đề: {topic}\n"
                f"Từ vựng tham khảo:{vocabulary}\n"
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
            block_meta.append(("ARRANGE", topic, 1, q_count, text_type_en))
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

            formatted_reading_prompt = (
                prompt_template
                    .replace("{TOPIC_NAME}", safe_str(topic))
                    .replace("{TEXT_TYPE}", safe_str(text_type))
                    .replace("{CEFR_LEVEL}", safe_str(diff))
                    .replace("{VOCABULARY_LIST}", safe_str(vocabulary))
                    .replace("{TARGET_WORD_COUNT}", safe_str(so_tu))
                    .replace("{SOURCE_TEXT}", safe_str(document_sample))
            )

            print(f">>>>>>> debug formated prompt {formatted_reading_prompt}")


            ai_input = (
                f"{formatted_reading_prompt}\n\n"
                f"Chủ đề: {topic}\n"
                f"Từ vựng tham khảo: {vocabulary}"
                f"Tài liệu tham khảo: {document_sample}"
                f"Số từ: {so_tu}\n"
                f"Độ khó: {diff}\n"
                f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
                f"{READING_COMPREHENSION_EXPLANATION_TEMPLATE}"
                f"Dạng thức: {text_type}\n"
                f"Số câu: {n_q}\n"
                + "\n".join(specs_list)
                + "\n\n## OUTPUT FORMAT\n"
                + output_rule
            )

            task = client.generate(prompt=ai_input)
            tasks.append(task)
            block_meta.append(("RC", topic, n_q, q_count,text_type_en))
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

            formatted_silent_prompt = (
                        prompt_template
                    .replace("{TOPIC_NAME}", safe_str(topic))
                    .replace("{TEXT_TYPE}", safe_str(text_type))
                    .replace("{CEFR_LEVEL}", safe_str(diff))
                    .replace("{VOCABULARY_LIST}", safe_str(vocabulary))
                    .replace("{TARGET_WORD_COUNT}", safe_str(so_tu))
                    .replace("{SOURCE_TEXT}", safe_str(document_sample))
            )


            ai_input = (
                f"{formatted_silent_prompt}\n\n"
                f"Chủ đề: {topic}\n"
                f"Từ vựng tham khảo: {vocabulary}"
                f"Tài liệu tham khảo: {document_sample}"
                f"## EXPLANATION MICRO-FORMAT (STRICT)\n"
                f"Cấm tuyệt đối không viết lại câu hỏi trong phần giải thích"
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
            block_meta.append(("GAP", topic, n_q, q_count,text_type_en))
            q_count += n_q

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for (block_type, topic, n_q, start_num, text_type_en), response_text in zip(block_meta, responses):
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
            "text_type_en": text_type_en.lower()
        })
        # print(f">>>>>> debug results {results}")

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


        if res["type"] in ("CLOZE", "GAP", "RC"):
                _render_cloze_from_json(doc, parsed, merge_options=(res["type"] == "CLOZE"),qtype=res["type"])
        elif res["type"] == "ARRANGE":
                _render_arrange_from_json(doc, parsed)

        _add_separator(doc)

    doc.save(output_path)


def export_standard_docx_from_data(json_data, output_path):
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

        if res_type in ("CLOZE", "GAP", "RC"):
                _render_standard_cloze_from_json(doc, parsed, merge_options=(res_type == "CLOZE"))
        elif res_type == "ARRANGE":
                _render_standard_arrange_from_json(doc, parsed)
        else:
                logger.warning(f"Unknown type: {res_type}")

        _add_separator(doc)

    doc.save(output_path)
    return output_path



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


def _render_standard_cloze_from_json(doc: Document, parsed: dict, merge_options: bool = False):
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
        question_content = question_content.replace("'", '"')
        opt_a = q.get("option_a", "")
        opt_b = q.get("option_b", "")
        opt_c = q.get("option_c", "")
        opt_d = q.get("option_d", "")

        # Header: "Question N:" + nội dung câu hỏi (nếu có) trên cùng đoạn
        p = doc.add_paragraph()
        p.add_run(f"Question {num}:").bold = True
        if question_content:
            question_content = question_content.replace("“", '"').replace("”", '"')
            parts = re.split(r'(".*?")', question_content)

            for part in parts:
                if part.startswith('"') and part.endswith('"'):
                    word = part[1:-1]
                    p.add_run('"')
                    run = p.add_run(word)
                    run.bold = True
                    run.underline = True
                    p.add_run('"')
                else:
                    words = re.split(r'(OPPOSITE)', part)
                    for w in words:
                        run = p.add_run(w)
                        if w == "OPPOSITE":
                            run.bold = True

        if merge_options:
            # Ghép A B C D trên 1 dòng (dạng CLOZE)
            opts_line = f"A. {opt_a}\t\tB. {opt_b}\t\tC. {opt_c}\t\tD. {opt_d}"
            doc.add_paragraph(opts_line)
        else:
            doc.add_paragraph(f"A. {opt_a}")
            doc.add_paragraph(f"B. {opt_b}")
            doc.add_paragraph(f"C. {opt_c}")
            doc.add_paragraph(f"D. {opt_d}")





def _render_cloze_from_json(doc: Document, parsed: dict, merge_options: bool = False, qtype: str = ""):
    """
    Render CLOZE / GAP / RC từ JSON đã parse.
    Question -> Options -> Lời giải -> Explanation -> Quote -> Translation
    """

    # ── Title ─────────────────────────────
    title = (parsed.get("passage_title") or "").strip()
    if title:
        p = doc.add_paragraph()
        run = p.add_run(title)
        run.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER


    # ── Passage ───────────────────────────
    _render_passage(doc, parsed.get("passage") or "")

    questions = parsed.get("questions") or []

    # ── Questions + Explanations ──────────
    for q in questions:

        num = q.get("number", "?")
        question_content = (q.get("question_content") or "").strip()
        question_content = question_content.replace("'", '"')
        opt_a = q.get("option_a", "")
        opt_b = q.get("option_b", "")
        opt_c = q.get("option_c", "")
        opt_d = q.get("option_d", "")

        answer = q.get("answer", "?")
        explanation = q.get("explanation", "")
        quote = q.get("quote", "")
        translation = q.get("translation", "")

        # Question header
        p = doc.add_paragraph()
        p.add_run(f"Question {num}: ").bold = True
        if question_content:
            question_content = question_content.replace("“", '"').replace("”", '"').replace("**", '"')
            parts = re.split(r'(".*?")', question_content)

            for part in parts:
                if part.startswith('"') and part.endswith('"'):
                    word = part[1:-1]
                    p.add_run('"')
                    run = p.add_run(word)
                    run.bold = True
                    run.underline = True
                    p.add_run('"')
                else:
                    words = re.split(r'(OPPOSITE)', part)
                    for w in words:
                        run = p.add_run(w)
                        if w == "OPPOSITE":
                            run.bold = True


        # Options
        if merge_options:
            doc.add_paragraph(
                f"A. {opt_a}\t\tB. {opt_b}\t\tC. {opt_c}\t\tD. {opt_d}"
            )
        else:
            doc.add_paragraph(f"A. {opt_a}")
            doc.add_paragraph(f"B. {opt_b}")
            doc.add_paragraph(f"C. {opt_c}")
            doc.add_paragraph(f"D. {opt_d}")


        # ── Lời giải ──
        p = doc.add_paragraph()
        p.add_run("Lời giải").bold = True

        p = doc.add_paragraph()
        p.add_run(f"Chọn {answer}").bold = True

        # Explanation
        if explanation:
            for line in explanation.splitlines():
                line = line.strip()
                if line:
                    # p = doc.add_paragraph()
                    # add_text_with_markdown_bold(p, line)
                    render_formatted_paragraph(doc, line)

        # Quote
        # if quote:
        #     p = doc.add_paragraph()
        #     p.add_run("Trích bài: ").bold = True
        #     p.add_run(quote)

        # # Translation
        # if translation:
        #     p = doc.add_paragraph()
        #     p.add_run("Tạm dịch: ").bold = True
        #     p.add_run(translation)

        
        if qtype not in ["RC", "GAP"]:

            if quote:
                # p = doc.add_paragraph()
                # p.add_run("Trích bài: ").bold = True
                # p.add_run(quote)
                add_formatted_paragraph(doc, "Trích bài: ", quote)

            if translation:
                # p = doc.add_paragraph()
                # p.add_run("Tạm dịch: ").bold = True
                # p.add_run(translation)
                add_formatted_paragraph(doc, "Tạm dịch: ", translation)
        # khoảng cách giữa các câu
        doc.add_paragraph("")


def _render_standard_arrange_from_json(doc: Document, parsed: dict):
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
    # p = doc.add_paragraph()
    # p.add_run("Lời giải").bold = True
    # doc.add_paragraph(f"Chọn {answer}")

    # for line in sol_lines:
    #     if line.strip():
    #         doc.add_paragraph(line.strip())

    # # Tạm dịch
    # if trans_lines:
    #     p = doc.add_paragraph()
    #     p.add_run("Tạm dịch:").bold = True
    #     for line in trans_lines:
    #         if line.strip():
    #             doc.add_paragraph(line.strip())


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
    stem       = parsed.get("question_stem", "title")
    opt_a      = parsed.get("option_a", "")
    opt_b      = parsed.get("option_b", "")
    opt_c      = parsed.get("option_c", "")
    opt_d      = parsed.get("option_d", "")
    answer     = parsed.get("answer", "?")
    sol_lines  = parsed.get("solution_lines") or []
    trans_lines = parsed.get("translation_lines") or []

    # Question stem
    p = doc.add_paragraph()
    p.add_run(f"Question {num}: ").bold = True
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
            # doc.add_paragraph(line.strip())
            add_html_paragraph(doc, line.strip())

    # Tạm dịch
    if trans_lines:
        p = doc.add_paragraph()
        p.add_run("Tạm dịch:").bold = True
        for line in trans_lines:
            if line.strip():
                # doc.add_paragraph(line.strip())
                 add_html_paragraph(doc, line.strip())


def add_html_paragraph(doc, text, prefix=None):
    p = doc.add_paragraph()

    # prefix (in đậm)
    if prefix:
        run = p.add_run(prefix)
        run.bold = True

    soup = BeautifulSoup(text, "html.parser")

    for element in soup.descendants:
        if element.name is None and element.string:
            parent = element.parent

            run = p.add_run(element.string)

            run.bold = any(tag.name in ["strong", "b"] for tag in parent.parents) or parent.name in ["strong", "b"]
            run.underline = parent.find_parent("u") is not None or parent.name == "u"
            run.italic = parent.find_parent("i") is not None or parent.name == "i"





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
            f"Read the following {res.get('text_type_en').lower()} and mark the letter A, B, C or D "
            "on your answer sheet to indicate the option that best fits each of the numbered blanks."
        )
    elif res['type'] == "ARRANGE":
        text = (
            "Mark the letter A, B, C or D on your answer sheet to indicate the best arrangement "
            "of utterances or sentences to make a meaningful exchange or text."
        )
    elif res['type'] == "RC":
        text = (
            f"Read the following passage and mark the letter A, B, C or D "
            "on your answer sheet to indicate the correct answer to each of the following questions."
        )
    else:  # GAP
        text = (
            f"Read the following passage and mark the letter A, B, C or D "
            "on your answer sheet to indicate the option that best fits each of the numbered blank."
        )
    run = instruction.add_run(text)
    run.italic = True


def _render_passage(doc, passage):
    bold_ul_pattern = r"\*\*(.*?)\*\*"
    underline_pattern = r"<u>(.*?)</u>"
    roman_pattern = r"\[(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\]"
    # FIX: thêm \s* để cho phép khoảng trắng giữa (1) và ______
    question_blank_pattern = r"\(\d+\)\s*_{2,}"

    combined = f"{bold_ul_pattern}|{underline_pattern}|{roman_pattern}|{question_blank_pattern}"

    for line in (passage or "").split("\n"):
        line = line.strip()
        if not line:
            continue

        p = doc.add_paragraph()
        pos = 0

        for m in re.finditer(combined, line):
            if m.start() > pos:
                p.add_run(line[pos:m.start()])

            if m.group(1):  # **text**
                run = p.add_run(m.group(1))
                run.bold = True
                run.underline = True

            elif m.group(2):  # <u>text</u>
                run = p.add_run(m.group(2))
                run.bold = True
                run.underline = True

            # FIX: dùng re.search thay vì re.match
            elif re.search(question_blank_pattern, m.group()):
                run = p.add_run(m.group())
                run.bold = True

            else:  # roman [I] [II]
                run = p.add_run(m.group())
                run.bold = True

            pos = m.end()

        if pos < len(line):
            p.add_run(line[pos:])

        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY




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





# # ============================
# # MAIN FLOW
# # ============================

async def generate_english_flow(file):
    session_id = str(uuid.uuid4())
    excel_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
    output_path = OUTPUT_DIR / f"ENGLISH_EXAM_{session_id}.docx"

    try:
        with open(excel_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        blocks = extract_blocks_from_excel(str(excel_path))
        results = await generate_exam_docx(blocks, str(output_path))

        # FileResponse(
        #     path=str(output_path),
        #     filename=f"ENGLISH_EXAM_{session_id}.docx",
        #     media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        # )

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