import json
import os
from pathlib import Path
import random
import re
import requests
import asyncio
import logging
from typing import Any, List
from api.callApi import get_credentials
from services.english_generator_service.json_utils import _safe_parse_json
from services.english_generator_service.llm_factory import build_llm_provider
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

ENGLISH_SCHEMA_SOLUTE = """
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
    "question_count": "number",
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
          "option_a": "<u>string</u>",
          "option_b": "<u>string</u>",
          "option_c": "<u>string</u>",
          "option_d": "<u>string</u>",
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
           "speaker_a": {
            "name": "string",
            "text": "string"
          },
          "speaker_b": {
            "name": "string",
            "text": "string"
          },
          "option_a": "string",
          "option_b": "string",
          "option_c": "string",
          "option_d": "string",
          "answer": "A | B | C | D",
          "explanation": "string",
          "translation": {
            "speaker_a": {
            "name": "string",
            "text": "string"
            },
            "speaker_b": {
            "name": "string",
            "text": "string"
          }
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
  },
  {
    "type": "ESSAY_WORD_FORM",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "sentence": "string",
          "given_words": ["string"],
          "answers": ["string"],
          "knowledge": "string",
          "explanation": {
            "blank_1": "string",
            "blank_2": "string",
            "blank_3": "string"
          },
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "ESSAY_SENTENCE_REWRITING",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "original_sentence": "string",
          "rewrite_prompt": "string",
          "answer": "string",
          "full_rewritten_sentence": "string",
          "knowledge": "string",
          "explanation": "string",
          "translation": {
            "original": "string",
            "rewritten": "string"
          }
        }
      ]
    }
  },
  {
    "type": "ESSAY_COMBINE_SENTENCES",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "sentence_1": "string",
          "sentence_2": "string",
          "rewrite_prompt": "string",
          "answer": "string",
          "combined_sentence": "string",
          "knowledge": "string",
          "explanation": "string",
          "translation": {
            "original_1": "string",
            "original_2": "string",
            "combined": "string"
          }
        }
      ]
    }
  },
  {
    "type": "ESSAY_WORD_ORDERING",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "given_words": "string",
          "correct_sentence": "string",
          "knowledge": "string",
          "explanation": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "ESSAY_WORD_FORM",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "sentence": "string",
          "given_words": ["string"],
          "answer": "string",
          "full_sentence": "string",
          "knowledge": "string",
          "explanation": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "ESSAY_WORD_PROMPT_COMPLETION",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "given_prompts": "string",
          "sentence_starter": "string | null",
          "full_sentence": "string",
          "knowledge": "string",
          "explanation": "string",
          "translation": "string"
        }
      ]
    }
  },
  {
    "type": "OPENING_AND_ORDERING",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "question_groups": [
        {
          "group_number": "number",
          "shared_stem": {
            "range": "string",
            "text": "string"
          },
          "opening_question": {
            "question_number": "number",
            "options": {
              "A": "string",
              "B": "string",
              "C": "string",
              "D": "string"
            },
            "answer": "A | B | C | D",
            "knowledge": "string",
            "explanation": {
              "reasoning": "string",
              "correct_sentence": "string"
            }
          },
          "ordering_question": {
            "question_number": "number",
            "sentences": {
              "a": "string",
              "b": "string",
              "c": "string"
            },
            "options": {
              "A": "string",
              "B": "string",
              "C": "string",
              "D": "string"
            },
            "answer": "A | B | C | D",
            "knowledge": "string",
            "explanation": {
              "steps": ["string"],
              "correct_order": "string",
              "full_passage": "string",
              "translation": "string"
            }
          }
        }
      ]
    }
  },
  {
    "type": "ORDERING_AND_CLOSING",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "question_groups": [
        {
          "group_number": "number",
          "ordering_question": {
            "question_number": "number",
            "passage_intro": "string",
            "sentences": {
              "a": "string",
              "b": "string",
              "c": "string"
            },
            "options": {
              "A": "string",
              "B": "string",
              "C": "string",
              "D": "string"
            },
            "answer": "A | B | C | D",
            "explanation": {
              "steps": ["string"],
              "correct_order": "string",
              "full_passage": "string",
              "translation": "string"
            }
          },
          "closing_question": {
            "question_number": "number",
            "options": {
              "A": "string",
              "B": "string",
              "C": "string",
              "D": "string"
            },
            "answer": "A | B | C | D",
            "knowledge": "string",
            "explanation": {
              "option_analysis": {
                "A": "string",
                "B": "string",
                "C": "string",
                "D": "string"
              },
              "reasoning": "string"
            }
          }
        }
      ]
    }
  },
  {
    "type": "COMPLETE_SENTENCE_GIVEN_WORD",
    "titleQuestion": "string",
    "question_count": "number",
    "start_num": "number",
    "parsed": {
      "questions": [
        {
          "number": "number",
          "given_words": "string",
          "sentence_stem": "string",
          "options": {
            "option_A": "string",
            "option_B": "string",
            "option_C": "string",
            "option_D": "string"
          },
          "correct_option": "A | B | C | D",
          "answer": "string",
          "knowledge": "string",
          "explanation": "string",
          "full_sentence": "string",
          "translation": "string"
        }
      ]
    }
  }
 ]
"""

