# services/regenerate_english_service.py

import asyncio
import os
from pathlib import Path
import traceback


from server.src.api.callApi import get_credentials
from server.src.services.english_generator_service.constants import(PROMPTS, SENTENCE_COMPLETION_JSON_SCHEMA,SENTENCE_TRANSFORMATION_JSON_SCHEMA, ARRANGE_SOLUTION_TEMPLATE, CLOZE_EXPLANATION_TEMPLATE, ERROR_IDENTIFICATION_JSON_SCHEMA,ESSAY_COMBINE_SENTENCES_THPT_JSON_SCHEMA,ESSAY_SENTENCE_REWRITING_THPT_JSON_SCHEMA,
                   ESSAY_WORD_FORM_SENTENCE_COMPLETION_JSON_SCHEMA,ESSAY_WORD_ORDERING_THPT_JSON_SCHEMA,ESSAY_WORD_PROMPT_SENTENCE_COMPLETION_THPT_JSON_SCHEMA,SILENT_PHASE_EXPLANATION_TEMPLATE,READING_COMPREHENSION_EXPLANATION_TEMPLATE,WORD_REORDERING_JSON_SCHEMA, ARRANGE_JSON_SCHEMA,CLOZE_JSON_SCHEMA, CLOZE_WITH_TITLE_JSON_SCHEMA, DIALOGUE_COMPLETION_JSON_SCHEMA, LOGICAL_THINKING_JSON_SCHEMA, PRONUNCIATION_STRESS_JSON_SCHEMA, SYNONYM_ANTONYM_JSON_SCHEMA, WORD_FORM_SENTENCE_COMPLETION_THPT_JSON_SCHEMA)
from server.src.services.english_generator_service.english_generator_service import _safe_parse_json, limited_generate, load_prompt, safe_str
from server.src.services.english_generator_service.llm_factory import build_llm_provider
from server.src.services.english_generator_service.vertex_async_3_1_model import AsyncVertexGemini31
from server.src.services.english_generator_service.vertex_async_client import AsyncVertexClient

# bạn import thêm schema khác nếu cần


def handle_sentence_completion(payload):

    # prompt_template = load_prompt(PROMPTS["Hoàn thành câu"])

    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    question_number = payload["question_number"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")
    print(f">>>>> debug question_number {question_number}")
    output_rule = SENTENCE_COMPLETION_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )
    print(f">>>>> debug output_rule {output_rule}")

    prompt_template = load_prompt(PROMPTS["Hoàn thành câu"])

    formatted_prompt = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt}

