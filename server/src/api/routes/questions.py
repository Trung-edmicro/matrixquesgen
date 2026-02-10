"""
Route quản lý danh sách câu hỏi và cập nhật
"""
import json
import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.schemas import (
    SessionListResponse, 
    SessionDetail, 
    UpdateQuestionRequest,
    SessionMetadata
)
from config.settings import Config


router = APIRouter(prefix="/api/questions", tags=["Questions"])


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


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    Lấy danh sách tất cả các session đã sinh
    
    - **limit**: Số lượng session tối đa (default: 50)
    - **offset**: Vị trí bắt đầu (default: 0)
    - **status**: Lọc theo status (processing, completed, failed)
    """
    sessions_dir = _get_sessions_dir()
    
    if not sessions_dir.exists():
        return SessionListResponse(sessions=[], total=0)
    
    # Lấy tất cả file session
    session_files = sorted(
        sessions_dir.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True  # Mới nhất trước
    )
    
    sessions = []
    
    for session_file in session_files:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', data)
            
            # Filter by status if specified
            if status and metadata.get('status') != status:
                continue
            
            sessions.append(SessionMetadata(
                session_id=metadata.get('session_id', session_file.stem),
                matrix_file=metadata.get('matrix_file', 'unknown'),
                total_questions=metadata.get('total_questions', metadata.get('total_generated', 0)),
                tn_count=metadata.get('tn_count', metadata.get('tn_generated', 0)),
                ds_count=metadata.get('ds_count', metadata.get('ds_generated', 0)),
                tln_count=metadata.get('tln_count', metadata.get('tln_generated', 0)),
                tl_count=metadata.get('tl_count', metadata.get('tl_generated', 0)),
                generated_at=metadata.get('generated_at'),
                status=metadata.get('status', 'unknown')
            ))
        except Exception as e:
            print(f"Error reading session {session_file}: {e}")
            continue
    
    # Apply pagination
    total = len(sessions)
    sessions = sessions[offset:offset + limit]
    
    return SessionListResponse(
        sessions=sessions,
        total=total
    )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(session_id: str):
    """
    Lấy chi tiết câu hỏi của một session
    """
    # First try to get from questions file (final results)
    questions_file = _get_questions_dir() / f"questions_{session_id}.json"
    if questions_file.exists():
        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        subject = metadata.get('subject', '')
        
        # Lọc source_text nếu môn không cần hiển thị
        if not Config.should_display_source(subject):
            questions = data.get('questions', {})
            ds_questions = questions.get('DS', [])
            for q in ds_questions:
                if 'source_text' in q:
                    q.pop('source_text', None)
                if 'source_citation' in q:
                    q.pop('source_citation', None)
                if 'source_origin' in q:
                    q.pop('source_origin', None)
                if 'source_type' in q:
                    q.pop('source_type', None)
        
        return SessionDetail(
            metadata=SessionMetadata(
                session_id=metadata.get('session_id', session_id),
                matrix_file=metadata.get('matrix_file'),
                total_questions=metadata.get('total_questions'),
                tn_count=metadata.get('tn_count'),
                ds_count=metadata.get('ds_count'),
                generated_at=metadata.get('generated_at'),
                status=metadata.get('status')
            ),
            questions=data.get('questions', {})
        )
    
    # Fallback to session file
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    
    if metadata.get('status') != 'completed':
        raise HTTPException(
            status_code=400, 
            detail=f"Session đang ở trạng thái: {metadata.get('status')}"
        )
    
    return SessionDetail(
        metadata=SessionMetadata(
            session_id=metadata.get('session_id', session_id),
            matrix_file=metadata.get('matrix_file'),
            total_questions=metadata.get('total_questions'),
            tn_count=metadata.get('tn_count'),
            ds_count=metadata.get('ds_count'),
            generated_at=metadata.get('generated_at'),
            status=metadata.get('status')
        ),
        questions=data.get('questions', {})
    )


@router.put("/{session_id}/questions/{question_type}/{question_code}")
async def update_question(
    session_id: str,
    question_type: str,  # 'TN' hoặc 'DS'
    question_code: str,  # 'C1', 'C2', ...
    update_data: UpdateQuestionRequest
):
    """
    Cập nhật nội dung câu hỏi
    
    - **session_id**: ID của session
    - **question_type**: Loại câu hỏi (TN hoặc DS)
    - **question_code**: Mã câu hỏi (C1, C2, ...)
    - **update_data**: Dữ liệu cần cập nhật
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    if question_type not in ['TN', 'DS']:
        raise HTTPException(status_code=400, detail="question_type phải là 'TN' hoặc 'DS'")
    
    # Đọc dữ liệu hiện tại
    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Tìm câu hỏi cần update
    questions = data.get('questions', {}).get(question_type, [])
    question_found = False
    
    for i, q in enumerate(questions):
        if q.get('question_code') == question_code:
            # Cập nhật các field
            update_dict = update_data.model_dump(exclude_none=True)
            questions[i].update(update_dict)
            question_found = True
            break
    
    if not question_found:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    
    # Lưu lại
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {
        "message": "Đã cập nhật câu hỏi thành công",
        "question_code": question_code,
        "question_type": question_type
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Xóa một session
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    
    session_file.unlink()
    
    return {
        "message": "Đã xóa session thành công",
        "session_id": session_id
    }
