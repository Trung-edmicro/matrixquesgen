"""
API routes for regenerating questions
"""
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.core.genai_client import GenAIClient
from services.generators.question_generator import QuestionGenerator
from services.core.matrix_parser import QuestionSpec, TrueFalseQuestionSpec
from services.generators.image_description_service import ImageDescriptionService
from services.core.image_generation import ImageGenerator
from services.core.session_history import SessionGenerationHistory
from datetime import datetime
from config.settings import Config


router = APIRouter(prefix="/api/regenerate", tags=["Regenerate"])


def _get_app_dir() -> Path:
    """Get APP_DIR with lazy loading to ensure env var is set"""
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    # Fallback for dev mode (same as generate.py - 4 levels up to server/)
    return Path(__file__).parent.parent.parent.parent


def _get_project_root() -> Path:
    """Get project root directory (for matrix and prompts in dev mode)"""
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    # Fallback for dev mode (5 levels up to project root)
    return Path(__file__).parent.parent.parent.parent.parent


def _get_sessions_dir() -> Path:
    """Get sessions directory path"""
    return _get_app_dir() / "data" / "sessions"


def _get_questions_dir() -> Path:
    """Get questions directory path"""
    return _get_app_dir() / "data" / "questions"


class RegenerateQuestionRequest(BaseModel):
    """Request body để sinh lại câu hỏi"""
    session_id: str
    question_type: str  # TN, DS, TLN, TL
    question_code: str  # C1, C2, ...


class RegenerateBulkRequest(BaseModel):
    """Request body để sinh lại nhiều câu hỏi"""
    session_id: str
    questions: List[dict]  # [{"type": "TN", "code": "C1"}, ...]