## CURRENT QUESTION
Đánh số thứ tự chuẩn theo số thứ tự hiện tại của câu hỏi
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule}
"""

    return ai_input


async def regenerate_english_question(payload: dict):
    print(f">>>>> debug regenerate_english_question payload{payload}")

    # =========================
    # 1. Init AI
    # =========================
    credentials, project_id = get_credentials()

    client_25 = AsyncVertexClient(
        project_id=project_id,
        creds=credentials,
        model="gemini-2.5-pro"
    )

    BASE_DIR = Path(__file__).resolve().parent
    credentials_path = str(BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json")

    client_31 = AsyncVertexGemini31(
        project_id="onluyen-media",
        location="global",
        thinking_level="HIGH",
        credentials_path=credentials_path
    )
    provider_name = os.getenv("LLM_PROVIDER", "vertex")
    
    provider = build_llm_provider(
            provider_name=provider_name,
            client_31=client_31,
            client_25=client_25
        )

    # =========================
    # 2. Dispatcher
    # =========================
    q_type = payload["type"]
    # print(f">>>>> debug q_type {q_type}")

    handler = HANDLERS.get(q_type)

    print(f">>>>> debug handler {handler}")

    if not handler:
        raise Exception(f"Unsupported type: {q_type}")

    ai_input = handler(payload)
    # if q_type == "SENTENCE_COMPLETION":
    #     print(">>>>> calling handle_sentence_completion", flush=True)
    #     ai_input, schema = handle_sentence_completion(payload)
    # print(f">>>>>>> debug ai_input{ai_input}")
    # =========================
    # 3. Call AI
    # =========================
    # response = await limited_generate(client_31, client_25, ai_input)
    response = await limited_generate(provider, ai_input)


    parsed = _safe_parse_json(response)
    print(f">>>>> debug parsed {parsed}")
    return parsed

# async def regenerate_english_question(payload: dict):
#     try:
#         print(f">>>>> debug regenerate_english_question payload {payload}")

#         # =========================
#         # 1. Init AI
#         # =========================
#         credentials, project_id = get_credentials()

#         client_25 = AsyncVertexClient(
#             project_id=project_id,
#             creds=credentials,
#             model="gemini-2.5-pro"
#         )

#         BASE_DIR = Path(__file__).resolve().parent
#         credentials_path = str(
#             BASE_DIR / "data" / "SA" / "sinh-de-tuong-tu-syscfg.bin 2.json"
#         )

#         client_31 = AsyncVertexGemini31(
#             project_id="onluyen-media",
#             location="global",
#             thinking_level="HIGH",
#             credentials_path=credentials_path
#         )

#         # =========================
#         # 2. Dispatcher
#         # =========================
#         q_type = payload["type"]

#         handler = HANDLERS.get(q_type)

#         print(f">>>>> debug handler {handler}")

#         if not handler:
#             raise Exception(f"Unsupported type: {q_type}")

#         ai_input = handler(payload)

#         print(f">>>>> debug ai_input {ai_input}")

#         # =========================
#         # 3. Call AI
#         # =========================
#         response = await limited_generate(
#             client_31,
#             client_25,
#             ai_input
#         )

#         print(f">>>>> debug raw response {response}")

#         parsed = _safe_parse_json(response)

#         print(f">>>>> debug parsed {parsed}")

#         return {
#             "status": "success",
#             "parsed": parsed
#         }

#     except Exception as e:
#         print(">>>>>> ERROR regenerate_english_question")
#         print(traceback.format_exc())

#         return {
#             "status": "error",
#             "message": str(e),
#             "trace": traceback.format_exc()
#         }





def handle_synonym_antonym(payload):

    prompt_template = load_prompt(PROMPTS["Đồng nghĩa/Trái nghĩa"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_synonym_antonym = SYNONYM_ANTONYM_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_synonym_antoynym = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_synonym_antoynym}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_synonym_antonym}
"""

    return ai_input, output_rule_synonym_antonym

def handle_error_identification(payload):

    prompt_template = load_prompt(PROMPTS["Tìm lỗi sai"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_error_identification =  ERROR_IDENTIFICATION_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_error_identification = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_error_identification}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_error_identification}
"""

    return ai_input, output_rule_error_identification

def handle_sentence_transformation(payload):

    prompt_template = load_prompt(PROMPTS["Kết hợp/viết lại câu"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_sentence_transformation =  ERROR_IDENTIFICATION_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_sentence_transformation = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_sentence_transformation}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_sentence_transformation}
"""

    return ai_input, output_rule_sentence_transformation

