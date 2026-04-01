import json
import random
import re
import requests
import asyncio
import logging
from typing import Any, List

from api.callApi import get_credentials
from services.english_generator_service.vertex_async_client import AsyncVertexClient
from services.english_generator_service.vertex_async_3_1_model import AsyncVertexGemini31

logger = logging.getLogger(__name__)


# ============================
# PROMPT LOADER
# ============================

def get_drive_file_content():
    """
    Lấy nội dung file TA_Huong_dan_giai.md từ Google Drive public folder
    Không cần auth
    """
    FILE_ID = "19WaudkbI20vukSvswqrHGvv407E6PiLZ"
    url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

    response = requests.get(url)

    print(f">>>>> debug response drive {response}")

    if response.status_code != 200:
        raise Exception("Không lấy được prompt từ Google Drive")

    return response.text


DRIVE_PROMPT_ENGLISH_SOLUTION = "https://drive.google.com/drive/folders/19WaudkbI20vukSvswqrHGvv407E6PiLZ"

ENGLISH_SCHEMA_SOLUTE = r"""
[
  {
    "type": "CLOZE",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
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
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "passage_title": "string",
      "passage": "string",
      "questions": [
        {
          "number": "number",
          "question_content": "string | null", 
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
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "passage_title": "string | null",
      "passage": "string",
      "questions": [
        {
          "number": "number",
          "question_content": "string | null",
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
    "titleQuestion": "string",
    "question_count": "number,
    "start_num": "number",
    "parsed": {
      "question_number": "number",
      "question_content": ["string"],
      "option_a": "string",
      "option_b": "string",
      "option_c": "string",
      "option_d": "string",
      "answer": "A | B | C | D",
      "solution_lines": ["string"],
      "translation_lines": ["string"]
    }
  },
  {
    "type": "SENTENCE_COMPLETION",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "question": "string",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "SYNONYM_ANTONYM",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "question": "string",
          "type": "synonym | antonym",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "ERROR_IDENTIFICATION",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "question": "string",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "correction": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "SENTENCE_TRANSFORMATION",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "type": "rewriting | combination",
          "question": "string",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "translation": "string",
          "correct_translation": "string"
        }
      ]
    }
  },
  {
    "type": "WORD_REORDERING",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "word_list": "string",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "PRONUNCIATION_STRESS",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "type": "pronunciation | stress",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "details": [
            {
              "word": "string",
              "ipa": "string",
              "pos": "string",
              "meaning": "string"
            }
          ]
        }
      ]
    }
  },
  {
    "type": "DIALOGUE_COMPLETION",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "instruction": "string",
      "questions": [
        {
          "number": "number",
          "speaker_a": "string",
          "speaker_b": "______",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "translation": {
            "speaker_a": "string",
            "speaker_b": "string"
          }
        }
      ]
    }
  },
  {
    "type": "LOGICAL_THINKING",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "type": "social_interaction | dialogue_response | cause_inference | result_prediction | fact_verification | definition_example",
          "scenario": "string",
          "speaker_a": "string | null",
          "speaker_b": "______ | null",
          "question": "string | null",
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "translation": {
            "scenario": "string",
            "question": "string | null",
            "speaker_a": "string | null",
            "speaker_b": "string | null"
          }
        }
      ]
    }
  }
]
"""


API_KEY = "AIzaSyAUZx6cZjFMEGZjDV9Hv7489s-seEcqMxI"
DRIVE_FOLDER = "https://drive.google.com/drive/folders/19WaudkbI20vukSvswqrHGvv407E6PiLZ"


def extract_folder_id(url):
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise Exception("Không tìm thấy folder ID")
    return match.group(1)


def get_md_file_from_drive():
    try:
        folder_id = extract_folder_id(DRIVE_FOLDER)

        # 1. List files trong folder
        list_url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name = 'TA_Huong_dan_giai.md'",
            "fields": "files(id, name, mimeType)"
        }

        res = requests.get(list_url, params=params)
        res.raise_for_status()

        files = res.json().get("files", [])

        if not files:
            raise Exception("❌ Không tìm thấy file TA_Huong_dan_giai.md")

        file_id = files[0]["id"]

        # 2. Download file content
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"

        params = {
            "mimeType": "text/plain",
            "key": API_KEY
        }

        file_res = requests.get(download_url, params=params)
        file_res.raise_for_status()

        content = file_res.content.decode("utf-8")

        print(f">>>>> debug content {content}")
        return content

    except requests.exceptions.RequestException as e:
        # lỗi HTTP / network
        raise Exception(
            f"🌐 Request error\n"
            f"Error: {str(e)}\n"
            f"Response: {getattr(e.response, 'text', 'No response')}"
        )

    except Exception as e:
        # lỗi logic
        raise Exception(f"❌ Internal error: {str(e)}")

# ============================
# FALLBACK LOGIC
# ============================