EXAM_JSON_SCHEMA = """
{
   "exam_id": "string",
    "exam_title": "string",
    "province": "string | null",
    "subject": "string",
    "sections: [
      "section_title:"string | null",
      "questions": [
    {
      "type": "multiple_choice",
      "question_number": "number",
      "question_title": "string | null",
      "media": [  
        {
          "type": "table",
          "context_source": "explicit | implicit",
          "position": "before_question_content | after_question_content",
          "source": "Bảng [X] - Trang [Y]",
          "title": "Tiêu đề bảng",
          "unit": "string | null",
          "headers": ["Cột 1", "Cột 2"],
          "rows": [["Dữ liệu 1", "Dữ liệu 2"]],
          "notes": "string | null",
        }
       ] | null,
      "question_content": "string | null",
      "note":"string | null",
      "options": [
        {
          "option_a": "string |  number",
          "option_b": "string |  number",
          "option_c": "string |  number",
          "option_d": "string |  number",
          "answer": "A | B | C | D | E | F | G | H"
        }
      ],
      "explanation": "string",
      "conclusion":"string"
    },
    {
        "type": "true_false",
        "question_number": "number",
        "question_title": "string | null",
         "media": [  
        {
          "type": "table",
          "position": "before_question_content | after_question_content",
          "context_source": "explicit | implicit",
          "source": "Bảng [X] - Trang [Y]",
          "title": "Tiêu đề bảng",
          "unit": "string | null",
          "headers": ["Cột 1", "Cột 2"],
          "rows": [["Dữ liệu 1", "Dữ liệu 2"]],
          "notes": "string | null"
        }
       ] | null,
        "question_content": "string | null",
        "note":"string | null",
        "images": [],
        "options": [
            {
            "label": "A",
            "content": "string | number",
            "is_correct": "boolean",
            "explanation": "string"
            },
            {
            "label": "B",
            "content": "string | number",
            "is_correct": "boolean",
            "explanation": "string"
            },
            {
            "label": "C",
            "content": "string | number",
            "is_correct": "boolean",
            "explanation": "string"
            },
            {
            "label": "D",
            "content": "string | number",
            "is_correct": "boolean",
            "explanation": "string"
            }
           ],
        "correct_answer": "string"
        },
    {
      "type": "short_answer",
      "question_number": "number",
      "question_title": "string | null",
      "media": [  
        {
          "type": "table",
          "position": "before_question_content | after_question_content",
          "context_source": "explicit | implicit",
          "source": "Bảng [X] - Trang [Y]",
          "title": "Tiêu đề bảng",
          "unit": "string | null",
          "headers": ["Cột 1", "Cột 2"],
          "rows": [["Dữ liệu 1", "Dữ liệu 2"]],
          "notes": "Ghi chú dưới bảng"
        }
      ] | null,
      "question_content": "string | null",
      "note":"string | null",
      "images": [],
      "correct_answer": "string | number",
      "explanation": "string",
      "conclusion":"string"
    },
    {
      "type": "essay",
      "question_number": "number",
      "media": [  
        {
          "type": "table",
          "position": "before_question_content | after_question_content",
          "context_source": "explicit | implicit",
          "source": "Bảng [X] - Trang [Y]",
          "title": "Tiêu đề bảng",
          "unit": "string | null",
          "headers": ["Cột 1", "Cột 2"],
          "rows": [["Dữ liệu 1", "Dữ liệu 2"]],
          "notes": "Ghi chú dưới bảng"
        }
      ] | null,
      "passage_data":[
        {
            "passage_title":"string | null",
            "passage_content":"string | null",
            "notes": "string | null"
        }
        ] | null,
      "question_title": "string | null",
      "question_content": "string | null",
      "note":"string | null",
      "images": [],
      "explanation": "string"
      }
    ]
  ]
}
"""


