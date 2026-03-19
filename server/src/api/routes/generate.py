import os
import json
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import traceback
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.schemas import GenerateQuestionsRequest, GenerateResponse
from services.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig
from services.core.genai_client import GenAIClient
from services.core.matrix_parser import MatrixParser
from services.generators.question_generator import QuestionGenerator
from services.exporters.template_generator import QuestionGeneratorWithTemplate
from services.english_generator_service.english_generator_service import generate_english_flow
from services.hsk_generator_service.hsk_generator import generate_hsk_flow

router = APIRouter(prefix="/api/generate", tags=["Generate"])


# Helper functions for lazy path loading (ensures APP_DIR env var is set)
def _get_app_dir() -> Path:
    """Get APP_DIR with lazy loading to ensure env var is set"""
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    # Fallback for dev mode
    return Path(__file__).parent.parent.parent.parent


def _get_sessions_dir() -> Path:
    """Get sessions directory path with lazy loading"""
    sessions_dir = _get_app_dir() / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def _get_questions_dir() -> Path:
    """Get questions directory path with lazy loading"""
    questions_dir = _get_app_dir() / "data" / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)
    return questions_dir


def _get_uploads_dir() -> Path:
    """Get uploads directory path with lazy loading"""
    uploads_dir = _get_app_dir() / "data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