def _load_session_data(session_id: str) -> dict:
    """Load session data from file"""
    # Try questions file first
    questions_dir = _get_questions_dir()
    questions_file = questions_dir / f"questions_{session_id}.json"
    if questions_file.exists():
        with open(questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback to session file
    sessions_dir = _get_sessions_dir()
    session_file = sessions_dir / f"{session_id}.json"
    if not session_file.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} không tồn tại")
    
    with open(session_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_session_data(session_id: str, data: dict):
    """Save session data back to file"""
    # Save to questions file if it exists
    questions_dir = _get_questions_dir()
    questions_file = questions_dir / f"questions_{session_id}.json"
    if questions_file.exists():
        try:
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return
        except TypeError as e:
            print(f"❌ JSON serialization error: {e}")
            print(f"   Trying to serialize data with keys: {list(data.keys())}")
            raise
    
    # Otherwise save to session file
    sessions_dir = _get_sessions_dir()
    session_file = sessions_dir / f"{session_id}.json"
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except TypeError as e:
        print(f"❌ JSON serialization error: {e}")
        print(f"   Trying to serialize data with keys: {list(data.keys())}")
        raise


def _get_prompts_dir(subject: str, curriculum: str, grade: str) -> Path:
    """Lấy thư mục prompts theo môn_curriculum_lớp"""
    # Use project root for prompts (in dev mode: project_root/data/prompts)
    workspace_root = _get_project_root()
    prompts_base_dir = workspace_root / "data" / "prompts"
    prompts_subdir = f"{subject}_{curriculum}_{grade}"
    prompts_dir = prompts_base_dir / prompts_subdir
    
    if not prompts_dir.exists():
        print(f"⚠️ Prompts directory not found: {prompts_dir}, using base dir")
        prompts_dir = prompts_base_dir
    
    return prompts_dir


def _get_question_generator(question_type: str, metadata: dict) -> QuestionGenerator:
    """Khởi tạo QuestionGenerator instance với prompt phù hợp"""
    # Read model from env at call time (not Config class attr which is set at import time)
    genai_model = os.getenv("VERTEX_AI_MODEL") or Config.VERTEX_AI_MODEL
    fallback_model = os.getenv("VERTEX_AI_FALLBACK_MODEL") or Config.VERTEX_AI_FALLBACK_MODEL
    gcp_location = os.getenv("GCP_LOCATION") or Config.GCP_LOCATION
    
    ai_client = GenAIClient(
        project_id=os.getenv("GCP_PROJECT_ID") or Config.GCP_PROJECT_ID,
        location=gcp_location,
        credentials_path=os.getenv("GCP_CREDENTIALS_PATH") or Config.GCP_CREDENTIALS_PATH
    )
    # Set model name sau khi khởi tạo
    ai_client.model_name = genai_model
    
    # Lấy thông tin môn học từ metadata
    subject = metadata.get('subject', '')
    curriculum = metadata.get('curriculum', 'KNTT')
    grade = metadata.get('grade', '')
    
    # Tìm prompts directory
    prompts_dir = _get_prompts_dir(subject, curriculum, grade)
    
    # Tìm prompt template theo loại câu hỏi
    prompt_path = None
    if question_type == 'TN':
        # Ưu tiên TN2.txt
        if (prompts_dir / "TN2.txt").exists():
            prompt_path = str(prompts_dir / "TN2.txt")
        elif (prompts_dir / "TN.txt").exists():
            prompt_path = str(prompts_dir / "TN.txt")
    elif question_type == 'DS':
        if (prompts_dir / "DS.txt").exists():
            prompt_path = str(prompts_dir / "DS.txt")
    elif question_type == 'TLN':
        if (prompts_dir / "TLN.txt").exists():
            prompt_path = str(prompts_dir / "TLN.txt")
    elif question_type == 'TL':
        if (prompts_dir / "TL.txt").exists():
            prompt_path = str(prompts_dir / "TL.txt")
    
    # Fallback nếu không tìm thấy
    if not prompt_path:
        # Tạo dummy prompt file
        prompts_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = str(prompts_dir / f"{question_type}.txt")
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(f"# Placeholder prompt template for {question_type}")
    
    generator = QuestionGenerator(
        ai_client=ai_client,
        prompt_template_path=prompt_path,
        verbose=True
    )
    
    # Set fallback_model sau khi khởi tạo
    generator.fallback_model = fallback_model
    
    return generator


def _build_history_for_regenerate(
        question_type: str,
        lesson_name: str,
        all_questions_of_type: list,
        exclude_code: str) -> str:
    """
    Build history context from questions already in the session for the same
    (lesson_name, question_type), excluding the question being regenerated.
    Used to tell the AI which questions already exist so it creates something different.
    """
    same_lesson_others = [
        q for q in all_questions_of_type
        if q.get('lesson_name') == lesson_name
        and q.get('question_code') != exclude_code
    ]
    return SessionGenerationHistory.build_context_from_question_dicts(
        question_type, same_lesson_others
    )


def _load_enriched_matrix(subject: str, curriculum: str, grade: str) -> dict:
    """Load enriched matrix file"""
    # Use project root for matrix (in dev mode: project_root/data/matrix)
    workspace_root = _get_project_root()
    matrix_dir = workspace_root / "data" / "matrix"
    matrix_file = matrix_dir / f"enriched_matrix_{subject}_{curriculum}_{grade}.json"
    
    if not matrix_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy file enriched_matrix: {matrix_file.name}"
        )
    
    with open(matrix_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def _find_question_spec_in_matrix(enriched_matrix: dict, question_code: str, question_type: str, lesson_name: str) -> tuple:
    """
    Tìm spec của câu hỏi trong enriched_matrix
    Returns: (lesson_data, question_spec_list, content)
    """
    # Duyet qua cac lesson de tim ma cau hoi
    for lesson in enriched_matrix.get('lessons', []):
            # Lấy content của lesson
            content = lesson.get('content', '')
            
            # Lấy danh sách spec theo question_type và level
            question_specs = None
            if question_type == 'TN':
                # TN có NB, TH, VD
                for level in ['NB', 'TH', 'VD']:
                    specs = lesson.get('TN', {}).get(level, [])
                    for spec in specs:
                        if question_code in spec.get('code', []):
                            return lesson, spec, content, level
            elif question_type == 'DS':
                # DS là list trực tiếp, không phân level như TN/TLN/TL
                ds_specs = lesson.get('DS', [])
                for spec in ds_specs:
                    if question_code == spec.get('question_code', ''):
                        # DS không có level trong enriched_matrix, lấy từ old_question
                        return lesson, spec, content, 'NB'  # Default level
            elif question_type == 'TLN':
                # TLN có NB, TH, VD
                for level in ['NB', 'TH', 'VD']:
                    specs = lesson.get('TLN', {}).get(level, [])
                    for spec in specs:
                        if question_code in spec.get('code', []):
                            return lesson, spec, content, level
            elif question_type == 'TL':
                # TL có NB, TH, VD
                for level in ['NB', 'TH', 'VD']:
                    specs = lesson.get('TL', {}).get(level, [])
                    for spec in specs:
                        if question_code in spec.get('code', []):
                            return lesson, spec, content, level
    
    raise HTTPException(
        status_code=404,
        detail=f"Không tìm thấy spec cho câu {question_code} trong enriched_matrix"
    )


def _build_question_spec_from_matrix(spec_data: dict, lesson_data: dict, question_code: str, level: str, question_type: str) -> QuestionSpec:
    """Tạo QuestionSpec từ enriched_matrix"""
    # Lấy rich_content_types nếu có
    rich_content_types_dict = spec_data.get('rich_content_types', {})
    rich_content_types = rich_content_types_dict.get(question_code, []) if rich_content_types_dict else []
    
    return QuestionSpec(
        lesson_name=lesson_data.get('lesson_name', ''),
        competency_level=1,
        cognitive_level=level,
        question_type=question_type,
        num_questions=1,
        question_codes=[question_code],
        learning_outcome=spec_data.get('learning_outcome', ''),
        row_index=0,
        chapter_number=lesson_data.get('chapter_number'),
        supplementary_material=lesson_data.get('supplementary_material', ''),
        rich_content_types={question_code: rich_content_types} if rich_content_types else None
    )


def _build_ds_spec_from_matrix(spec_data: dict, lesson_data: dict, question_code: str, old_question: dict) -> TrueFalseQuestionSpec:
    """Tạo TrueFalseQuestionSpec từ enriched_matrix"""
    from services.core.matrix_parser import StatementSpec
    
    # Lấy statements từ câu hỏi cũ để biết có bao nhiêu statement và level của chúng
    statements_dict = old_question.get('statements', {})
    statements = []
    
    for key, stmt in statements_dict.items():
        statements.append(StatementSpec(
            statement_code=f"{question_code}{key.upper()}",
            label=key,
            cognitive_level=stmt.get('level', 'NB'),
            learning_outcome=spec_data.get('learning_outcome', ''),
            competency_level=1
        ))
    
    # Lấy rich_content_types nếu có
    rich_content_types_dict = spec_data.get('rich_content_types', {})
    rich_content_types = rich_content_types_dict.get(question_code, []) if rich_content_types_dict else []
    
    return TrueFalseQuestionSpec(
        question_code=question_code,
        lesson_name=lesson_data.get('lesson_name', ''),
        statements=statements,
        question_type='DS',
        chapter_number=lesson_data.get('chapter_number'),
        supplementary_material=lesson_data.get('supplementary_material', ''),
        materials=spec_data.get('materials', ''),
        rich_content_types={question_code: rich_content_types} if rich_content_types else None
    )


def _generate_image_for_question(
    question_code: str,
    rich_content_types: List[str],
    metadata: dict,
    lesson_data: dict,
    spec_data: dict,
    content: str
) -> Optional[dict]:
    """
    Sinh ảnh cho câu hỏi nếu rich_content_types chứa HA_MH hoặc HA_TL
    
    Args:
        question_code: Mã câu hỏi
        rich_content_types: List các loại rich content (e.g., ['HA_MH'], ['HA_TL'])
        metadata: Metadata từ session (subject, grade, curriculum)
        lesson_data: Data của lesson từ enriched_matrix
        spec_data: Spec data từ enriched_matrix
        content: Nội dung SGK
    
    Returns:
        dict: Rich content dict để merge vào question_stem, hoặc None nếu không cần ảnh
    """
    # Kiểm tra xem có cần sinh ảnh không
    # rich_content_types có thể là list of string ['HA_TL'] hoặc list of dict [{'code': 'HA_TL', ...}]
    image_type = None
    
    for item in rich_content_types:
        if isinstance(item, dict):
            # Format: {'code': 'HA_TL', 'name': '...', 'description': '...'}
            code = item.get('code', '')
        else:
            # Format: 'HA_TL'
            code = item
        
        if code in ['HA_MH', 'HA_TL']:
            image_type = code
            break
    
    if not image_type:
        return None
    
    print(f"🖼️ Generating {image_type} image for question {question_code}...")
    
    try:
        # Khởi tạo AI client
        genai_model = Config.VERTEX_AI_MODEL
        ai_client = GenAIClient(
            project_id=Config.GCP_PROJECT_ID,
            location=Config.GCP_LOCATION,
            credentials_path=Config.GCP_CREDENTIALS_PATH
        )
        ai_client.model_name = genai_model
        
        # Khởi tạo ImageDescriptionService (dùng default prompts_dir: server/src/services/prompts)
        description_service = ImageDescriptionService(
            ai_client=ai_client
            # Không truyền prompts_dir để dùng default: server/src/services/prompts/
            # (image description prompts khác với question generation prompts)
        )
        
        # Sinh mô tả hình ảnh
        print(f"  ➡️ Generating image description...")
        print(f"     Subject: {metadata.get('subject', '')}")
        print(f"     Grade: {metadata.get('grade', '')}")
        print(f"     Chapter: {lesson_data.get('chapter', '')}")
        print(f"     Lesson: {lesson_data.get('lesson_name', '')}")
        print(f"     Content length: {len(content)} chars")
        print(f"     Learning outcome: {spec_data.get('learning_outcome', '')[:100]}...")
        
        if image_type == 'HA_MH':
            desc_result = description_service.generate_illustrative_description(
                subject=metadata.get('subject', ''),
                class_level=metadata.get('grade', ''),
                chapter=lesson_data.get('chapter', ''),
                lesson_name=lesson_data.get('lesson_name', ''),
                content=content,
                learning_outcome=spec_data.get('learning_outcome', '')
            )
        else:  # HA_TL
            desc_result = description_service.generate_data_source_description(
                subject=metadata.get('subject', ''),
                class_level=metadata.get('grade', ''),
                chapter=lesson_data.get('chapter', ''),
                lesson_name=lesson_data.get('lesson_name', ''),
                content=content,
                learning_outcome=spec_data.get('learning_outcome', '')
            )
        
        print(f"  ✓ Description: {desc_result.description[:100]}...")
        
        # Sinh hình ảnh từ mô tả
        print(f"  ➡️ Generating image from description...")
        image_generator = ImageGenerator(num_images=1, aspect_ratio="16:9")
        images_data = image_generator.generate(
            prompt=desc_result.description,
            num_images=1
        )
        
        if not images_data:
            print(f"  ❌ Failed to generate image")
            return None
        
        # Lưu hình ảnh - use same path logic as images.py
        app_dir = _get_app_dir()
        images_dir = app_dir / "data" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{question_code}_{image_type}_{timestamp}.png"
        image_path = images_dir / filename
        
        with open(image_path, 'wb') as f:
            f.write(images_data[0])
        
        print(f"  ✓ Image saved to: {image_path}")
        
        # Convert absolute path to API URL path for frontend
        image_filename = image_path.name
        api_image_url = f"/api/images/file/{image_filename}"
        print(f"  ✓ API URL: {api_image_url}")
        
        # Tạo rich content dict
        return {
            "type": "image",
            "content": api_image_url,  # Use API URL instead of absolute path
            "metadata": {
                "image_type": image_type,
                "description": desc_result.description,
                "caption": f"Hình ảnh minh họa {question_code}",
                "local_path": str(image_path)  # Keep absolute path for server reference
            }
        }
        
    except Exception as e:
        print(f"  ❌ Error generating image: {e}")
        import traceback
        traceback.print_exc()
        return None


@router.post("/question")
async def regenerate_single_question(request: RegenerateQuestionRequest):
    """
    Sinh lại một câu hỏi cụ thể
    
    - **session_id**: ID của session
    - **question_type**: Loại câu hỏi (TN, DS, TLN, TL)
    - **question_code**: Mã câu hỏi (C1, C2, ...)
    """
    try:
        # Load session data
        data = _load_session_data(request.session_id)
        questions = data.get('questions', {})
        metadata = data.get('metadata', {})
        
        # Find the question
        question_list = questions.get(request.question_type, [])
        question_idx = None
        old_question = None
        
        for idx, q in enumerate(question_list):
            if q.get('question_code') == request.question_code:
                question_idx = idx
                old_question = q
                break
        
        if old_question is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Không tìm thấy câu hỏi {request.question_type} - {request.question_code}"
            )
        
        # Load enriched_matrix để lấy spec gốc
        enriched_matrix = _load_enriched_matrix(
            metadata.get('subject', ''),
            metadata.get('curriculum', ''),
            metadata.get('grade', '')
        )
        
        # Tìm spec trong enriched_matrix
        lesson_data, spec_data, content, level = _find_question_spec_in_matrix(
            enriched_matrix,
            request.question_code,
            request.question_type,
            old_question.get('lesson_name', '')
        )
        
        # Initialize question generator với prompt phù hợp
        generator = _get_question_generator(request.question_type, metadata)
        
        # Build history context: questions of same (lesson, type) already in the session
        _history_ctx = _build_history_for_regenerate(
            request.question_type,
            old_question.get('lesson_name', ''),
            question_list,
            request.question_code
        )
        if _history_ctx:
            print(f"📚 History context: {len([x for x in question_list if x.get('lesson_name') == old_question.get('lesson_name') and x.get('question_code') != request.question_code])} existing questions injected")

        # Lấy question_template từ spec_data
        question_template = spec_data.get('question_template', '')
        # Nếu là list, join thành string hoặc lấy phần tử đầu tiên
        if isinstance(question_template, list):
            question_template = '\n'.join(question_template) if question_template else ''
        
        # Generate new question based on type - sử dụng content từ enriched_matrix
        print(f"🤖 Calling AI to generate {request.question_type} question {request.question_code}...")
        
        if request.question_type == 'DS':
            spec = _build_ds_spec_from_matrix(spec_data, lesson_data, request.question_code, old_question)
            
            # Lấy prompts directory từ metadata
            prompts_dir = _get_prompts_dir(
                metadata.get('subject', ''),
                metadata.get('curriculum', ''),
                metadata.get('grade', '')
            )
            ds_prompt_path = str(prompts_dir / "DS.txt")
            
            new_questions = generator.generate_true_false_question(
                tf_spec=spec,
                prompt_template_path=ds_prompt_path,
                question_template=question_template,
                content=content,  # Sử dụng content từ enriched_matrix
                history_context=_history_ctx
            )
            # Convert to dict
            new_question_dict = {
                'question_code': new_questions.question_code,
                'question_type': new_questions.question_type,
                'lesson_name': new_questions.lesson_name,
                'source_text': new_questions.source_text,
                'statements': new_questions.statements,
                'explanation': new_questions.explanation,
                'source_citation': getattr(new_questions, 'source_citation', None),
                'source_origin': getattr(new_questions, 'source_origin', None),
                'source_type': getattr(new_questions, 'source_type', None),
            }
        elif request.question_type == 'TLN':
            spec = _build_question_spec_from_matrix(spec_data, lesson_data, request.question_code, level, 'TLN')
            
            # Lấy prompts directory từ metadata
            prompts_dir = _get_prompts_dir(
                metadata.get('subject', ''),
                metadata.get('curriculum', ''),
                metadata.get('grade', '')
            )
            tln_prompt_path = str(prompts_dir / "TLN.txt")
            
            new_questions = generator.generate_tln_questions(
                spec=spec,
                prompt_template_path=tln_prompt_path,
                question_template=question_template,
                content=content,  # Sử dụng content từ enriched_matrix
                history_context=_history_ctx
            )
            if not new_questions:
                raise HTTPException(status_code=500, detail="Không thể sinh câu hỏi mới")
            new_q = new_questions[0]
            new_question_dict = {
                'question_code': new_q.question_code,
                'question_type': new_q.question_type,
                'lesson_name': new_q.lesson_name,
                'level': new_q.level,
                'question_stem': new_q.question_stem,
                'correct_answer': new_q.correct_answer,
                'explanation': new_q.explanation,
            }
        elif request.question_type == 'TL':
            spec = _build_question_spec_from_matrix(spec_data, lesson_data, request.question_code, level, 'TL')
            
            # Lấy prompts directory từ metadata
            prompts_dir = _get_prompts_dir(
                metadata.get('subject', ''),
                metadata.get('curriculum', ''),
                metadata.get('grade', '')
            )
            tl_prompt_path = str(prompts_dir / "TL.txt")
            
            new_questions = generator.generate_tl_questions(
                spec=spec,
                prompt_template_path=tl_prompt_path,
                question_template=question_template,
                content=content,  # Sử dụng content từ enriched_matrix
                history_context=_history_ctx
            )
            if not new_questions:
                raise HTTPException(status_code=500, detail="Không thể sinh câu hỏi mới")
            new_q = new_questions[0]
            new_question_dict = {
                'question_code': new_q.question_code,
                'question_type': new_q.question_type,
                'lesson_name': new_q.lesson_name,
                'level': new_q.level,
                'question_stem': new_q.question_stem,
                'correct_answer': new_q.correct_answer,
                'explanation': new_q.explanation,
            }
        else:  # TN
            spec = _build_question_spec_from_matrix(spec_data, lesson_data, request.question_code, level, 'TN')
            
            print(f"🔍 TN spec details: codes={spec.question_codes}, rich_content={spec.rich_content_types}")
            
            # Lấy prompts directory từ metadata
            prompts_dir = _get_prompts_dir(
                metadata.get('subject', ''),
                metadata.get('curriculum', ''),
                metadata.get('grade', '')
            )
            # Ưu tiên TN2.txt, fallback TN.txt
            if (prompts_dir / "TN2.txt").exists():
                tn_prompt_path = str(prompts_dir / "TN2.txt")
            else:
                tn_prompt_path = str(prompts_dir / "TN.txt")
            
            new_questions = generator.generate_questions_for_spec(
                spec=spec,
                prompt_template_path=tn_prompt_path,
                question_template=question_template,
                content=content,  # Sử dụng content từ enriched_matrix
                history_context=_history_ctx
            )
            
            print(f"✅ AI returned {len(new_questions) if new_questions else 0} questions")
            
            if not new_questions:
                raise HTTPException(status_code=500, detail="Không thể sinh câu hỏi mới")
            new_q = new_questions[0]
            
            # Serialize câu hỏi với full rich content support
            print(f"✅ AI generated TN question successfully")
            new_question_dict = {
                'question_code': new_q.question_code,
                'question_type': new_q.question_type,
                'lesson_name': new_q.lesson_name,
                'level': new_q.level,
                'question_stem': new_q.question_stem,  # Có thể là text hoặc rich content dict
                'options': new_q.options,
                'correct_answer': new_q.correct_answer,
                'explanation': new_q.explanation,
            }
            
            # Thêm rich_content_types nếu có từ spec
            if hasattr(spec, 'rich_content_types') and spec.rich_content_types:
                new_question_dict['rich_content_types'] = spec.rich_content_types
        
        # Preserve some fields from old question
        if 'content' in old_question:
            new_question_dict['content'] = old_question['content']
        if 'chapter_number' in old_question:
            new_question_dict['chapter_number'] = old_question['chapter_number']
        if 'lesson_number' in old_question:
            new_question_dict['lesson_number'] = old_question['lesson_number']
        
        # 🖼️ Generate image if needed (HA_MH or HA_TL)
        rich_content_types_dict = spec_data.get('rich_content_types', {})
        rich_content_types = rich_content_types_dict.get(request.question_code, []) if rich_content_types_dict else []
        
        if rich_content_types:
            print(f"🎨 Question has rich content types: {rich_content_types}")
            try:
                image_rich_content = _generate_image_for_question(
                    question_code=request.question_code,
                    rich_content_types=rich_content_types,
                    metadata=metadata,
                    lesson_data=lesson_data,
                    spec_data=spec_data,
                    content=content
                )
            except Exception as img_error:
                print(f"⚠️ Error generating image (will continue without image): {img_error}")
                import traceback
                traceback.print_exc()
                image_rich_content = None
            
            if image_rich_content:
                # Merge image into appropriate field based on question type
                if request.question_type == 'DS':
                    # DS questions use source_text
                    current_text = new_question_dict.get('source_text', '')
                    field_name = 'source_text'
                else:
                    # TN/TL/TLN questions use question_stem
                    current_text = new_question_dict.get('question_stem', '')
                    field_name = 'question_stem'
                
                print(f"  🔄 Merging image into {field_name}...")
                
                # Replace [IMAGE_PLACEHOLDER] if exists
                if isinstance(current_text, dict):
                    text_content = current_text.get('content', [])
                    if isinstance(text_content, list):
                        # Replace placeholder in list
                        new_content = []
                        placeholder_replaced = False
                        for item in text_content:
                            if isinstance(item, str) and '[IMAGE_PLACEHOLDER]' in item:
                                # Replace placeholder with image
                                new_content.append(image_rich_content)
                                placeholder_replaced = True
                            else:
                                new_content.append(item)
                        
                        if not placeholder_replaced:
                            # No placeholder found, append image
                            new_content.append(image_rich_content)
                        
                        current_text['content'] = new_content
                        new_question_dict[field_name] = current_text
                    else:
                        # Content is not list - convert to mixed content
                        new_question_dict[field_name] = {
                            "type": "mixed",
                            "content": [text_content, image_rich_content]
                        }
                elif isinstance(current_text, str):
                    # Simple text - check for placeholder
                    if '[IMAGE_PLACEHOLDER]' in current_text:
                        # Split and inject image
                        parts = current_text.split('[IMAGE_PLACEHOLDER]')
                        new_question_dict[field_name] = {
                            "type": "mixed",
                            "content": [
                                parts[0].strip() if parts[0].strip() else None,
                                image_rich_content,
                                parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
                            ]
                        }
                        # Remove None entries
                        new_question_dict[field_name]['content'] = [
                            c for c in new_question_dict[field_name]['content'] if c is not None
                        ]
                    else:
                        # No placeholder - append image
                        new_question_dict[field_name] = {
                            "type": "mixed",
                            "content": [current_text, image_rich_content]
                        }
                
                print(f"  ✓ Image merged into {field_name}")
        
        # Replace old question with new one
        question_list[question_idx] = new_question_dict
        
        # Save back to both questions file and session file
        try:
            print(f"💾 Saving regenerated question {request.question_code} to session {request.session_id}...")
            _save_session_data(request.session_id, data)
            print(f"✅ Saved successfully")
        except Exception as save_error:
            print(f"❌ Error saving data: {save_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Lỗi khi lưu câu hỏi: {str(save_error)}")
        
        return {
            "success": True,
            "message": f"Đã sinh lại câu {request.question_code}",
            "question": new_question_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error regenerating question: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh lại câu hỏi: {str(e)}")


@router.post("/bulk")
async def regenerate_bulk_questions(request: RegenerateBulkRequest):
    """
    Sinh lại nhiều câu hỏi cùng lúc với parallel execution
    
    - **session_id**: ID của session
    - **questions**: Danh sách câu hỏi cần sinh lại [{"type": "TN", "code": "C1"}, ...]
    """
    try:
        print(f"🔄 Bulk regenerate: {len(request.questions)} questions (group-serial by lesson+type)")
        results = []
        errors = []

        # Load session once to determine lesson groupings
        session_data = _load_session_data(request.session_id)
        questions_map = {q.get('question_code'): q for q in session_data.get('questions', [])}

        # Group by (question_type, lesson_name) so same-lesson questions run serially
        from collections import defaultdict
        lesson_groups: dict = defaultdict(list)
        for q in request.questions:
            q_session = questions_map.get(q.get('code'), {})
            lesson_name = q_session.get('lesson_name', '')
            group_key = (q.get('type', ''), lesson_name)
            lesson_groups[group_key].append(q)

        print(f"  ↳ {len(lesson_groups)} lesson-type groups formed")

        # Helper: regenerate one question synchronously (own event loop per thread)
        def regenerate_sync(q: dict):
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                single_request = RegenerateQuestionRequest(
                    session_id=request.session_id,
                    question_type=q.get('type'),
                    question_code=q.get('code')
                )
                result = loop.run_until_complete(regenerate_single_question(single_request))
                return {
                    "type": q.get('type'),
                    "code": q.get('code'),
                    "status": "success",
                    "question": result.get('question')
                }
            except Exception as e:
                return {
                    "type": q.get('type'),
                    "code": q.get('code'),
                    "status": "error",
                    "error": str(e)
                }
            finally:
                if loop:
                    try:
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass
                    finally:
                        loop.close()

        # Run each group serially (history accumulates via save/reload); groups run in parallel
        def run_group(group_key, group_questions: list):
            group_results = []
            for q in group_questions:
                result = regenerate_sync(q)
                group_results.append(result)
                if result['status'] == 'success':
                    print(f"✅ Completed {result['type']} {result['code']}")
                else:
                    print(f"❌ Failed {result['type']} {result['code']}: {result.get('error')}")
            return group_results

        max_workers = min(5, len(lesson_groups))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_group = {
                executor.submit(run_group, gk, gqs): gk
                for gk, gqs in lesson_groups.items()
            }
            for future in as_completed(future_to_group):
                gk = future_to_group[future]
                try:
                    group_results = future.result()
                    for result in group_results:
                        if result['status'] == 'success':
                            results.append(result)
                        else:
                            errors.append(result)
                except Exception as e:
                    print(f"❌ Group {gk} exception: {e}")
                    errors.append({"type": str(gk[0]), "code": "", "status": "error", "error": str(e)})
        
        return {
            "success": len(errors) == 0,
            "message": f"Đã sinh lại {len(results)} câu hỏi",
            "total": len(request.questions),
            "succeeded": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        print(f"Error regenerating bulk questions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh lại câu hỏi: {str(e)}")


class EditQuestionRequest(BaseModel):
    session_id: str
    question_type: str
    question_code: str
    comment: str

@router.post("/edit")
async def edit_single_question(request: EditQuestionRequest):
    """
    Sửa lại một câu hỏi cụ thể dựa theo comment
    """
    try:
        # Load session data
        data = _load_session_data(request.session_id)
        questions = data.get('questions', {})
        metadata = data.get('metadata', {})

        # Find the question
        question_list = questions.get(request.question_type, [])
        question_idx = None
        old_question = None

        for idx, q in enumerate(question_list):
            if q.get('question_code') == request.question_code:
                question_idx = idx
                old_question = q
                break

        if old_question is None:
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy câu hỏi {request.question_type} - {request.question_code}"
            )

        # Load enriched_matrix để lấy spec gốc
        enriched_matrix = _load_enriched_matrix(
            metadata.get('subject', ''),
            metadata.get('curriculum', ''),
            metadata.get('grade', '')
        )

        # Tìm spec trong enriched_matrix
        lesson_data, spec_data, content, level = _find_question_spec_in_matrix(
            enriched_matrix,
            request.question_code,
            request.question_type,
            old_question.get('lesson_name', '')
        )
        
        # Load prompt template
        # Path(__file__) = server/src/api/routes/regenerate.py
        # .parent = server/src/api/routes/
        # .parent.parent = server/src/api/
        # .parent.parent.parent = server/src/
        prompt_path = Path(__file__).parent.parent.parent / "services" / "prompts" / "edit_question" / "edit_question_prompt.md"
        if not prompt_path.exists():
            print(f"⚠️ Edit prompt not found at {prompt_path}, checking alternative paths...")
            # Fallback: try from app_dir
            alt_path = _get_app_dir() / "server" / "src" / "services" / "prompts" / "edit_question" / "edit_question_prompt.md"
            if alt_path.exists():
                prompt_path = alt_path
            else:
                raise FileNotFoundError(f"Edit question prompt not found at {prompt_path} or {alt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f_prompt:
            prompt_template = f_prompt.read()

        # Ánh xạ biến
        current_question_str = json.dumps(old_question, ensure_ascii=False, indent=2)
        expected_learning_outcome = spec_data.get('expected_learning_outcome', '') or spec_data.get('yccc', '') or spec_data.get('YCCC', '')
        
        # Determine SUPPLEMENTARY_MATERIAL if it's DS or has materials
        supp_mat = ""
        if request.question_type == 'DS' and lesson_data.get('materials'):
            supp_mat = json.dumps(lesson_data.get('materials'), ensure_ascii=False)
            
        prompt = prompt_template.replace('{{CURRENT_QUESTION}}', current_question_str)
        prompt = prompt.replace('{{COGNITIVE_LEVEL}}', str(level))
        prompt = prompt.replace('{{EXPECTED_LEARNING_OUTCOME}}', str(expected_learning_outcome))
        prompt = prompt.replace('{{CONTENT}}', str(content))
        prompt = prompt.replace('{{USER_COMMENT}}', str(request.comment))
        prompt = prompt.replace('{{SUPPLEMENTARY_MATERIAL}}', str(supp_mat))
        
        print(f"🤖 Calling AI to edit {request.question_type} question {request.question_code}...")
        
        genai_model = os.getenv("VERTEX_AI_MODEL") or Config.VERTEX_AI_MODEL
        gcp_location = os.getenv("GCP_LOCATION") or Config.GCP_LOCATION
        
        client = GenAIClient(
            project_id=os.getenv("GCP_PROJECT_ID") or Config.GCP_PROJECT_ID,
            location=gcp_location,
            credentials_path=os.getenv("GCP_CREDENTIALS_PATH") or Config.GCP_CREDENTIALS_PATH
        )
        # Set model name sau khi khởi tạo
        client.model_name = genai_model
        
        response = client.generate_content(prompt)
        response_text = response if isinstance(response, str) else response.text
        
        # Extract JSON
        import re
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        try:
            new_question_dict = json.loads(response_text)
        except:
             # try to find first { and last }
             start = response_text.find('{')
             end = response_text.rfind('}') + 1
             new_question_dict = json.loads(response_text[start:end])
        
        # Ensure question code and type stay the same
        new_question_dict['question_code'] = request.question_code
        new_question_dict['question_type'] = request.question_type
        new_question_dict['lesson_name'] = old_question.get('lesson_name', '')
        
        # Update question list
        question_list[question_idx] = new_question_dict
        
        # Save session
        _save_session_data(request.session_id, data)
        
        print(f"✅ Edited {request.question_type} question {request.question_code} successfully")
        
        return {
            "success": True,
            "message": f"Đã sửa thành công câu {request.question_code}",
            "question": new_question_dict,
            "type": request.question_type
        }
    except Exception as e:
        print(f"❌ Lỗi khi sửa câu hỏi: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
