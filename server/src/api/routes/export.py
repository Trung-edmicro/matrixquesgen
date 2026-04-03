"""
Route xuất file DOCX
"""
import json
import os
import base64
import tempfile
import time
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import zipfile

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.schemas import ExportResponse
from services.exporters.docx_generator import DocxGenerator
from config.settings import Config
# from services.exporters.english_docx_generator import export_docx_from_data
from services.english_generator_service.english_generator_service import export_standard_docx_from_data, export_docx_from_data


router = APIRouter(prefix="/api/export", tags=["Export"])

routerEnglish = APIRouter(
    prefix="/api",
    tags=["English Export"]
)


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
    return _get_app_dir() / "data" / "sessions"


def _get_questions_dir() -> Path:
    """Get questions directory path with lazy loading"""
    return _get_app_dir() / "data" / "questions"


def _get_exports_dir() -> Path:
    """Get exports directory path with lazy loading"""
    exports_dir = _get_app_dir() / "exports"
    if exports_dir.parent.name == "server":
        exports_dir = exports_dir.parent.parent / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir



@routerEnglish.post("/export-english-solution")
async def export_english_solution(payload: dict):

    return FileResponse(
        # path=str(file_path),
        filename="English_Solution.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@routerEnglish.post("/export-standard-english-solution")
async def export_standard_english_solution(payload: dict):


    return FileResponse(
        # path=str(file_path),
        filename="English_Standard_Solution.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@routerEnglish.post("/export-english-exam")
async def export_english_exam(payload: dict):

    output_dir = _get_exports_dir()
    file_path = output_dir / "English_Exam.docx"

    export_docx_from_data(payload, str(file_path))

    return FileResponse(
        path=str(file_path),
        filename="English_Exam.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@routerEnglish.post("/export-english-standard")
async def export_english_standard(payload: dict):

    output_dir = _get_exports_dir()
    file_path = output_dir / "English_Standard_Exam.docx"

    export_standard_docx_from_data(payload, str(file_path))

    return FileResponse(
        path=str(file_path),
        filename="English_Standard_Exam.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@router.post("/{session_id}", response_model=ExportResponse)
async def export_docx(session_id: str, body: dict = None):
    """
    Export câu hỏi ra file DOCX
    
    - **session_id**: ID của session cần export
    - **body (optional)**: JSON body containing:
        - chart_images: Dict[str, str] mapping "question_code-chart_index" to Base64 images
    
    Request body example:
    {
        "chart_images": {
            "C1-0": "iVBORw0KGgo...",
            "C1-1": "iVBORw0KGgo..."
        }
    }
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    # Đọc dữ liệu
    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Kiểm tra status từ session data
    status = data.get('status')
    if status != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Session chưa hoàn thành. Status: {status}"
        )
    
    # Lấy metadata từ questions file
    results_file = data.get('results_file')
    if not results_file:
        raise HTTPException(status_code=404, detail="Results file không được chỉ định trong session")
    
    questions_file = _get_questions_dir() / results_file
    if not questions_file.exists():
        raise HTTPException(status_code=404, detail=f"Questions file không tồn tại: {results_file}")
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    metadata = questions_data.get('metadata', {})
    subject = metadata.get('subject', '')
    
    # Filter source metadata for subjects that don't need source display
    if not Config.should_display_source(subject):
        questions = questions_data.get('questions', {})
        ds_questions = questions.get('DS', [])
        for q in ds_questions:
            # Keep source_text.content but remove metadata.source
            if 'source_text' in q and isinstance(q['source_text'], dict):
                if 'metadata' in q['source_text']:
                    q['source_text']['metadata'].pop('source', None)
            # Remove source citation fields
            q.pop('source_citation', None)
            q.pop('source_origin', None)
            q.pop('source_type', None)
    
    # ✨ NEW: Extract chart images from request body
    chart_images = {}
    if body and isinstance(body, dict):
        chart_images = body.get('chart_images', {})
    
    # Tạo tên file
    matrix_filename = Path(metadata.get('matrix_file', 'questions')).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{matrix_filename}_{timestamp}.docx"
    output_path = _get_exports_dir() / output_filename
    
    # Generate DOCX
    try:
        generator = DocxGenerator(verbose=True)
        generator.generate_questions_document(
            json_data=questions_data,
            output_path=str(output_path),
            chart_images=chart_images  # ✨ NEW: Pass chart images
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo file DOCX: {str(e)}"
        )
    
    return ExportResponse(
        file_path=str(output_path),
        file_name=output_filename,
        download_url=f"/api/export/{session_id}/download"
    )


@router.get("/{session_id}/download")
async def download_docx(session_id: str):
    """
    Download file DOCX đã export
    """
    # Tìm file export mới nhất cho session này
    export_files = sorted(
        _get_exports_dir().glob("*.docx"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    # Kiểm tra session tồn tại
    session_file = _get_sessions_dir() / f"{session_id}.json"
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    # Lấy file export mới nhất (hoặc có thể lưu mapping session->export file)
    if not export_files:
        raise HTTPException(status_code=404, detail="Chưa có file export nào")
    
    latest_export = export_files[0]
    
    return FileResponse(
        path=str(latest_export),
        filename=latest_export.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# ✨ NEW ENDPOINT: Save chart image from client canvas
@router.post("/save-chart-image")
async def save_chart_image(request_data: dict):
    """
    Receive Base64 PNG from client canvas, save to temp file
    
    Request body:
    {
        "image_base64": "iVBORw0KGgo...",  // Base64 PNG data (without data:image/png;base64, prefix)
        "chart_title": "My Chart",
        "metadata": {"question_id": "Q1", ...},
        "timestamp": "2023-04-03T10:30:00Z"
    }
    
    Response:
    {
        "success": true,
        "image_path": "/tmp/matrixquesgen_charts/chart_Q1_1680505800.png",
        "size_kb": 45.2,
        "timestamp": "2023-04-03T10:30:00Z"
    }
    """
    try:
        image_base64 = request_data.get('image_base64', '')
        chart_title = request_data.get('chart_title', 'unknown')
        metadata = request_data.get('metadata', {})
        
        if not image_base64:
            raise ValueError("image_base64 is required")
        
        # Decode Base64 to bytes
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            raise ValueError(f"Invalid Base64 data: {e}")
        
        # Create temp directory for charts
        temp_dir = Path(tempfile.gettempdir()) / 'matrixquesgen_charts'
        temp_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate unique filename
        timestamp = int(time.time())
        question_id = metadata.get('question_id', 'unknown')
        image_filename = f'chart_{question_id}_{timestamp}.png'
        image_path = temp_dir / image_filename
        
        # Save image
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        size_kb = len(image_bytes) / 1024
        
        return {
            'success': True,
            'image_path': str(image_path),
            'image_filename': image_filename,
            'size_kb': round(size_kb, 2),
            'chart_title': chart_title,
            'timestamp': request_data.get('timestamp', datetime.now().isoformat())
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save chart image: {str(e)}")