def generate_questions_task(
    session_id: str,
    matrix_file_path: str,
    config: dict,
    template_docx_path: Optional[str] = None
):
    """
    Background task để sinh câu hỏi theo 4 phase workflow
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    def update_session(data: dict):
        """Helper to update session file"""
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    try:
        # Khởi tạo session data
        session_data = {
            "session_id": session_id,
            "status": "processing",
            "matrix_file": Path(matrix_file_path).name,
            "generated_at": datetime.now().isoformat(),
            "progress": 0,
            "current_phase": "initializing"
        }
        update_session(session_data)
        
        # Progress callback: update session_data in-place so status: "processing"
        # is always preserved and the full dict is written to the session file.
        def _on_progress(phase, progress):
            session_data['current_phase'] = phase
            session_data['progress'] = progress
            update_session(session_data)

        # Use WorkflowOrchestrator for complete workflow
        orchestrator = WorkflowOrchestrator(config=WorkflowConfig(
            ai_provider="genai",
            question_types=["TN", "DS", "TLN", "TL"],
            max_concurrent_generations=config.get('max_workers', 5)
        ), progress_callback=_on_progress)
        
        # Execute complete workflow (Phase 2 will gracefully handle missing Google Drive)
        import logging as _logging
        _log = _logging.getLogger(__name__)
        _log.info(f"[{session_id}] Starting WorkflowOrchestrator")
        workflow_result = orchestrator.execute_complete_workflow(
            Path(matrix_file_path)
        )
        
        if not workflow_result.success:
            raise Exception(f"Failed: {', '.join(workflow_result.errors)}")
        
        # Extract data from workflow result
        matrix_metadata = workflow_result.matrix_metadata
        question_sets = workflow_result.question_sets
        
        # Convert metadata
        metadata = {
            "subject": matrix_metadata.subject,
            "grade": matrix_metadata.grade,
            "curriculum": matrix_metadata.curriculum,
            "filename": Path(matrix_file_path).name
        }
        
        # Count questions
        tn_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "TN")
        ds_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "DS")
        tln_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "TLN")
        tl_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "TL")
        
        # Progress will be updated to 100% when completed
        
        # ===== Finalize: Save Results =====
        print("💾 Saving generated questions...")
        # Progress already updated by WorkflowOrchestrator
        
        # Flatten questions from question_sets
        generated_tn = []
        generated_ds = []
        generated_tln = []
        generated_tl = []
        for qs in question_sets:
            for q in qs.questions:
                if q.type == "TN":
                    generated_tn.append(q)
                elif q.type == "DS":
                    generated_ds.append(q)
                elif q.type == "TLN":
                    generated_tln.append(q)
                elif q.type == "TL":
                    generated_tl.append(q)
        
        # Save final results to data/questions
        questions_file = _get_questions_dir() / f"questions_{session_id}.json"
        
        output_data = {
            "metadata": {
                "session_id": session_id,
                "subject": metadata["subject"],
                "grade": metadata["grade"],
                "curriculum": metadata["curriculum"],
                "matrix_file": Path(matrix_file_path).name,
                "total_questions": len(generated_tn) + len(generated_ds) + len(generated_tln) + len(generated_tl),
                "tn_count": len(generated_tn),
                "ds_count": len(generated_ds),
                "tln_count": len(generated_tln),
                "tl_count": len(generated_tl),
                "generated_at": datetime.now().isoformat(),
                "status": "completed"
            },
            "questions": {
                "TN": [
                    {
                        "question_code": q.id.split('_')[-1],  # Extract question code from ID
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tn
                ],
                "DS": [
                    {
                        "question_code": q.id.split('_')[-1],  # Extract question code from ID
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "source_text": q.source_text,
                        "statements": q.statements,
                        "explanation": {
                            "a": (q.explanation.get("a", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("a", "")),
                            "b": (q.explanation.get("b", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("b", "")),
                            "c": (q.explanation.get("c", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("c", "")),
                            "d": (q.explanation.get("d", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("d", ""))
                        }
                    }
                    for q in generated_ds
                ],
                "TLN": [
                    {
                        "question_code": q.id.split('_')[-1],  # Extract question code from ID
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tln
                ],
                "TL": [
                    {
                        "question_code": q.id.split('_')[-1],
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tl
                ]
            }
        }
        
        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Update final session status
        session_data.update({
            'current_phase': 'completed',
            'progress': 100,
            'status': 'completed',
            'total_questions': len(generated_tn) + len(generated_ds) + len(generated_tln) + len(generated_tl),
            'tn_count': len(generated_tn),
            'ds_count': len(generated_ds),
            'tln_count': len(generated_tln),
            'tl_count': len(generated_tl),
            'total_generated': len(generated_tn) + len(generated_ds) + len(generated_tln) + len(generated_tl),
            'tn_generated': len(generated_tn),
            'ds_generated': len(generated_ds),
            'tln_generated': len(generated_tln),
            'tl_generated': len(generated_tl),
            'results_file': str(questions_file.name)
        })
        update_session(session_data)
        
        print(f"✅ Workflow completed! Generated {len(generated_tn)} TN + {len(generated_ds)} DS + {len(generated_tln)} TLN + {len(generated_tl)} TL questions")
        
    except Exception as e:
        # Handle errors with detailed logging
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        import logging as _logging
        _logging.getLogger(__name__).error(
            f"[{session_id}] Workflow failed: {error_msg}\n{error_trace}"
        )
        
        # Save error to session
        error_data = {
            "session_id": session_id,
            "status": "failed",
            "error": error_msg,
            "error_trace": error_trace,
            "current_phase": session_data.get('current_phase', 'unknown'),
            "progress": session_data.get('progress', 0),
            "generated_at": datetime.now().isoformat(),
            "matrix_file": Path(matrix_file_path).name
        }
        
        update_session(error_data)


@router.post("", response_model=GenerateResponse)
async def generate_questions(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    template_docx: Optional[UploadFile] = File(None),
    max_workers: int = 10,
    min_interval: float = 0.3,
    max_retries: int = 3,
    retry_delay: float = 2.0
):
    """
    Upload file Excel ma trận và sinh câu hỏi theo 4 phase workflow
    
    - **file**: File Excel ma trận (.xlsx)
    - **template_docx**: (Optional) File DOCX đề mẫu để AI tham khảo
    - **max_workers**: Số threads xử lý song song (default: 10)
    - **min_interval**: Delay tối thiểu giữa requests (default: 0.3s)
    - **max_retries**: Số lần retry khi lỗi (default: 3)
    - **retry_delay**: Delay giữa các lần retry (default: 2.0s)
    """
    
    # Validate file extension
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .xlsx")
    
    if file.filename.startswith("MATRIX_ENGLISH_"):
        try:
            return await generate_english_flow(file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình xử lý: {str(e)}")
    elif file.filename.startswith("MATRIX_HSK_"):
        try:
            return await generate_hsk_flow(file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình xử lý: {str(e)}")
    
    # Tạo session ID
    session_id = str(uuid.uuid4())
    
    # Lưu file upload
    upload_dir = _get_uploads_dir()
    
    file_path = upload_dir / f"{session_id}_{file.filename}"
    
    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu file: {str(e)}")
    
    # Lưu template DOCX nếu có
    template_path = None
    if template_docx:
        if not template_docx.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Template phải là file .docx")
        
        template_path = upload_dir / f"{session_id}_template_{template_docx.filename}"
        try:
            with open(template_path, 'wb') as f:
                template_content = await template_docx.read()
                f.write(template_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Không thể lưu template: {str(e)}")
    
    # Đường dẫn tuyệt đối đến thư mục config
    project_root = _get_app_dir()
    
    # Cấu hình
    config = {
        'project_id': os.getenv("GCP_PROJECT_ID"),
        'location': os.getenv("GCP_LOCATION", "global"),
        'credentials_path': os.getenv("GCP_CREDENTIALS_PATH"),
        'prompt_template_tn': str(project_root / "config" / "prompt" / "TN.txt"),
        'prompt_template_ds': str(project_root / "config" / "prompt" / "DS.txt"),
        'max_workers': max_workers,
        'min_interval': min_interval,
        'max_retries': max_retries,
        'retry_delay': retry_delay,
        'verbose': False
    }
    
    # Thêm background task
    background_tasks.add_task(
        generate_questions_task,
        session_id,
        str(file_path),
        config,
        str(template_path) if template_path else None
    )
    
    return GenerateResponse(
        session_id=session_id,
        status="processing",
        message="Đã bắt đầu sinh câu hỏi. Vui lòng kiểm tra tiến độ qua session_id."
    )


@router.get("/{session_id}/progress")
async def get_generation_progress(session_id: str):
    """
    Lấy tiến độ sinh câu hỏi
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check nếu có metadata (completed), lấy từ đó
    if "metadata" in data:
        metadata = data["metadata"]
        return {
            "session_id": session_id,
            "status": metadata.get("status", "completed"),
            "progress": 100,
            "total_questions": metadata.get("total_questions", 0),
            "current_phase": "completed",
            "error": None
        }
    
    # Nếu chưa có metadata (đang processing), lấy từ root
    return {
        "session_id": session_id,
        "status": data.get("status", "unknown"),
        "progress": data.get("progress", 0),
        "total_questions": data.get("total_questions", 0),
        "current_phase": data.get("current_phase", ""),
        "error": data.get("error")
    }


