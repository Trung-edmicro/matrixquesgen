import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.schemas import GenerateQuestionsRequest, GenerateResponse
from services.genai_client import GenAIClient
from services.matrix_parser import MatrixParser
from services.question_generator import QuestionGenerator
from services.concurrent_generator import (
    generate_tn_questions_parallel,
    generate_ds_questions_parallel
)


router = APIRouter(prefix="/api/generate", tags=["Generate"])


# Storage cho các session
SESSIONS_DIR = Path("data/sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def generate_questions_task(
    session_id: str,
    matrix_file_path: str,
    config: dict
):
    """
    Background task để sinh câu hỏi
    """
    session_file = SESSIONS_DIR / f"{session_id}.json"
    
    try:
        # Cập nhật status = processing
        session_data = {
            "session_id": session_id,
            "status": "processing",
            "matrix_file": Path(matrix_file_path).name,
            "generated_at": datetime.now().isoformat(),
            "progress": 0
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # Khởi tạo AI Client
        ai_client = GenAIClient(
            project_id=config.get('project_id'),
            location=config.get('location'),
            credentials_path=config.get('credentials_path')
        )
        
        ai_client.initialize_model(
            model_name="gemini-3-pro-preview",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        
        # Parse ma trận
        parser = MatrixParser()
        parser.load_excel(matrix_file_path)
        all_questions = parser.parse_matrix()
        
        tn_questions = [q for q in all_questions if q.question_type == "TN"]
        ds_questions = parser.group_true_false_questions()
        
        # Update progress
        session_data['total_questions'] = len(tn_questions) + len(ds_questions)
        session_data['tn_count'] = len(tn_questions)
        session_data['ds_count'] = len(ds_questions)
        session_data['progress'] = 10
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # Sinh câu hỏi TN
        generator = QuestionGenerator(
            ai_client=ai_client,
            prompt_template_path=config.get('prompt_template_tn')
        )
        
        generated_tn = generate_tn_questions_parallel(
            generator=generator,
            tn_specs=tn_questions,
            prompt_template_path=config.get('prompt_template_tn'),
            max_workers=config.get('max_workers', 5),
            min_interval=config.get('min_interval', 0.2),
            verbose=config.get('verbose', False),
            max_retries=config.get('max_retries', 3),
            retry_delay=config.get('retry_delay', 2.0)
        )
        
        session_data['progress'] = 50
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # Sinh câu hỏi DS
        generated_ds = generate_ds_questions_parallel(
            generator=generator,
            ds_specs=ds_questions,
            prompt_template_path=config.get('prompt_template_ds'),
            max_workers=config.get('max_workers', 5),
            min_interval=config.get('min_interval', 0.2),
            verbose=config.get('verbose', False),
            max_retries=config.get('max_retries', 3),
            retry_delay=config.get('retry_delay', 2.0)
        )
        
        # Lưu kết quả
        output_data = {
            "metadata": {
                "session_id": session_id,
                "total_questions": len(generated_tn) + len(generated_ds),
                "tn_count": len(generated_tn),
                "ds_count": len(generated_ds),
                "matrix_file": Path(matrix_file_path).name,
                "generated_at": datetime.now().isoformat(),
                "status": "completed"
            },
            "questions": {
                "TN": [
                    {
                        "question_code": q.question_code,
                        "question_type": q.question_type,
                        "lesson_name": q.lesson_name,
                        "level": q.level,
                        "question_stem": q.question_stem,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tn
                ],
                "DS": [
                    {
                        "question_code": q.question_code,
                        "question_type": q.question_type,
                        "lesson_name": q.lesson_name,
                        "source_text": q.source_text,
                        "statements": q.statements,
                        "explanation": q.explanation
                    }
                    for q in generated_ds
                ]
            }
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        # Lưu lỗi
        error_data = {
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)


@router.post("", response_model=GenerateResponse)
async def generate_questions(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    max_workers: int = 5,
    min_interval: float = 0.2,
    max_retries: int = 3,
    retry_delay: float = 2.0
):
    """
    Upload file Excel ma trận và sinh câu hỏi
    
    - **file**: File Excel ma trận (.xlsx)
    - **max_workers**: Số threads xử lý song song (default: 5)
    - **min_interval**: Delay tối thiểu giữa requests (default: 0.2s)
    - **max_retries**: Số lần retry khi lỗi (default: 3)
    - **retry_delay**: Delay giữa các lần retry (default: 2.0s)
    """
    
    # Validate file extension
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .xlsx")
    
    # Tạo session ID
    session_id = str(uuid.uuid4())
    
    # Lưu file upload
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{session_id}_{file.filename}"
    
    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu file: {str(e)}")
    
    # Đường dẫn tuyệt đối đến thư mục config
    api_dir = Path(__file__).parent.parent
    project_root = api_dir.parent
    
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
        config
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
    session_file = SESSIONS_DIR / f"{session_id}.json"
    
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
            "error": None
        }
    
    # Nếu chưa có metadata (đang processing), lấy từ root
    return {
        "session_id": session_id,
        "status": data.get("status", "unknown"),
        "progress": data.get("progress", 0),
        "total_questions": data.get("total_questions", 0),
        "error": data.get("error")
    }
