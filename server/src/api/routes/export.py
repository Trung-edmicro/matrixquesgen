"""
Route xuất file DOCX
"""
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.schemas import ExportResponse
from services.docx_generator import DocxGenerator


router = APIRouter(prefix="/api/export", tags=["Export"])


SESSIONS_DIR = Path("data/sessions")
EXPORTS_DIR = Path("data/exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/{session_id}", response_model=ExportResponse)
async def export_docx(session_id: str):
    """
    Export câu hỏi ra file DOCX
    
    - **session_id**: ID của session cần export
    """
    session_file = SESSIONS_DIR / f"{session_id}.json"
    
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    # Đọc dữ liệu
    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    
    if metadata.get('status') != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Session chưa hoàn thành. Status: {metadata.get('status')}"
        )
    
    # Tạo tên file
    matrix_filename = Path(metadata.get('matrix_file', 'questions')).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{matrix_filename}_{timestamp}.docx"
    output_path = EXPORTS_DIR / output_filename
    
    # Generate DOCX
    try:
        generator = DocxGenerator(verbose=False)
        generator.generate_questions_document(
            json_data=data,
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
        EXPORTS_DIR.glob("*.docx"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    # Kiểm tra session tồn tại
    session_file = SESSIONS_DIR / f"{session_id}.json"
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