EXAM_LITERATURE_JSON_SCHEMA = """{
  "exam_data_schema": {
    "exam_id": "string",
    "exam_title": "string",
    "province": "string | null",
    "subject": "string",
    "sections": [
      {
        "section_title": "string",
        "reading_passage": {
          "intro_text": "string | null (Bắt buộc chứa lời dẫn như: Đọc đoạn trích sau, Đọc văn bản...)",
          "content": "string | null",
          "source": "string | null",
        },
        "questions": [
          {
            "number": "number",
            "question_type": "READING | WRITING_200 | WRITING_600",
            "question_content": "string",
            "content_learning_materials":"string | null",
            "content_source":"string | null",
            "solution": {
              "problem_statement": "string | null",
              "structured_content": {
                "a_general_requirements": {
                  "issue": "string | null",
                  "form": "string | null",
                  "length": "string | null",
                  "evidence": "string | null"
                },
                "b_specific_requirements": {
                "name": "string (ví dụ: Yêu cầu cụ thể)",
                "steps": {
                  "b1": {
                    "name": "string ",
                    "content": "string | null (các ý triển khai chi tiết)"
                  },
                  "b2": {
                    "name": "string",
                    "content": "string | null"
                  },
                  "b3": {
                    "name": "string",
                    "content": "string | null"
                  },
                  "b4": {
                    "name": "string | null",
                    "content": "string | null"
                  },
                  "b5": {
                    "name": "string | null",
                    "content": "string | null"
                  }
                }
              },
              "explanation": "string (must use <i> for formatting and \\n for line breaks)"
            }
          }
        ]
      }
    ],
  "formatting_rules": {
    "italic_tag": "<i>text</i>",
    "line_break": "\\n",
    "forbidden_markdown": ["**", "###", "- ", "1. ","*","“","”"],
  }
}
"""


API_KEY = "AIzaSyAUZx6cZjFMEGZjDV9Hv7489s-seEcqMxI"
DRIVE_FOLDER = "https://drive.google.com/drive/folders/19WaudkbI20vukSvswqrHGvv407E6PiLZ"


def extract_folder_id(url):
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise Exception("Không tìm thấy folder ID")
    return match.group(1)

