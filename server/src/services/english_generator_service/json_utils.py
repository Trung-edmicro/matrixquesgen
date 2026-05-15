import json
import re

from fastapi import logger


# def _safe_parse_json(raw: str) -> dict | None:
#     """
#     Cố gắng parse JSON từ response của AI.
#     Xử lý trường hợp AI trả về markdown fences hoặc text thừa.
#     """
#     if not raw:
#         return None

#     # Strip markdown code fences nếu có
#     text = raw.strip()
#     text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
#     text = re.sub(r"\s*```$", "", text)
#     text = text.strip()

#     # Tìm JSON object đầu tiên
#     start = text.find("{")
#     if start == -1:
#         logger.warning("No JSON object found in AI response")
#         return None

#     # Tìm closing brace tương ứng (depth counting)
#     depth = 0
#     end = -1
#     in_string = False
#     escape_next = False

#     for i, ch in enumerate(text[start:], start=start):
#         if escape_next:
#             escape_next = False
#             continue
#         if ch == "\\" and in_string:
#             escape_next = True
#             continue
#         if ch == '"':
#             in_string = not in_string
#             continue
#         if in_string:
#             continue
#         if ch == "{":
#             depth += 1
#         elif ch == "}":
#             depth -= 1
#             if depth == 0:
#                 end = i
#                 break

#     if end == -1:
#         logger.warning("Could not find closing brace in AI response")
#         return None

#     json_str = text[start:end + 1]

#     try:
#         return json.loads(json_str)
#     except json.JSONDecodeError as e:
#         logger.warning(f"JSON parse error: {e}. Attempting cleanup...")

#         # Cleanup: loại bỏ trailing commas trước } hoặc ]
#         json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
#         try:
#             return json.loads(json_str)
#         except json.JSONDecodeError as e2:
#             logger.error(f"JSON parse failed after cleanup: {e2}")
#             return None


def _safe_parse_json(raw: str) -> any:
    if not raw:
        return None

    text = raw.strip()
    # Loại bỏ markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Tìm vị trí bắt đầu của JSON (có thể là { hoặc [)
    start_match = re.search(r"[\{\[]", text)
    if not start_match:
        return None
    
    start_idx = start_match.start()
    
    # Tìm dấu đóng tương ứng
    # Cách đơn giản nhất là thử parse từ start_idx
    # Nếu text chứa rác ở sau, json.loads sẽ lỗi, ta cần cắt dần
    for end_idx in range(len(text), start_idx, -1):
        try:
            return json.loads(text[start_idx:end_idx])
        except json.JSONDecodeError:
            continue
            
    return None