async def solute_with_fallback(
    client_31: AsyncVertexGemini31,
    client_25: AsyncVertexClient,
    prompt: str,
    pdf_path: str,
    max_retries: int = 3
):
    """
    Ưu tiên dùng Gemini 3.1. Nếu gặp lỗi 429 (Resource Exhausted),
    chuyển sang Gemini 2.5 Pro với cơ chế exponential backoff retry.
    """
    # 1. Thử Gemini 3.1 trước
    try:
        logger.info(f"--- [Solute] Attempting with Gemini 3.1: {pdf_path} ---")
        return await client_31.solute(
            prompt=prompt,
            pdf_path=pdf_path,
            temperature=1.0
        )
    except Exception as e:
        error_msg = str(e).upper()
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            logger.warning(
                f"⚠️ Gemini 3.1 hit quota limit (429) for {pdf_path}. "
                f"Falling back to Gemini 2.5 Pro..."
            )

            # 2. Fallback sang Gemini 2.5 Pro với retry + backoff
            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"--- [Solute] Gemini 2.5 attempt {attempt + 1}/{max_retries}: {pdf_path} ---"
                    )
                    return await client_25.solute(
                        prompt=prompt,
                        pdf_path=pdf_path,
                        temperature=1.0
                    )
                except Exception as e2:
                    if "429" in str(e2).upper() or "RESOURCE_EXHAUSTED" in str(e2).upper():
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"⚠️ Gemini 2.5 also hit 429 (attempt {attempt + 1}). "
                            f"Retry after {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ Gemini 2.5 failed with non-429 error: {e2}")
                        raise e2

            raise Exception(
                f"❌ Cả Gemini 3.1 và 2.5 đều vượt ngưỡng giới hạn yêu cầu (429) "
                f"cho file: {pdf_path}"
            )
        else:
            # Lỗi khác (không phải 429) → raise ngay để debug
            logger.error(f"❌ Gemini 3.1 failed with non-429 error for {pdf_path}: {e}")
            raise e


# ============================
# PER-FILE PROCESSOR
# ============================

async def process_single_pdf(
    pdf_path: str,
    prompt: str,
    client_31: AsyncVertexGemini31,
    client_25: AsyncVertexClient
):
    """
    Xử lý 1 file PDF với cơ chế fallback Gemini 3.1 → 2.5.
    """
    result = await solute_with_fallback(
        client_31=client_31,
        client_25=client_25,
        prompt=prompt,
        pdf_path=pdf_path
    )
    return result


# ============================
# MAIN SERVICE
# ============================

def clean_json(results: list[Any]) -> list[dict]:
    """
    Clean và parse JSON từ kết quả trả về của solve_english_exam.
    Xử lý các trường hợp: raw string, list có wrapper ```json```, hoặc dict thuần.
    """
    cleaned = []

    for result in results:
        parsed = _parse_single_result(result)
        if parsed is not None:
            cleaned.append(parsed)

    return cleaned


def _parse_single_result(result: Any) -> Any:
    # Trường hợp đã là dict/list rồi → trả thẳng
    if isinstance(result, (dict, list)):
        return result

    if not isinstance(result, str):
        return None

    # Bóc markdown fence ```json ... ``` hoặc ``` ... ```
    text = result.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Thử fix escaped newline/tab thừa rồi parse lại
        text = text.encode("utf-8").decode("unicode_escape", errors="ignore")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

async def solve_english_exam(file_paths: List[str]):
    print(f">>>>> debug file_paths {file_paths}")

    try:
        base_prompt = get_md_file_from_drive()

        full_prompt = f"""
{base_prompt}

========================
OUTPUT FORMAT (STRICT JSON):


{ENGLISH_SCHEMA_SOLUTE}

### QUY TẮC NGHIÊM NGẶT PHẢI TUÂN THỦ:

#### 1.Trong các trường passage hoặc tất cả các key và value theo schema có những phần tử hoặc các từ được in nghiêng và in đậm trong đoạn văn hãy viết format dạng <strong><u>abc</u></strong>, ví dụ <strong><u>contribute positively</u></strong> không được bỏ sót

### 2. KHÔNG ĐƯỢC BỎ SÓT FORMATTING 
 - Phải quét tất cả các kí tự được in đậm in nghiêng gạch chân và trả về dạng <strong><u><i>abc</i></u></strong> không được thiếu bất kì 1 kí tự nào.
"""

        credentials, project_id = get_credentials()

        client_31 = AsyncVertexGemini31(
            project_id="onluyen-media",
            model="gemini-3.1-pro-preview",
            thinking_level="HIGH"
        )

        client_25 = AsyncVertexClient(
            project_id=project_id,
            creds=credentials,
            model="gemini-2.5-pro"
        )

        async def run_all():
            tasks = [
                process_single_pdf(pdf_path, full_prompt, client_31, client_25)
                for pdf_path in file_paths
            ]
            return await asyncio.gather(*tasks)

        # ✅ FIX HERE
        results = await run_all()
        cleaned_results = clean_json(results)
        print(f">>>>> debug cleaned_results {cleaned_results}")
        return cleaned_results


    except Exception as e:
        logger.error(f"Error in solve_english_exam: {e}")
        return []


