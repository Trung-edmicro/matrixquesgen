# services/regenerate_english_service.py

import asyncio
from pathlib import Path


from server.src.api.callApi import get_credentials
from server.src.services.english_generator_service.constants import(PROMPTS, SENTENCE_COMPLETION_JSON_SCHEMA,SENTENCE_TRANSFORMATION_JSON_SCHEMA, ARRANGE_SOLUTION_TEMPLATE, CLOZE_EXPLANATION_TEMPLATE, ERROR_IDENTIFICATION_JSON_SCHEMA,ESSAY_COMBINE_SENTENCES_THPT_JSON_SCHEMA,ESSAY_SENTENCE_REWRITING_THPT_JSON_SCHEMA,
                   ESSAY_WORD_FORM_SENTENCE_COMPLETION_JSON_SCHEMA,ESSAY_WORD_ORDERING_THPT_JSON_SCHEMA,ESSAY_WORD_PROMPT_SENTENCE_COMPLETION_THPT_JSON_SCHEMA,SILENT_PHASE_EXPLANATION_TEMPLATE,READING_COMPREHENSION_EXPLANATION_TEMPLATE,WORD_REORDERING_JSON_SCHEMA, ARRANGE_JSON_SCHEMA,CLOZE_JSON_SCHEMA, CLOZE_WITH_TITLE_JSON_SCHEMA, DIALOGUE_COMPLETION_JSON_SCHEMA, LOGICAL_THINKING_JSON_SCHEMA, PRONUNCIATION_STRESS_JSON_SCHEMA, SYNONYM_ANTONYM_JSON_SCHEMA, WORD_FORM_SENTENCE_COMPLETION_THPT_JSON_SCHEMA)
from server.src.services.english_generator_service.english_generator_service import _safe_parse_json, limited_generate, load_prompt, safe_str
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
    response = await limited_generate(client_31, client_25, ai_input)

    parsed = _safe_parse_json(response)
    print(f">>>>> debug parsed {parsed}")
    return parsed







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


HANDLERS = {
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