def get_other_txt_file_from_drive():
    try:
        folder_id = extract_folder_id(DRIVE_FOLDER)

        # 1. List files trong folder
        list_url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name = 'promptToolGiaiDe.txt'",
            "fields": "files(id, name, mimeType)"
        }

        res = requests.get(list_url, params=params)
        res.raise_for_status()

        files = res.json().get("files", [])

        if not files:
            raise Exception("❌ Không tìm thấy file promptGiaiDeDiaLi.txt")

        file_id = files[0]["id"]

        # 2. Download file content
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"

        params = {
            "alt":"media",
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

def get_geography_txt_file_from_drive():
    try:
        folder_id = extract_folder_id(DRIVE_FOLDER)

        # 1. List files trong folder
        list_url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name = 'promptGiaiDeDiaLi.md'",
            "fields": "files(id, name, mimeType)"
        }

        res = requests.get(list_url, params=params)
        res.raise_for_status()

        files = res.json().get("files", [])

        if not files:
            raise Exception("❌ Không tìm thấy file promptGiaiDeDiaLi.txt")

        file_id = files[0]["id"]

        # 2. Download file content
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"

        params = {
            "alt":"media",
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

def get_math_txt_file_from_drive():
    try:
        folder_id = extract_folder_id(DRIVE_FOLDER)

        # 1. List files trong folder
        list_url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name = 'promptGiaiDeToan.txt'",
            "fields": "files(id, name, mimeType)"
        }

        res = requests.get(list_url, params=params)
        res.raise_for_status()

        files = res.json().get("files", [])

        if not files:
            raise Exception("❌ Không tìm thấy file promptGiaiDeToan.txt")

        file_id = files[0]["id"]

        # 2. Download file content
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"

        params = {
            "alt":"media",
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

def get_literature_txt_file_from_drive():
    try:
        folder_id = extract_folder_id(DRIVE_FOLDER)

        # 1. List files trong folder
        list_url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name = 'promptGiaiDeNguVanUpgrade.txt'",
            "fields": "files(id, name, mimeType)"
        }

        res = requests.get(list_url, params=params)
        res.raise_for_status()

        files = res.json().get("files", [])

        if not files:
            raise Exception("❌ Không tìm thấy file TA_Huong_dan_giai.md")

        file_id = files[0]["id"]

        # 2. Download file content
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"

        params = {
            "alt":"media",
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

def get_history_md_file_from_drive():
    try:
        folder_id = extract_folder_id(DRIVE_FOLDER)

        # 1. List files trong folder
        list_url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name = 'promptToolGiaiDeLichSu.md'",
            "fields": "files(id, name, mimeType)"
        }

        res = requests.get(list_url, params=params)
        res.raise_for_status()

        files = res.json().get("files", [])

        if not files:
            raise Exception("❌ Không tìm thấy file TA_Huong_dan_giai.md")

        file_id = files[0]["id"]

        # 2. Download file content
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"

        params = {
            "alt":"media",
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

def get_md_file_from_drive():
    try:
        folder_id = extract_folder_id(DRIVE_FOLDER)

        # 1. List files trong folder
        list_url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name = 'TA_Huong_dan_giai_21_4.md'",
            "fields": "files(id, name, mimeType)"
        }

        res = requests.get(list_url, params=params)
        res.raise_for_status()

        files = res.json().get("files", [])

        if not files:
            raise Exception("❌ Không tìm thấy file TA_Huong_dan_giai.md")

        file_id = files[0]["id"]

        # 2. Download file content
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"

        params = {
            "alt":"media",
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
    schema:Any = None,
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
            schema=schema,
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

# async def process_single_pdf(
#     pdf_path: str,
#     prompt: str,
#     client_31: AsyncVertexGemini31,
#     client_25: AsyncVertexClient,
#     schema: Any,
# ):
#     """
#     Xử lý 1 file PDF với cơ chế fallback Gemini 3.1 → 2.5.
#     """
#     result = await solute_with_fallback(
#         pdf_path=pdf_path,
#         prompt=prompt,
#         client_31=client_31,
#         client_25=client_25,
#         schema=schema,
#     )
#     return result

async def process_single_pdf(
    pdf_path: str,
    prompt: str,
    client_31: AsyncVertexGemini31,
    client_25: AsyncVertexClient,
):
    """
    Xử lý 1 file PDF với cơ chế fallback Gemini 3.1 → 2.5.
    Đã thêm try-catch để đảm bảo một file lỗi không làm sập toàn bộ tiến trình.
    """
    try:
        logger.info(f"🚀 Đang bắt đầu xử lý file: {pdf_path}")
        
        result = await solute_with_fallback(
            pdf_path=pdf_path,
            prompt=prompt,
            client_31=client_31,
            client_25=client_25,
        )

        if result is None:
            logger.warning(f"⚠️ Cảnh báo: Kết quả trả về từ file {pdf_path} bị trống (None).")
        else:
            logger.info(f"✅ Xử lý thành công file: {pdf_path}")
            
        return result

    except Exception as e:
        # exc_info=True sẽ in chi tiết trackback lỗi để bạn dễ debug
        logger.error(f"❌ Lỗi nghiêm trọng khi xử lý file {pdf_path}: {str(e)}", exc_info=True)
        
        # Trả về None thay vì raise lỗi để các task khác trong asyncio.gather vẫn chạy tiếp được
        return None


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

# async def solve_english_exam(file_paths: List[str]):
#     print(f">>>>> debug file_paths {file_paths}")

#     raw_schema_list = json.loads(ENGLISH_SCHEMA_SOLUTE)
    
#     valid_schema = {
#         "type": "array",
#         "items": {
#             "anyOf": raw_schema_list
#         }
#     }
#     try:
#         base_prompt = get_md_file_from_drive()

#         full_prompt = f"""
# {base_prompt}

# ========================
# OUTPUT FORMAT (STRICT JSON):


# {ENGLISH_SCHEMA_SOLUTE}

# ### QUY TẮC NGHIÊM NGẶT PHẢI TUÂN THỦ:

# #### 1.Trong các trường passage hoặc tất cả các key và value theo schema có những phần tử hoặc các từ được in nghiêng và in đậm trong đoạn văn hãy viết format dạng <strong><u>abc</u></strong>, ví dụ <strong><u>contribute positively</u></strong> không được bỏ sót

# ### 2. KHÔNG ĐƯỢC BỎ SÓT FORMATTING 
#  - Phải quét tất cả các kí tự được in đậm in nghiêng gạch chân và trả về dạng <strong><u><i>abc</i></u></strong> không được thiếu bất kì 1 kí tự nào.
# """

#         credentials, project_id = get_credentials()

#         client_31 = AsyncVertexGemini31(
#             project_id="onluyen-media",
#             model="gemini-3.1-pro-preview",
#             thinking_level="HIGH"
#         )

#         client_25 = AsyncVertexClient(
#             project_id=project_id,
#             creds=credentials,
#             model="gemini-2.5-pro"
#         )

#         async def run_all():
#             tasks = [
#                 process_single_pdf(pdf_path, full_prompt,client_31, client_25)
#                 for pdf_path in file_paths
#             ]
#             return await asyncio.gather(*tasks)

#         # ✅ FIX HERE
#         results = await run_all()
#         cleaned_results = clean_json(results)
#         print(">>>>> debug cleaned_results:\n", json.dumps(cleaned_results, indent=2, ensure_ascii=False))
#         return cleaned_results


#     except Exception as e:
#         logger.error(f"Error in solve_english_exam: {e}")
#         return []

async def solve_geography_exam(file_paths: List[str]):
    logger.info(f"🚀 Bắt đầu giải đề với {len(file_paths)} files")
    
    try:
        base_prompt =  get_geography_txt_file_from_drive()
        full_prompt = f"""
{base_prompt}
========================
        YÊU CẦU OUTPUT JSON MÔN VĂN
        =====================

        - Chỉ trả về JSON đúng theo schema dưới đây
        - Không markdown
        - Không ```json
        - Không giải thích ngoài JSON
        - Field nào không dùng thì bỏ qua
        - Giữ nguyên cấu trúc key
        - Bắt buộc giữ formatting <b><i>

        SCHEMA:
{EXAM_JSON_SCHEMA}

"""

        # 1. Khởi tạo Provider thông qua Factory
        credentials, project_id = get_credentials()
        
        # Vertex Clients (dùng cho trường hợp provider là vertex)
        client_25 = AsyncVertexClient(project_id=project_id, creds=credentials, model="gemini-2.5-pro")
        
        BASE_DIR = Path(__file__).resolve().parent 
        credentials_path = str(BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json")
        client_31 = AsyncVertexGemini31(
            project_id="onluyen-media",
            location="global",
            thinking_level="HIGH",
            credentials_path=credentials_path
        )

        provider_name = os.getenv("LLM_PROVIDER", "openai") # Có thể set "openai" trong .env
        provider = build_llm_provider(
            provider_name=provider_name,
            client_31=client_31,
            client_25=client_25
        )

        # 2. Xử lý song song các file PDF bằng provider
        async def process_file(pdf_path):
            try:
                # Gọi phương thức solute đã được thống nhất interface
                result = await provider.solute(
                    prompt=full_prompt,
                    pdf_path=pdf_path,
                    schema=None # Hoặc truyền schema nếu provider hỗ trợ
                )
                return result
            except Exception as e:
                logger.error(f"Lỗi khi xử lý file {pdf_path}: {e}")
                return None

        tasks = [process_file(p) for p in file_paths]
        results = await asyncio.gather(*tasks)

        # 3. Clean và parse kết quả
        cleaned_results = []
        for res in results:
            if res:
                # Lúc này res đã là một chuỗi JSON chứa toàn bộ câu hỏi của 1 file PDF
                parsed = _safe_parse_json(res) 
                if parsed:
                    # parsed bây giờ là List[Dict] (danh sách các block câu hỏi)
                    if isinstance(parsed, list):
                        cleaned_results.extend(parsed) # Gộp vào kết quả tổng
                    else:
                        cleaned_results.append(parsed)
        merge_data = merge_exam_sections(cleaned_results)
        logger.info(f"✅ Đã giải xong {len(cleaned_results)}/{len(file_paths)} files")
        # return cleaned_results
        return merge_data

    except Exception as e:
        logger.error(f"Error in solve_english_exam: {e}", exc_info=True)
        return []

def merge_exam_sections(cleaned_results):
    """
    Gộp tất cả các sections từ nhiều file/kết quả vào đối tượng đầu tiên.
    """
    if not cleaned_results or len(cleaned_results) < 2:
        return cleaned_results

    # Lấy đối tượng đầu tiên làm gốc (Base Exam)
    base_exam = cleaned_results[0]
    
    # Nếu đối tượng gốc chưa có mảng sections, khởi tạo nó
    if "sections" not in base_exam:
        base_exam["sections"] = []

    # Lặp qua các kết quả từ file thứ 2 trở đi
    for extra_exam in cleaned_results[1:]:
        if isinstance(extra_exam, dict) and "sections" in extra_exam:
            # Gộp các section của file này vào file gốc
            base_exam["sections"].extend(extra_exam["sections"])
        elif isinstance(extra_exam, list):
            # Trường hợp kết quả trả về là một list các exam
            for item in extra_exam:
                if "sections" in item:
                    base_exam["sections"].extend(item["sections"])

    # Trả về kết quả cuối cùng là một list chứa 1 exam duy nhất đã gộp
    return [base_exam]


async def solve_history_exam(file_paths: List[str]):
    logger.info(f"🚀 Bắt đầu giải đề với {len(file_paths)} files")
    
    try:
        base_prompt =   get_history_md_file_from_drive()
        full_prompt = f"""
{base_prompt}
========================
        YÊU CẦU OUTPUT JSON MÔN VĂN
        =====================

        - Chỉ trả về JSON đúng theo schema dưới đây
        - Không markdown
        - Không ```json
        - Không giải thích ngoài JSON
        - Field nào không dùng thì bỏ qua
        - Giữ nguyên cấu trúc key
        - Bắt buộc giữ formatting <b><i>

        SCHEMA:
{EXAM_JSON_SCHEMA}

"""

        # 1. Khởi tạo Provider thông qua Factory
        credentials, project_id = get_credentials()
        
        # Vertex Clients (dùng cho trường hợp provider là vertex)
        client_25 = AsyncVertexClient(project_id=project_id, creds=credentials, model="gemini-2.5-pro")
        
        BASE_DIR = Path(__file__).resolve().parent 
        credentials_path = str(BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json")
        client_31 = AsyncVertexGemini31(
            project_id="onluyen-media",
            location="global",
            thinking_level="HIGH",
            credentials_path=credentials_path
        )

        provider_name = os.getenv("LLM_PROVIDER", "openai") # Có thể set "openai" trong .env
        provider = build_llm_provider(
            provider_name=provider_name,
            client_31=client_31,
            client_25=client_25
        )

        # 2. Xử lý song song các file PDF bằng provider
        async def process_file(pdf_path):
            try:
                # Gọi phương thức solute đã được thống nhất interface
                result = await provider.solute(
                    prompt=full_prompt,
                    pdf_path=pdf_path,
                    schema=None # Hoặc truyền schema nếu provider hỗ trợ
                )
                return result
            except Exception as e:
                logger.error(f"Lỗi khi xử lý file {pdf_path}: {e}")
                return None

        tasks = [process_file(p) for p in file_paths]
        results = await asyncio.gather(*tasks)

        # 3. Clean và parse kết quả
        cleaned_results = []
        for res in results:
            if res:
                # Lúc này res đã là một chuỗi JSON chứa toàn bộ câu hỏi của 1 file PDF
                parsed = _safe_parse_json(res) 
                if parsed:
                    # parsed bây giờ là List[Dict] (danh sách các block câu hỏi)
                    if isinstance(parsed, list):
                        cleaned_results.extend(parsed) # Gộp vào kết quả tổng
                    else:
                        cleaned_results.append(parsed)
        merge_data = merge_exam_sections(cleaned_results)

        logger.info(f"✅ Đã giải xong {len(cleaned_results)}/{len(file_paths)} files")
        return merge_data

    except Exception as e:
        logger.error(f"Error in solve_english_exam: {e}", exc_info=True)
        return []

async def solve_math_exam(file_paths: List[str]):
    logger.info(f"🚀 Bắt đầu giải đề với {len(file_paths)} files")
    
    try:
        base_prompt =  get_math_txt_file_from_drive()
        full_prompt = f"""
{base_prompt}
========================
        YÊU CẦU OUTPUT JSON MÔN VĂN
        =====================

        - Chỉ trả về JSON đúng theo schema dưới đây
        - Không markdown
        - Không ```json
        - Không giải thích ngoài JSON
        - Field nào không dùng thì bỏ qua
        - Giữ nguyên cấu trúc key
        - Bắt buộc giữ formatting <b><i>

        SCHEMA:
{EXAM_JSON_SCHEMA}

"""

        # 1. Khởi tạo Provider thông qua Factory
        credentials, project_id = get_credentials()
        
        # Vertex Clients (dùng cho trường hợp provider là vertex)
        client_25 = AsyncVertexClient(project_id=project_id, creds=credentials, model="gemini-2.5-pro")
        
        BASE_DIR = Path(__file__).resolve().parent 
        credentials_path = str(BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json")
        client_31 = AsyncVertexGemini31(
            project_id="onluyen-media",
            location="global",
            thinking_level="HIGH",
            credentials_path=credentials_path
        )

        provider_name = os.getenv("LLM_PROVIDER", "openai") # Có thể set "openai" trong .env
        provider = build_llm_provider(
            provider_name=provider_name,
            client_31=client_31,
            client_25=client_25
        )

        # 2. Xử lý song song các file PDF bằng provider
        async def process_file(pdf_path):
            try:
                # Gọi phương thức solute đã được thống nhất interface
                result = await provider.solute(
                    prompt=full_prompt,
                    pdf_path=pdf_path,
                    schema=None # Hoặc truyền schema nếu provider hỗ trợ
                )
                return result
            except Exception as e:
                logger.error(f"Lỗi khi xử lý file {pdf_path}: {e}")
                return None

        tasks = [process_file(p) for p in file_paths]
        results = await asyncio.gather(*tasks)

        # 3. Clean và parse kết quả
        cleaned_results = []
        for res in results:
            if res:
                # Lúc này res đã là một chuỗi JSON chứa toàn bộ câu hỏi của 1 file PDF
                parsed = _safe_parse_json(res) 
                if parsed:
                    # parsed bây giờ là List[Dict] (danh sách các block câu hỏi)
                    if isinstance(parsed, list):
                        cleaned_results.extend(parsed) # Gộp vào kết quả tổng
                    else:
                        cleaned_results.append(parsed)
        merge_data = merge_exam_sections(cleaned_results)

        logger.info(f"✅ Đã giải xong {len(cleaned_results)}/{len(file_paths)} files")
        return merge_data

    except Exception as e:
        logger.error(f"Error in solve_english_exam: {e}", exc_info=True)
        return []


async def solve_other_exam(file_paths: List[str]):
    logger.info(f"🚀 Bắt đầu giải đề với {len(file_paths)} files")
    
    try:
        base_prompt = get_other_txt_file_from_drive()
        full_prompt = f"""
{base_prompt}
========================
        YÊU CẦU OUTPUT JSON MÔN VĂN
        =====================

        - Chỉ trả về JSON đúng theo schema dưới đây
        - Không markdown
        - Không ```json
        - Không giải thích ngoài JSON
        - Field nào không dùng thì bỏ qua
        - Giữ nguyên cấu trúc key
        - Bắt buộc giữ formatting <b><i>
        - File nào có bảng phải trả về data dạng bảng

        SCHEMA:
{EXAM_JSON_SCHEMA}

"""

        # 1. Khởi tạo Provider thông qua Factory
        credentials, project_id = get_credentials()
        
        # Vertex Clients (dùng cho trường hợp provider là vertex)
        client_25 = AsyncVertexClient(project_id=project_id, creds=credentials, model="gemini-2.5-pro")
        
        BASE_DIR = Path(__file__).resolve().parent 
        credentials_path = str(BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json")
        client_31 = AsyncVertexGemini31(
            project_id="onluyen-media",
            location="global",
            thinking_level="HIGH",
            credentials_path=credentials_path
        )

        provider_name = os.getenv("LLM_PROVIDER", "openai") # Có thể set "openai" trong .env
        provider = build_llm_provider(
            provider_name=provider_name,
            client_31=client_31,
            client_25=client_25
        )

        # 2. Xử lý song song các file PDF bằng provider
        async def process_file(pdf_path):
            try:
                # Gọi phương thức solute đã được thống nhất interface
                result = await provider.solute(
                    prompt=full_prompt,
                    pdf_path=pdf_path,
                    schema=None # Hoặc truyền schema nếu provider hỗ trợ
                )
                return result
            except Exception as e:
                logger.error(f"Lỗi khi xử lý file {pdf_path}: {e}")
                return None

        tasks = [process_file(p) for p in file_paths]
        results = await asyncio.gather(*tasks)

        # 3. Clean và parse kết quả
        cleaned_results = []
        for res in results:
            if res:
                # Lúc này res đã là một chuỗi JSON chứa toàn bộ câu hỏi của 1 file PDF
                parsed = _safe_parse_json(res) 
                if parsed:
                    # parsed bây giờ là List[Dict] (danh sách các block câu hỏi)
                    if isinstance(parsed, list):
                        cleaned_results.extend(parsed) # Gộp vào kết quả tổng
                    else:
                        cleaned_results.append(parsed)
        merge_data = merge_exam_sections(cleaned_results)
        logger.info(f"✅ Đã giải xong {len(cleaned_results)}/{len(file_paths)} files")
        return merge_data

    except Exception as e:
        logger.error(f"Error in solve_other_exam: {e}", exc_info=True)
        return []


async def solve_literature_exam(file_paths: List[str]):
    logger.info(f"🚀 Bắt đầu giải đề với {len(file_paths)} files")
    
    try:
        base_prompt = get_literature_txt_file_from_drive()
        full_prompt = f"""
{base_prompt}
========================
        YÊU CẦU OUTPUT JSON MÔN VĂN
        =====================

        - Chỉ trả về JSON đúng theo schema dưới đây
        - Không markdown
        - Không ```json
        - Không giải thích ngoài JSON
        - Field nào không dùng thì bỏ qua
        - Giữ nguyên cấu trúc key
        - Bắt buộc giữ formatting <b><i>

        SCHEMA:
{EXAM_LITERATURE_JSON_SCHEMA}

"""

        # 1. Khởi tạo Provider thông qua Factory
        credentials, project_id = get_credentials()
        
        # Vertex Clients (dùng cho trường hợp provider là vertex)
        client_25 = AsyncVertexClient(project_id=project_id, creds=credentials, model="gemini-2.5-pro")
        
        BASE_DIR = Path(__file__).resolve().parent 
        credentials_path = str(BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json")
        client_31 = AsyncVertexGemini31(
            project_id="onluyen-media",
            location="global",
            thinking_level="HIGH",
            credentials_path=credentials_path
        )

        provider_name = os.getenv("LLM_PROVIDER", "openai") # Có thể set "openai" trong .env
        provider = build_llm_provider(
            provider_name=provider_name,
            client_31=client_31,
            client_25=client_25
        )

        # 2. Xử lý song song các file PDF bằng provider
        async def process_file(pdf_path):
            try:
                # Gọi phương thức solute đã được thống nhất interface
                result = await provider.solute(
                    prompt=full_prompt,
                    pdf_path=pdf_path,
                    schema=None # Hoặc truyền schema nếu provider hỗ trợ
                )
                return result
            except Exception as e:
                logger.error(f"Lỗi khi xử lý file {pdf_path}: {e}")
                return None

        tasks = [process_file(p) for p in file_paths]
        results = await asyncio.gather(*tasks)

        # 3. Clean và parse kết quả
        cleaned_results = []
        for res in results:
            if res:
                # Lúc này res đã là một chuỗi JSON chứa toàn bộ câu hỏi của 1 file PDF
                parsed = _safe_parse_json(res) 
            if parsed:
                # Nếu AI trả về 1 object đơn lẻ, ta bọc nó vào list
                if isinstance(parsed, dict):
                    cleaned_results.append(parsed)
                # Nếu AI trả về list, ta gộp vào cleaned_results
                elif isinstance(parsed, list):
                    cleaned_results.extend(parsed)
        logger.info(f"✅ Đã giải xong {len(cleaned_results)}/{len(file_paths)} files")
        return cleaned_results

    except Exception as e:
        logger.error(f"Error in solve_english_exam: {e}", exc_info=True)
        return []



async def solve_english_exam(file_paths: List[str]):
    logger.info(f"🚀 Bắt đầu giải đề với {len(file_paths)} files")
    
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

        # 1. Khởi tạo Provider thông qua Factory
        credentials, project_id = get_credentials()
        
        # Vertex Clients (dùng cho trường hợp provider là vertex)
        client_25 = AsyncVertexClient(project_id=project_id, creds=credentials, model="gemini-2.5-pro")
        
        BASE_DIR = Path(__file__).resolve().parent 
        credentials_path = str(BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json")
        client_31 = AsyncVertexGemini31(
            project_id="onluyen-media",
            location="global",
            thinking_level="HIGH",
            credentials_path=credentials_path
        )

        provider_name = os.getenv("LLM_PROVIDER", "openai") # Có thể set "openai" trong .env
        provider = build_llm_provider(
            provider_name=provider_name,
            client_31=client_31,
            client_25=client_25
        )

        # 2. Xử lý song song các file PDF bằng provider
        async def process_file(pdf_path):
            try:
                # Gọi phương thức solute đã được thống nhất interface
                result = await provider.solute(
                    prompt=full_prompt,
                    pdf_path=pdf_path,
                    schema=None # Hoặc truyền schema nếu provider hỗ trợ
                )
                return result
            except Exception as e:
                logger.error(f"Lỗi khi xử lý file {pdf_path}: {e}")
                return None

        tasks = [process_file(p) for p in file_paths]
        results = await asyncio.gather(*tasks)

        # 3. Clean và parse kết quả
        cleaned_results = []
        for res in results:
            if res:
                # Lúc này res đã là một chuỗi JSON chứa toàn bộ câu hỏi của 1 file PDF
                parsed = _safe_parse_json(res) 
                if parsed:
                    # parsed bây giờ là List[Dict] (danh sách các block câu hỏi)
                    if isinstance(parsed, list):
                        cleaned_results.extend(parsed) # Gộp vào kết quả tổng
                    else:
                        cleaned_results.append(parsed)
        logger.info(f"✅ Đã giải xong {len(cleaned_results)}/{len(file_paths)} files")
        return cleaned_results

    except Exception as e:
        logger.error(f"Error in solve_english_exam: {e}", exc_info=True)
        return []


