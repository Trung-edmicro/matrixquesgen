"""
Pydantic schemas for API requests/responses
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== REQUEST MODELS ====================

class GenerateQuestionsRequest(BaseModel):
    """Request để sinh câu hỏi từ ma trận"""
    max_workers: Optional[int] = Field(default=5, description="Số threads xử lý song song")
    min_interval: Optional[float] = Field(default=0.2, description="Delay tối thiểu giữa requests (giây)")
    max_retries: Optional[int] = Field(default=3, description="Số lần retry khi lỗi")
    retry_delay: Optional[float] = Field(default=2.0, description="Delay giữa các lần retry (giây)")


class UpdateQuestionRequest(BaseModel):
    """Request để cập nhật câu hỏi"""
    question_stem: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    source_text: Optional[str] = None
    statements: Optional[Dict[str, Any]] = None


class ExportRequest(BaseModel):
    """Request để export DOCX"""
    format: Optional[str] = Field(default="docx", description="Format xuất file (docx)")


# ==================== RESPONSE MODELS ====================

class QuestionTN(BaseModel):
    """Câu hỏi trắc nghiệm"""
    question_code: str
    question_type: str
    lesson_name: str
    level: str
    question_stem: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str


class QuestionDS(BaseModel):
    """Câu hỏi đúng/sai"""
    question_code: str
    question_type: str
    lesson_name: str
    source_text: str
    statements: Dict[str, Any]
    explanation: Dict[str, str]


class QuestionTLN(BaseModel):
    """Câu hỏi trắc nghiệm luận (trả lời ngắn)"""
    question_code: str
    question_type: str
    lesson_name: str
    level: str
    question_stem: str
    correct_answer: str
    explanation: str


class SessionMetadata(BaseModel):
    """Metadata của một session sinh câu hỏi"""
    session_id: str
    matrix_file: str
    total_questions: int
    tn_count: int
    ds_count: int
    tln_count: int = 0
    tl_count: int = 0
    generated_at: datetime
    status: str  # 'processing', 'completed', 'failed'


class SessionDetail(BaseModel):
    """Chi tiết đầy đủ của session"""
    metadata: SessionMetadata
    questions: Dict[str, List[Any]]  # {'TN': [...], 'DS': [...]}


class GenerateResponse(BaseModel):
    """Response sau khi bắt đầu sinh câu hỏi"""
    session_id: str
    status: str
    message: str
    results: Optional[Any]


class SessionListResponse(BaseModel):
    """Response danh sách sessions"""
    sessions: List[SessionMetadata]
    total: int


class ExportResponse(BaseModel):
    """Response sau khi export thành công"""
    file_path: str
    file_name: str
    download_url: str


class ErrorResponse(BaseModel):
    """Response khi có lỗi"""
    error: str
    detail: Optional[str] = None
    status_code: int
