"""
Route xuất file DOCX
"""
import json
import os
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.schemas import ExportResponse
from services.exporters.docx_generator import DocxGenerator
from config.settings import Config
from services.exporters.english_docx_generator import export_english_docx, generate_docx_from_ai_results,build_results_from_response, export_docx_from_data


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
    exports_dir = _get_app_dir() / "data" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir


# @routerEnglish.post("/export-english/{session_id}")
# async def export_english(session_id: str):

#     print(f">>>>> debug api export {session_id}")

#     result = await export_english_docx(session_id)

#     return FileResponse(
#         path=result["file_path"],
#         filename=result["file_name"],
#         media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#     )

@routerEnglish.post("/export-english")
async def export_english(payload: dict):
    # 3️⃣ Tạo folder export
    output_dir = Path("exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    file_name = "English_Exam.docx"
    output_path = output_dir / file_name

    # 4️⃣ Generate file
    # generate_docx_from_ai_results(results, str(output_path))
    export_docx_from_data(payload, str(output_path))

    # 5️⃣ Trả file về
    return FileResponse(
        path=str(output_path),
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.post("/{session_id}", response_model=ExportResponse)
async def export_docx(session_id: str):
    """
    Export câu hỏi ra file DOCX
    
    - **session_id**: ID của session cần export
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
            output_path=str(output_path)
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
