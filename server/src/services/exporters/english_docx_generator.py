# english_docx_generator.py

import os
import json
from datetime import datetime
from pathlib import Path

from docx import Document

# import các hàm bạn đã viết
from services.english_generator_service.english_generator_service import generate_docx_from_ai_results, export_docx_from_data

# ============================================
# LOAD SESSION DATA
# ============================================

def load_session_data(session_id: str):
    """
    Load dữ liệu AI đã generate theo session.
    Tuỳ bạn đang lưu DB hay file JSON.
    Ở đây ví dụ load từ file.
    """

    session_file = f"sessions/{session_id}.json"

    if not os.path.exists(session_file):
        raise Exception("Session not found")

    with open(session_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================
# CONVERT RESPONSE TO RESULTS FORMAT
# ============================================

# def build_results_from_response(response_json):
#     """
#     Convert dữ liệu response thành format
#     mà generate_docx_from_ai_results cần
#     """

#     results = []

#     blocks = response_json.get("blocks", [])

#     for block in blocks:

#         block_type = block.get("type")
#         topic = block.get("topic", "")
#         raw_text = block.get("ai_response", "")

#         # Mapping type
#         if block_type == "Điền từ":
#             mapped = "CLOZE"

#         elif block_type == "Sắp xếp":
#             mapped = "ARRANGE"

#         elif block_type == "Đọc hiểu":
#             mapped = "RC"

#         elif block_type == "Điền cụm từ/điền câu":
#             mapped = "GAP"

#         else:
#             continue

#         results.append({
#             "type": mapped,
#             "data": raw_text,
#             "title": topic
#         })

#     return results


def build_results_from_response(response_json):

    TYPE_MAPPING = {
        "Điền từ": "CLOZE",
        "Sắp xếp": "ARRANGE",
        "Đọc hiểu": "RC",
        "Điền cụm từ/điền câu": "GAP"
    }

    results = []
    blocks = response_json.get("blocks", [])

    for block in blocks:

        block_type = block.get("type")
        topic = block.get("topic", "")
        raw_text = block.get("ai_response", "")

        mapped = TYPE_MAPPING.get(block_type)

        if not mapped:
            print("⚠ Unknown type:", block_type)
            continue

        if not raw_text:
            print("⚠ Empty ai_response")
            continue

        results.append({
            "type": mapped,
            "data": raw_text,
            "title": topic
        })

    return results


# ============================================
# MAIN EXPORT FUNCTION
# ============================================

async def export_english_docx(session_id: str):

    print(f">>>>> debug session_id {session_id}")

    # 1️⃣ Load session data
    response_json = load_session_data(session_id)

    # 2️⃣ Convert sang results format
    results = build_results_from_response(response_json)

    if not results:
        raise Exception("No valid blocks found")

    # 3️⃣ Generate output path
    output_dir = Path("exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"English_Exam_{session_id}.docx"
    output_path = output_dir / file_name

    # 4️⃣ Generate DOCX
    generate_docx_from_ai_results(results, str(output_path))

    return {
        "file_name": file_name,
        "file_path": str(output_path)
    }