@router.get("/{session_id}/result")
async def get_generation_result(session_id: str):
    """
    Lấy kết quả sinh câu hỏi đã hoàn thành
    
    Returns:
        - metadata: Thông tin về session
        - questions: Object chứa TN và DS questions đã sinh
    """
    questions_file = _get_questions_dir() / f"questions_{session_id}.json"
    
    if not questions_file.exists():
        # Check session status
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            status = session_data.get('status', 'unknown')
            if status == 'failed':
                raise HTTPException(
                    status_code=500, 
                    detail=f"Generation failed: {session_data.get('error', 'Unknown error')}"
                )
            elif status == 'processing':
                raise HTTPException(
                    status_code=202, 
                    detail="Generation still in progress. Check /progress endpoint."
                )
        
        raise HTTPException(
            status_code=404, 
            detail="Result not found. Session may not exist or generation not started."
        )
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data
import os
import json
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import traceback
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.schemas import GenerateQuestionsRequest, GenerateResponse
from services.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig
from services.core.genai_client import GenAIClient
from services.core.matrix_parser import MatrixParser
from services.generators.question_generator import QuestionGenerator
from services.exporters.template_generator import QuestionGeneratorWithTemplate
from services.english_generator_service.english_generator_service import generate_english_flow


router = APIRouter(prefix="/api/generate", tags=["Generate"])


