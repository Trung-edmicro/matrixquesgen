import requests
import asyncio
from typing import List

from services.english_generator_service.vertex_async_3_1_model import AsyncVertexGemini31 


def get_drive_file_content():
    """
    Lấy nội dung file TA_Huong_dan_giai.md từ Google Drive public folder
    Không cần auth
    """

    # ⚠️ Cách đơn giản: dùng link export raw nếu biết file_id
    # Bạn cần lấy file_id của file TA_Huong_dan_giai.md
    FILE_ID = "19WaudkbI20vukSvswqrHGvv407E6PiLZ"

    url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception("Không lấy được prompt từ Google Drive")

    return response.text

DRIVE_PROMPT_ENGLISH_SOLUTION  = "https://drive.google.com/drive/folders/19WaudkbI20vukSvswqrHGvv407E6PiLZ"

ENGLISH_SCHEMA_SOLUTE = r"""
[
  {
    "type": "CLOZE",
    "title": "string",
    "question_count": "number",
    "start_num": "number",
    "text_type_en": "string",
    "parsed": {
      "passage_title": "string",
      "passage": "string",
      "questions": [
        {
          "number": "number",
          "question_content": "string",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "quote": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "RC",
    "title": "string",
    "question_count": "number",
    "start_num": "number",
    "text_type_en": "string",
    "parsed": {
      "passage_title": "string",
      "passage": "string",
      "questions": [
        {
          "number": "number",
          "question_content": "string",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "quote": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "GAP",
    "title": "string",
    "question_count": "number",
    "start_num": "number",
    "text_type_en": "string",
    "parsed": {
      "passage_title": "string",
      "passage": "string",
      "questions": [
        {
          "number": "number",
          "question_content": "string",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "quote": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "ARRANGE",
    "title": "string",
    "question_count": 1,
    "start_num": "number",
    "text_type_en": "string",
    "parsed": {
      "question_number": "number",
      "question_stem": "string",
      "option_a": "string",
      "option_b": "string",
      "option_c": "string",
      "option_d": "string",
      "answer": "A | B | C | D",
      "solution_lines": ["string"],
      "translation_lines": ["string"]
    }
  }
]
"""

async def process_single_pdf(pdf_path: str, prompt: str, client: AsyncVertexGemini31):
    """
    Xử lý 1 file PDF
    """
    result = await client.solute(
        prompt=prompt,
        pdf_path=pdf_path,
        temperature=1.0
    )
    return result


def solve_english_exam(file_paths: List[str]):
    """
    Main service xử lý nhiều file PDF
    """

    try:
        # 1. Lấy prompt từ Drive
        base_prompt = get_drive_file_content()

        # 2. Append schema
        full_prompt = f"""
{base_prompt}

========================
OUTPUT FORMAT (STRICT JSON):
{ENGLISH_SCHEMA_SOLUTE}
"""

        # 3. Khởi tạo Gemini client
        client = AsyncVertexGemini31(
            project_id="onluyen-media",
            thinking_level="HIGH"
        )

        # 4. Run async cho nhiều file
        async def run_all():
            tasks = [
                process_single_pdf(pdf_path, full_prompt, client)
                for pdf_path in file_paths
            ]
            return await asyncio.gather(*tasks)

        results = asyncio.run(run_all())

        return results

    except Exception as e:
        print(f"Error in solve_english_exam: {e}")
        return []