def handle_word_ordering(payload):

    prompt_template = load_prompt(PROMPTS["Sắp xếp từ"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_error_identification =  ERROR_IDENTIFICATION_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_error_identification = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_error_identification}
    
## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_error_identification}
"""

    return ai_input, output_rule_error_identification

def handle_pronounciation_stress(payload):

    prompt_template = load_prompt(PROMPTS["Phát âm/Trọng âm"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_pronounciation_stress =  PRONUNCIATION_STRESS_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_pronounciation_stress = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_pronounciation_stress}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_pronounciation_stress}
"""

    return ai_input, output_rule_pronounciation_stress


def handle_dialouge_competition(payload):

    prompt_template = load_prompt(PROMPTS["Câu giao tiếp"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_dialouge_competition =  PRONUNCIATION_STRESS_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_dialouge_competition = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_dialouge_competition}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_dialouge_competition}
"""

    return ai_input, output_rule_dialouge_competition

def handle_logical_thinking(payload):

    prompt_template = load_prompt(PROMPTS["Tư duy/Tình huống"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_logical_thinking =  LOGICAL_THINKING_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_logical_thinking = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_logical_thinking}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_logical_thinking}
"""

    return ai_input, output_rule_logical_thinking

def handle_essay_sentence_rewriting(payload):

    prompt_template = load_prompt(PROMPTS["Tư duy/Tình huống"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_essay_sentence_rewriting =  ESSAY_SENTENCE_REWRITING_THPT_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_essay_sentence_rewriting = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_essay_sentence_rewriting}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_essay_sentence_rewriting}
"""

    return ai_input, output_rule_essay_sentence_rewriting


def handle_essay_combines_sentences(payload):

    prompt_template = load_prompt(PROMPTS["Tự luận/Kết hợp câu"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_essay_combines_sentences =  ESSAY_COMBINE_SENTENCES_THPT_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_essay_combines_sentences = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_essay_combines_sentences}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_essay_combines_sentences}
"""

    return ai_input, output_rule_essay_combines_sentences

def handle_essay_word_ordering(payload):

    prompt_template = load_prompt(PROMPTS["Tư duy/Tình huống"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_essay_word_ordering =   ESSAY_WORD_ORDERING_THPT_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_essay_word_ordering = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_essay_word_ordering}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_essay_word_ordering}
"""

    return ai_input, output_rule_essay_word_ordering


def handle_arrange(payload):

    prompt_template = load_prompt(PROMPTS["Sắp xếp"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_arrange =  ARRANGE_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_arrange = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_arrange}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_arrange}
"""

    return ai_input, output_rule_arrange

def handle_essay_word_form_completion(payload):

    prompt_template = load_prompt(PROMPTS["Tư duy/Tình huống"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_essay_word_form_completion =  ESSAY_WORD_FORM_SENTENCE_COMPLETION_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_essay_word_form_completion = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_essay_word_form_completion}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_essay_word_form_completion}
"""

    return ai_input, output_rule_essay_word_form_completion

def handle_essay_word_prompt_sentence_completion(payload):

    prompt_template = load_prompt(PROMPTS["Tư duy/Tình huống"])

    question_number = payload["question_number"]
    topic = payload["topic"]
    diff = payload["diff"]
    level = payload["level"]
    spec = payload["spec"]
    feedback = payload["user_feedback"]
    current_q = payload["current_question_data"]
    text_type = payload.get("text_type", "")

    output_rule_essay_word_prompt_sentence_completion =  ESSAY_WORD_PROMPT_SENTENCE_COMPLETION_THPT_JSON_SCHEMA.format(
        N_Q=question_number,
        START_NUM=question_number
    )

    formatted_prompt_essay_word_prompt_sentence_completion = (
        prompt_template
        .replace("{TOPIC_NAME}", safe_str(topic))
        .replace("{TEXT_TYPE}", safe_str(text_type))
        .replace("{CEFR_LEVEL}", safe_str(diff))
    )

    ai_input = f"""
{formatted_prompt_essay_word_prompt_sentence_completion}

## CURRENT QUESTION
{current_q}

## USER FEEDBACK
{feedback}

## REQUIREMENT
- Sửa lại câu hỏi
- Giữ dạng: {spec}
- Mức độ: {level}
- Độ khó: {diff}

## OUTPUT FORMAT
{output_rule_essay_word_prompt_sentence_completion}
"""

    return ai_input, output_rule_essay_word_prompt_sentence_completion

# def handle_passage_based_regenerate(payload):
#     """
#     Dùng chung cho CLOZE, RC, GAP
#     """
#     q_type = payload["type"]
#     feedback = payload["user_feedback"]
#     q_number = payload.get("question_number") # Có thể None nếu sinh cả block
#     passage = payload.get("passage", "")
#     passage_title = payload.get("passage_title","")
#     current_data = payload["current_question_data"]
    
#     # Xác định Schema
#     # Nếu q_number có giá trị => Sinh 1 câu => Schema chỉ gồm mảng questions 1 phần tử
#     # Nếu q_number là None => Sinh cả block => Schema gồm passage + questions
#     if q_number:
#         output_rule = CLOZE_JSON_SCHEMA.format(N_Q=q_number, START_NUM=q_number)
#         mode_desc = f"Giữ nguyên đoạn văn dưới đây, chỉ sửa lại duy nhất câu hỏi số {q_number}."
#     else:
#         output_rule = CLOZE_WITH_TITLE_JSON_SCHEMA # Schema có cả field passage
#         mode_desc = "Viết lại một đoạn văn mới hoàn toàn và các câu hỏi đi kèm dựa trên feedback."

#     prompt_template = load_prompt(PROMPTS.get(q_type, PROMPTS["Điền từ"]))

#     ai_input = f"""
# {prompt_template}

# ## CONTEXT
# {mode_desc}

# ## CURRENT PASSAGE
# {passage}

# ## CURRENT QUESTION/DATA
# {current_data}

# ## USER FEEDBACK
# {feedback}

# ## REQUIREMENT
# - Mức độ: {payload['level']}
# - Độ khó: {payload['diff']}
# - Đảm bảo câu hỏi logic với nội dung bài đọc.

# ## OUTPUT FORMAT
# {output_rule}
# """
#     return ai_input


def handle_passage_based_regenerate(payload):
    q_type = payload["type"]
    feedback = payload["user_feedback"]
    q_number = payload.get("question_number")
    passage = payload.get("passage", "")
    current_data = payload["current_question_data"]
    text_type = payload.get("text_type", "")
    diff = payload.get("diff", "B2")
    level = payload.get("level", "Thông hiểu")

    # =========================
    # MAP TYPE -> PROMPT KEY
    # =========================
    TYPE_TO_PROMPT_KEY = {
        "RC": "Đọc hiểu",
        "CLOZE": "Điền từ",
        "GAP": "Điền cụm từ/điền câu"
    }

    prompt_key = TYPE_TO_PROMPT_KEY.get(q_type, "Điền từ")

    # =========================
    # MODE
    # =========================
    if q_number:
        # regenerate 1 question
        output_rule = CLOZE_JSON_SCHEMA.format(
            N_Q=1,
            START_NUM=q_number
        )

        mode_desc = (
            f"Giữ nguyên đoạn văn, "
            f"chỉ sửa lại câu hỏi số {q_number} "
            f"dựa trên yêu cầu."
        )

    else:
        # regenerate whole block
        q_count = (
            len(current_data.get("questions", []))
            if isinstance(current_data, dict)
            else 5
        )

        start_num = (
            current_data.get("questions", [{}])[0].get("number", 1)
            if isinstance(current_data, dict)
            else 1
        )

        output_rule = CLOZE_WITH_TITLE_JSON_SCHEMA.format(
            N_Q=q_count,
            START_NUM=start_num,
            TEXT_TYPE=payload.get("text_type", "")
        )

        mode_desc = (
            "Viết lại một đoạn văn hoàn toàn mới "
            "và các câu hỏi đi kèm "
            "dựa trên chủ đề và feedback."
        )

    # =========================
    # LOAD PROMPT
    # =========================
    prompt_path = PROMPTS.get(prompt_key)

    if not prompt_path:
        raise Exception(
            f"Prompt not found for q_type={q_type}, "
            f"prompt_key={prompt_key}"
        )

    prompt_template = load_prompt(prompt_path)

    # =========================
    # AI INPUT
    # =========================
    ai_input = f"""
        {prompt_template}

        ## CONTEXT
        {mode_desc}

        ## CURRENT DATA
        Passage: {passage}

        Current Questions:
        {current_data}

        ## USER FEEDBACK
        {feedback}

        ## CONSTRAINTS
        - Topic: {payload.get('topic')}
        - CEFR Level: {diff}
        - Cognitive Level: {level}

        ## OUTPUT INSTRUCTION
        Tuyệt đối không nhắc lại A,B,C,D
        Phải viết lại toàn bộ nội dung của các đáp án A,B,C,D
        Trả về JSON đúng cấu trúc sau:


        {output_rule}
"""

    return ai_input


# Cập nhật HANDLERS mapping


HANDLERS = {
    "GAP":handle_passage_based_regenerate,
    "RC": handle_passage_based_regenerate,
    "CLOZE": handle_passage_based_regenerate,
    "ARRANGE": handle_arrange,
    "SENTENCE_COMPLETION": handle_sentence_completion,
    "SYNONYM_ANTONYM": handle_synonym_antonym,
    "ERROR_IDENTIFICATION": handle_error_identification,
    "SENTENCE_TRANSFORMATION": handle_sentence_transformation,
    "WORD_ORDERING": handle_word_ordering,
    "PROUNOUNCIATION_STRESS": handle_pronounciation_stress,
    "DIALOUGE_COMPLETION": handle_dialouge_competition,
    "LOGICAL_THINKING": handle_logical_thinking,
    "ESSAY_REWRITING_SENTENCES":handle_essay_sentence_rewriting,
    "ESSAY_COMBINE_SENTENCES": handle_essay_combines_sentences,
    "ESSAY_WORD_ORDERING": handle_word_ordering,
    "ESSAY_WORD_FORM_SENTENCE_COMPLETION": handle_essay_word_form_completion,
    "ESSAY_WORD_PROMPT_SENTENCE": handle_essay_word_prompt_sentence_completion
}