# Helper functions for lazy path loading (ensures APP_DIR env var is set)
def _get_app_dir() -> Path:
    """Get APP_DIR with lazy loading to ensure env var is set"""
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    # Fallback for dev mode
    return Path(__file__).parent.parent.parent.parent


def _get_sessions_dir() -> Path:
    """Get sessions directory path with lazy loading"""
    sessions_dir = _get_app_dir() / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def _get_questions_dir() -> Path:
    """Get questions directory path with lazy loading"""
    questions_dir = _get_app_dir() / "data" / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)
    return questions_dir


def _get_uploads_dir() -> Path:
    """Get uploads directory path with lazy loading"""
    uploads_dir = _get_app_dir() / "data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


def generate_questions_task(
    session_id: str,
    matrix_file_path: str,
    config: dict,
    template_docx_path: Optional[str] = None
):
    """
    Background task để sinh câu hỏi theo 4 phase workflow
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    def update_session(data: dict):
        """Helper to update session file"""
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    try:
        # Khởi tạo session data
        session_data = {
            "session_id": session_id,
            "status": "processing",
            "matrix_file": Path(matrix_file_path).name,
            "generated_at": datetime.now().isoformat(),
            "progress": 0,
            "current_phase": "initializing"
        }
        update_session(session_data)
        
        # Progress callback: update session_data in-place so status: "processing"
        # is always preserved and the full dict is written to the session file.
        def _on_progress(phase, progress):
            session_data['current_phase'] = phase
            session_data['progress'] = progress
            update_session(session_data)

        # Use WorkflowOrchestrator for complete workflow
        orchestrator = WorkflowOrchestrator(config=WorkflowConfig(
            ai_provider="genai",
            question_types=["TN", "DS", "TLN", "TL"],
            max_concurrent_generations=config.get('max_workers', 5)
        ), progress_callback=_on_progress)
        
        # Execute complete workflow (Phase 2 will gracefully handle missing Google Drive)
        import logging as _logging
        _log = _logging.getLogger(__name__)
        _log.info(f"[{session_id}] Starting WorkflowOrchestrator")
        workflow_result = orchestrator.execute_complete_workflow(
            Path(matrix_file_path)
        )
        
        if not workflow_result.success:
            raise Exception(f"Failed: {', '.join(workflow_result.errors)}")
        
        # Extract data from workflow result
        matrix_metadata = workflow_result.matrix_metadata
        question_sets = workflow_result.question_sets
        
        # Convert metadata
        metadata = {
            "subject": matrix_metadata.subject,
            "grade": matrix_metadata.grade,
            "curriculum": matrix_metadata.curriculum,
            "filename": Path(matrix_file_path).name
        }
        
        # Count questions
        tn_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "TN")
        ds_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "DS")
        tln_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "TLN")
        tl_count = sum(len(qs.questions) for qs in question_sets if qs.question_type == "TL")
        
        # Progress will be updated to 100% when completed
        
        # ===== Finalize: Save Results =====
        print("💾 Saving generated questions...")
        # Progress already updated by WorkflowOrchestrator
        
        # Flatten questions from question_sets
        generated_tn = []
        generated_ds = []
        generated_tln = []
        generated_tl = []
        for qs in question_sets:
            for q in qs.questions:
                if q.type == "TN":
                    generated_tn.append(q)
                elif q.type == "DS":
                    generated_ds.append(q)
                elif q.type == "TLN":
                    generated_tln.append(q)
                elif q.type == "TL":
                    generated_tl.append(q)
        
        # Save final results to data/questions
        questions_file = _get_questions_dir() / f"questions_{session_id}.json"
        
        output_data = {
            "metadata": {
                "session_id": session_id,
                "subject": metadata["subject"],
                "grade": metadata["grade"],
                "curriculum": metadata["curriculum"],
                "matrix_file": Path(matrix_file_path).name,
                "total_questions": len(generated_tn) + len(generated_ds) + len(generated_tln) + len(generated_tl),
                "tn_count": len(generated_tn),
                "ds_count": len(generated_ds),
                "tln_count": len(generated_tln),
                "tl_count": len(generated_tl),
                "generated_at": datetime.now().isoformat(),
                "status": "completed"
            },
            "questions": {
                "TN": [
                    {
                        "question_code": q.id.split('_')[-1],  # Extract question code from ID
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tn
                ],
                "DS": [
                    {
                        "question_code": q.id.split('_')[-1],  # Extract question code from ID
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "source_text": q.source_text,
                        "statements": q.statements,
                        "explanation": {
                            "a": (q.explanation.get("a", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("a", "")),
                            "b": (q.explanation.get("b", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("b", "")),
                            "c": (q.explanation.get("c", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("c", "")),
                            "d": (q.explanation.get("d", "") if isinstance(q.explanation, dict) else json.loads(q.explanation or "{}").get("d", ""))
                        }
                    }
                    for q in generated_ds
                ],
                "TLN": [
                    {
                        "question_code": q.id.split('_')[-1],  # Extract question code from ID
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tln
                ],
                "TL": [
                    {
                        "question_code": q.id.split('_')[-1],
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tl
                ]
            }
        }
        
        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Update final session status
        session_data.update({
            'current_phase': 'completed',
            'progress': 100,
            'status': 'completed',
            'total_questions': len(generated_tn) + len(generated_ds) + len(generated_tln) + len(generated_tl),
            'tn_count': len(generated_tn),
            'ds_count': len(generated_ds),
            'tln_count': len(generated_tln),
            'tl_count': len(generated_tl),
            'total_generated': len(generated_tn) + len(generated_ds) + len(generated_tln) + len(generated_tl),
            'tn_generated': len(generated_tn),
            'ds_generated': len(generated_ds),
            'tln_generated': len(generated_tln),
            'tl_generated': len(generated_tl),
            'results_file': str(questions_file.name)
        })
        update_session(session_data)
        
        print(f"✅ Workflow completed! Generated {len(generated_tn)} TN + {len(generated_ds)} DS + {len(generated_tln)} TLN + {len(generated_tl)} TL questions")
        
    except Exception as e:
        # Handle errors with detailed logging
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        import logging as _logging
        _logging.getLogger(__name__).error(
            f"[{session_id}] Workflow failed: {error_msg}\n{error_trace}"
        )
        
        # Save error to session
        error_data = {
            "session_id": session_id,
            "status": "failed",
            "error": error_msg,
            "error_trace": error_trace,
            "current_phase": session_data.get('current_phase', 'unknown'),
            "progress": session_data.get('progress', 0),
            "generated_at": datetime.now().isoformat(),
            "matrix_file": Path(matrix_file_path).name
        }
        
        update_session(error_data)


@router.post("", response_model=GenerateResponse)
async def generate_questions(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    template_docx: Optional[UploadFile] = File(None),
    max_workers: int = 10,
    min_interval: float = 0.3,
    max_retries: int = 3,
    retry_delay: float = 2.0
):
    """
    Upload file Excel ma trận và sinh câu hỏi theo 4 phase workflow
    
    - **file**: File Excel ma trận (.xlsx)
    - **template_docx**: (Optional) File DOCX đề mẫu để AI tham khảo
    - **max_workers**: Số threads xử lý song song (default: 10)
    - **min_interval**: Delay tối thiểu giữa requests (default: 0.3s)
    - **max_retries**: Số lần retry khi lỗi (default: 3)
    - **retry_delay**: Delay giữa các lần retry (default: 2.0s)
    """
    
    # Validate file extension
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .xlsx")
    
    if file.filename.startswith("MATRIX_ENGLISH_"):
        try:
            return await generate_english_flow(file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình xử lý: {str(e)}")
    
    # Tạo session ID
    session_id = str(uuid.uuid4())
    
    # Lưu file upload
    upload_dir = _get_uploads_dir()
    
    file_path = upload_dir / f"{session_id}_{file.filename}"
    
    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu file: {str(e)}")
    
    # Lưu template DOCX nếu có
    template_path = None
    if template_docx:
        if not template_docx.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Template phải là file .docx")
        
        template_path = upload_dir / f"{session_id}_template_{template_docx.filename}"
        try:
            with open(template_path, 'wb') as f:
                template_content = await template_docx.read()
                f.write(template_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Không thể lưu template: {str(e)}")
    
    # Đường dẫn tuyệt đối đến thư mục config
    project_root = _get_app_dir()
    
    # Cấu hình
    config = {
        'project_id': os.getenv("GCP_PROJECT_ID"),
        'location': os.getenv("GCP_LOCATION", "global"),
        'credentials_path': os.getenv("GCP_CREDENTIALS_PATH"),
        'prompt_template_tn': str(project_root / "config" / "prompt" / "TN.txt"),
        'prompt_template_ds': str(project_root / "config" / "prompt" / "DS.txt"),
        'max_workers': max_workers,
        'min_interval': min_interval,
        'max_retries': max_retries,
        'retry_delay': retry_delay,
        'verbose': False
    }
    
    # Thêm background task
    background_tasks.add_task(
        generate_questions_task,
        session_id,
        str(file_path),
        config,
        str(template_path) if template_path else None
    )
    
    return GenerateResponse(
        session_id=session_id,
        status="processing",
        message="Đã bắt đầu sinh câu hỏi. Vui lòng kiểm tra tiến độ qua session_id."
    )


@router.get("/{session_id}/progress")
async def get_generation_progress(session_id: str):
    """
    Lấy tiến độ sinh câu hỏi
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check nếu có metadata (completed), lấy từ đó
    if "metadata" in data:
        metadata = data["metadata"]
        return {
            "session_id": session_id,
            "status": metadata.get("status", "completed"),
            "progress": 100,
            "total_questions": metadata.get("total_questions", 0),
            "current_phase": "completed",
            "error": None
        }
    
    # Nếu chưa có metadata (đang processing), lấy từ root
    return {
        "session_id": session_id,
        "status": data.get("status", "unknown"),
        "progress": data.get("progress", 0),
        "total_questions": data.get("total_questions", 0),
        "current_phase": data.get("current_phase", ""),
        "error": data.get("error")
    }


@router.get("/{session_id}/result")
async def get_generation_result(session_id: str):
    """
    Lấy kết quả sinh câu hỏi đã hoàn thành
    
    Returns:
        - metadata: Thông tin về session
        - questions: Object chứa TN và DS questions đã sinh
    """
    questions_file = _get_questions_dir() / f"questions_{session_id}.json"
    
    if not questions_file.exists():
        # Check session status
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            status = session_data.get('status', 'unknown')
            if status == 'failed':
                raise HTTPException(
                    status_code=500, 
                    detail=f"Generation failed: {session_data.get('error', 'Unknown error')}"
                )
            elif status == 'processing':
                raise HTTPException(
                    status_code=202, 
                    detail="Generation still in progress. Check /progress endpoint."
                )
        
        raise HTTPException(
            status_code=404, 
            detail="Result not found. Session may not exist or generation not started."
        )
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data
